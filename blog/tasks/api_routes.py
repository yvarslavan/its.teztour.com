# blog/tasks/api_routes.py
"""
API endpoints для новых компонентов TasksApp
Отдельный файл для чистой архитектуры
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import time
import traceback
from datetime import datetime

# Импорты из существующих модулей
from blog.utils.cache_manager import weekend_performance_optimizer, tasks_cache_optimizer
from blog.tasks.utils import (
    get_redmine_connector,
    get_user_assigned_tasks_paginated_optimized,
    task_to_dict,
    create_redmine_connector
)
from redmine import (
    get_status_name_from_id,
    get_project_name_from_id,
    get_user_full_name_from_id,
    get_priority_name_from_id,
    get_property_name,
    get_connection
)
# ИСПРАВЛЕНИЕ: Правильный импорт конфигурации
from blog.settings import Config

# Создаем Blueprint для API
api_bp = Blueprint('tasks_api', __name__, url_prefix='/tasks/api')

# ===== НОВЫЕ API ENDPOINTS ДЛЯ КОМПОНЕНТОВ =====

@api_bp.route("/statistics-corrected", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_statistics_corrected_api():
    """
    ИСПРАВЛЕННЫЙ API для получения статистики задач с правильными статусами
    Использует issue_statuses с локализацией из u_statuses
    """
    current_app.logger.info(f"[API] /statistics-corrected - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # ИСПРАВЛЕНИЕ: Используем правильную конфигурацию
        config = Config()
        mysql_conn = get_connection(
            config.DB_REDMINE_HOST,
            config.DB_REDMINE_USER_NAME,
            config.DB_REDMINE_PASSWORD,
            config.DB_REDMINE_NAME
        )

        if not mysql_conn:
            current_app.logger.error("[API] /statistics-corrected - не удалось подключиться к MySQL Redmine")
            return jsonify({
                "error": "Ошибка подключения к базе данных Redmine",
                "success": False
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_id = current_user.id_redmine_user
        if not redmine_user_id:
            current_app.logger.error(f"[API] /statistics-corrected - не найден ID пользователя Redmine для {current_user.username}")
            return jsonify({
                "error": "ID пользователя Redmine не найден",
                "success": False
            }), 400

        cursor = mysql_conn.cursor()

        try:
            # 1. ОБЩЕЕ количество задач
            sql_total = """
                SELECT COUNT(*) as total_count
                FROM issues i
                WHERE i.assigned_to_id = %s
            """
            cursor.execute(sql_total, (redmine_user_id,))
            result = cursor.fetchone()
            total_tasks = result['total_count'] if result else 0
            current_app.logger.info(f"[API] /statistics-corrected - общее количество задач: {total_tasks}")

            # 2. ЗАКРЫТЫЕ задачи (is_closed=1 в issue_statuses)
            sql_closed = """
                SELECT COUNT(*) as closed_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s AND s.is_closed = 1
            """
            cursor.execute(sql_closed, (redmine_user_id,))
            result = cursor.fetchone()
            closed_tasks = result['closed_count'] if result else 0
            current_app.logger.info(f"[API] /statistics-corrected - закрытые задачи: {closed_tasks}")

            # 3. ДЕТАЛЬНАЯ статистика по статусам с локализацией
            sql_detailed = """
                SELECT
                    s.id as status_id,
                    s.name as original_name,
                    COALESCE(us.name, s.name) as localized_name,
                    s.is_closed,
                    COUNT(i.id) as task_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                LEFT JOIN u_statuses us ON s.id = us.id
                WHERE i.assigned_to_id = %s
                GROUP BY s.id, s.name, us.name, s.is_closed
                ORDER BY s.is_closed ASC, task_count DESC
            """
            cursor.execute(sql_detailed, (redmine_user_id,))
            status_details = cursor.fetchall()

            # Инициализируем счетчики
            new_tasks = 0
            in_progress_tasks = 0
            status_breakdown = {}

            current_app.logger.info(f"[API] /statistics-corrected - детализация по статусам:")

            for status_row in status_details:
                status_id = status_row['status_id']
                original_name = status_row['original_name']
                localized_name = status_row['localized_name']
                is_closed = bool(status_row['is_closed'])
                task_count = status_row['task_count']

                # Добавляем в разбивку
                status_breakdown[localized_name] = task_count

                current_app.logger.info(f"  - {localized_name} (ID: {status_id}, закрыт: {is_closed}): {task_count} задач")

                # Классифицируем только открытые статусы
                if not is_closed:
                    status_name_lower = localized_name.lower().strip()

                    # NEW TASKS (Новые и Открытые)
                    if any(keyword in status_name_lower for keyword in ['новая', 'новый', 'новое', 'new', 'открыт']):
                        new_tasks += task_count
                        current_app.logger.info(f"    -> отнесено к NEW: +{task_count}")
                    else:
                        # Все остальные открытые статусы - в работе
                        in_progress_tasks += task_count
                        current_app.logger.info(f"    -> отнесено к IN_PROGRESS: +{task_count}")

            # Формируем ответ
            response_data = {
                "success": True,
                "total_tasks": total_tasks,
                "new_tasks": new_tasks,
                "in_progress_tasks": in_progress_tasks,
                "closed_tasks": closed_tasks,
                "status_breakdown": status_breakdown,
                "source": "mysql_redmine_corrected"
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /statistics-corrected выполнен за {execution_time:.2f}с")
            current_app.logger.info(f"[API] /statistics-corrected - итоговая статистика: {response_data}")

            return jsonify(response_data)

        except Exception as db_error:
            current_app.logger.error(f"[API] Ошибка БД в /statistics-corrected: {str(db_error)}. Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": f"Ошибка базы данных: {str(db_error)}",
                "success": False
            }), 500
        finally:
            cursor.close()
            mysql_conn.close()

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /statistics-corrected: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/tasks", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_tasks_api():
    """
    API для получения списка задач (для TasksTable компонента)
    Совместимый с DataTables параметрами
    ИСПРАВЛЕНО: Улучшено логирование и обработка ошибок
    """
    current_app.logger.info(f"[API] /tasks - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            current_app.logger.warning(f"[API] /tasks - доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "data": [],
                "recordsTotal": 0,
                "recordsFiltered": 0
            }), 403

        # Получаем параметры запроса
        draw = request.args.get('draw', 1, type=int)
        start = request.args.get('start', 0, type=int)
        length = request.args.get('length', 25, type=int)
        search_value = request.args.get('search[value]', '', type=str).strip()

        # Параметры сортировки
        order_column_index = request.args.get('order[0][column]', 0, type=int)
        order_direction = request.args.get('order[0][dir]', 'desc', type=str)

        # Параметры фильтрации
        status_filter = request.args.get('status_filter', '', type=str)
        project_filter = request.args.get('project_filter', '', type=str)
        priority_filter = request.args.get('priority_filter', '', type=str)
        search_value = request.args.get('search', search_value, type=str)  # Поддержка обоих параметров

        # Вычисляем номер страницы
        page = (start // length) + 1

        current_app.logger.info(f"[API] /tasks - параметры: draw={draw}, page={page}, per_page={length}, search='{search_value}', status='{status_filter}', project='{project_filter}', priority='{priority_filter}'")

        # ИСПРАВЛЕНИЕ: Детальная проверка пользователя Redmine
        try:
            # Создаем коннектор Redmine
            redmine_connector = create_redmine_connector(
                is_redmine_user=current_user.is_redmine_user,
                user_login=current_user.username,
                password=current_user.password
            )

            if not redmine_connector:
                current_app.logger.error("[API] /tasks - не удалось создать коннектор Redmine")
                return jsonify({
                    "draw": draw,
                    "error": "Ошибка подключения к Redmine",
                    "data": [],
                    "recordsTotal": 0,
                    "recordsFiltered": 0
                }), 500

            # Получаем ID пользователя Redmine (используем из локальной БД для производительности)
            redmine_user_id = current_user.id_redmine_user
            current_app.logger.debug(f"[API] /tasks - ID пользователя Redmine из БД: {redmine_user_id}")

            if not redmine_user_id:
                # Fallback: получаем из Redmine API
                current_app.logger.info("[API] /tasks - получаем ID пользователя из Redmine API")
                redmine_user_obj = redmine_connector.redmine.user.get('current')
                redmine_user_id = redmine_user_obj.id
                current_app.logger.info(f"[API] /tasks - ID пользователя из Redmine API: {redmine_user_id}")

            # ИСПРАВЛЕНИЕ: Получаем задачи с расширенной обработкой ошибок
            current_app.logger.info(f"[API] /tasks - запрашиваем задачи для пользователя {redmine_user_id}")

            issues_list, total_count = get_user_assigned_tasks_paginated_optimized(
                redmine_connector=redmine_connector,
                redmine_user_id=redmine_user_id,
                page=page,
                per_page=length,
                search_term=search_value,
                status_ids=[status_filter] if status_filter else [],
                project_ids=[project_filter] if project_filter else [],
                priority_ids=[priority_filter] if priority_filter else []
            )

            current_app.logger.info(f"[API] /tasks - получено задач: {len(issues_list)}, всего: {total_count}")

            # Преобразуем задачи в формат для DataTables
            formatted_tasks = []
            for i, task in enumerate(issues_list):
                try:
                    formatted_task = task_to_dict(task)
                    formatted_tasks.append(formatted_task)
                    current_app.logger.debug(f"[API] /tasks - обработана задача {i+1}: #{formatted_task.get('id', 'N/A')}")
                except Exception as task_error:
                    current_app.logger.error(f"[API] /tasks - ошибка обработки задачи {i+1}: {str(task_error)}")
                    # Добавляем заглушку для поврежденной задачи
                    formatted_tasks.append({
                        'id': f'error_{i}',
                        'subject': 'Ошибка загрузки задачи',
                        'status_name': 'Неизвестно',
                        'project_name': 'Неизвестно',
                        'priority_name': 'Неизвестно',
                        'created_on': None,
                        'updated_on': None
                    })

            response_data = {
                "draw": draw,
                "recordsTotal": total_count,
                "recordsFiltered": total_count,
                "data": formatted_tasks,
                "success": True,
                "source": "redmine_api"
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /tasks выполнен за {execution_time:.2f}с, возвращено {len(formatted_tasks)} задач")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка Redmine в /tasks: {str(redmine_error)}. Traceback: {traceback.format_exc()}")

            # ИСПРАВЛЕНИЕ: Возвращаем пустой результат вместо ошибки для стабильной работы таблицы
            return jsonify({
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "success": False,
                "error": f"Ошибка получения данных из Redmine: {str(redmine_error)}",
                "source": "error_fallback"
            }), 200  # Возвращаем 200 вместо 500 для корректной работы таблицы

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /tasks: {str(e)}. Traceback: {traceback.format_exc()}")

        # ИСПРАВЛЕНИЕ: Даже при критической ошибке возвращаем корректную структуру
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "source": "critical_error_fallback"
        }), 200  # Возвращаем 200 для стабильной работы фронтенда


@api_bp.route("/task/<int:task_id>", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_task_detail_api(task_id):
    """
    API для получения деталей задачи
    """
    current_app.logger.info(f"[API] /task/{task_id} - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем детали задачи
            task = redmine_connector.redmine.issue.get(
                task_id,
                include=['status', 'priority', 'project', 'tracker', 'author',
                        'assigned_to', 'journals', 'done_ratio', 'attachments',
                        'relations', 'watchers', 'changesets']
            )

            # Преобразуем в словарь
            task_dict = task_to_dict(task)

            response_data = {
                "success": True,
                "task": task_dict
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /task/{task_id} выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Задача {task_id} не найдена: {str(redmine_error)}")
            return jsonify({
                "error": f"Задача #{task_id} не найдена",
                "success": False
            }), 404

    except Exception as e:
        current_app.logger.error(f"[API] Ошибка в /task/{task_id}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/projects", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_projects_api():
    """
    API для получения списка проектов (для FiltersPanel компонента)
    """
    current_app.logger.info(f"[API] /projects - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "projects": []
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "projects": []
            }), 500

        try:
            # Получаем проекты с пагинацией для получения всех проектов
            projects_list = []
            offset = 0
            limit = 100

            while True:
                projects_batch = redmine_connector.redmine.project.all(offset=offset, limit=limit)
                if not projects_batch:
                    break

                for project in projects_batch:
                    projects_list.append({
                        "id": project.id,
                        "name": project.name,
                        "original_name": project.name,
                        "identifier": getattr(project, 'identifier', ''),
                        "description": getattr(project, 'description', '')
                    })

                # Если получили меньше чем лимит, значит это последняя страница
                if len(projects_batch) < limit:
                    break

                offset += limit

            response_data = {
                "success": True,
                "projects": projects_list
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /projects выполнен за {execution_time:.2f}с, возвращено {len(projects_list)} проектов")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка Redmine в /projects: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения проектов из Redmine: {str(redmine_error)}",
                "success": False,
                "projects": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Ошибка в /projects: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "projects": []
        }), 500


@api_bp.route("/users", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_users_api():
    """
    API для получения списка пользователей (для FiltersPanel компонента)
    """
    current_app.logger.info(f"[API] /users - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "users": []
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "users": []
            }), 500

        try:
            # Получаем пользователей
            users = redmine_connector.redmine.user.all()

            # Преобразуем в формат для фильтров
            users_list = []
            for user in users:
                users_list.append({
                    "id": user.id,
                    "name": f"{user.firstname} {user.lastname}".strip(),
                    "login": getattr(user, 'login', ''),
                    "email": getattr(user, 'mail', '')
                })

            response_data = {
                "success": True,
                "users": users_list
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /users выполнен за {execution_time:.2f}с, возвращено {len(users_list)} пользователей")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка Redmine в /users: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения пользователей из Redmine: {str(redmine_error)}",
                "success": False,
                "users": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Ошибка в /users: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "users": []
        }), 500


@api_bp.route("/export", methods=["GET"])
@login_required
@weekend_performance_optimizer
def export_tasks_api():
    """
    API для экспорта задач в различных форматах
    """
    current_app.logger.info(f"[API] /export - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        export_format = request.args.get('format', 'csv', type=str).lower()

        if export_format not in ['csv', 'xlsx', 'json']:
            return jsonify({
                "error": "Неподдерживаемый формат экспорта",
                "success": False
            }), 400

        # Получаем параметры фильтрации
        status_filter = request.args.get('status_filter', '', type=str)
        project_filter = request.args.get('project_filter', '', type=str)
        priority_filter = request.args.get('priority_filter', '', type=str)
        search_query = request.args.get('search', '', type=str)

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_id = current_user.id_redmine_user
        if not redmine_user_id:
            # Fallback: получаем из Redmine API
            redmine_user_obj = redmine_connector.redmine.user.get('current')
            redmine_user_id = redmine_user_obj.id

        # Получаем все задачи для экспорта
        issues_list, total_count = get_user_assigned_tasks_paginated_optimized(
            redmine_connector=redmine_connector,
            redmine_user_id=redmine_user_id,
            page=1,
            per_page=1000,  # Большой лимит для экспорта
            search_term=search_query,
            status_ids=[status_filter] if status_filter else [],
            project_ids=[project_filter] if project_filter else [],
            priority_ids=[priority_filter] if priority_filter else []
        )

        # Преобразуем задачи в формат для экспорта
        export_data = []
        for task in issues_list:
            task_dict = task_to_dict(task)
            export_data.append(task_dict)

        if export_format == 'json':
            from flask import make_response
            response = make_response(jsonify({
                "success": True,
                "data": export_data,
                "total": len(export_data),
                "exported_at": datetime.now().isoformat()
            }))
            response.headers['Content-Disposition'] = f'attachment; filename=tasks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            return response

        elif export_format in ['csv', 'xlsx']:
            # Для CSV и Excel нужно импортировать pandas
            try:
                import pandas as pd
                from io import BytesIO

                # Создаем DataFrame
                df = pd.DataFrame(export_data)

                if export_format == 'csv':
                    from flask import make_response
                    output = df.to_csv(index=False, encoding='utf-8-sig')
                    response = make_response(output)
                    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
                    response.headers['Content-Disposition'] = f'attachment; filename=tasks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                    return response

                elif export_format == 'xlsx':
                    from flask import make_response
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Tasks')
                    output.seek(0)

                    response = make_response(output.getvalue())
                    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    response.headers['Content-Disposition'] = f'attachment; filename=tasks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                    return response

            except ImportError:
                return jsonify({
                    "error": "Модули для экспорта не установлены (pandas, openpyxl)",
                    "success": False
                }), 500

        execution_time = time.time() - start_time
        current_app.logger.info(f"[API] /export выполнен за {execution_time:.2f}с")

    except Exception as e:
        current_app.logger.error(f"[API] Ошибка в /export: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/priorities", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_priorities_api():
    """
    API для получения списка приоритетов из таблицы u_Priority (для FiltersPanel компонента)
    """
    current_app.logger.info(f"[API] /priorities - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "priorities": []
            }), 403

        try:
            # Получаем приоритеты из таблицы u_Priority с соединением с enumerations
            from blog.db_config import db
            from sqlalchemy import text

            sql = """
            SELECT e.id, COALESCE(up.name, e.name) as name
            FROM enumerations e
            LEFT JOIN u_Priority up ON e.id = up.id
            WHERE e.type = 'IssuePriority'
            ORDER BY e.position ASC
            """

            result = db.session.execute(text(sql))
            priorities_raw = result.fetchall()

            # Преобразуем в формат для фильтров
            priorities_list = []
            for priority in priorities_raw:
                priorities_list.append({
                    "id": priority[0],
                    "name": priority[1] or f"Приоритет {priority[0]}"
                })

            # Если нет данных, используем стандартные значения
            if not priorities_list:
                priorities_list = [
                    {"id": 1, "name": "Низкий"},
                    {"id": 2, "name": "Нормальный"},
                    {"id": 3, "name": "Высокий"},
                    {"id": 4, "name": "Срочный"},
                    {"id": 5, "name": "Неотложный"}
                ]

            response_data = {
                "success": True,
                "priorities": priorities_list
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /priorities выполнен за {execution_time:.2f}с, возвращено {len(priorities_list)} приоритетов")

            return jsonify(response_data)

        except Exception as db_error:
            current_app.logger.error(f"[API] Ошибка БД в /priorities: {str(db_error)}")
            # Fallback к стандартным значениям
            priorities_list = [
                {"id": 1, "name": "Низкий"},
                {"id": 2, "name": "Нормальный"},
                {"id": 3, "name": "Высокий"},
                {"id": 4, "name": "Срочный"},
                {"id": 5, "name": "Неотложный"}
            ]
            return jsonify({
                "success": True,
                "priorities": priorities_list
            })

    except Exception as e:
        current_app.logger.error(f"[API] Ошибка в /priorities: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "priorities": []
        }), 500


@api_bp.route("/statuses", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_statuses_api():
    """
    API для получения списка статусов из таблицы u_statuses (для FiltersPanel компонента)
    ИСПРАВЛЕНО: Улучшено логирование и обработка ошибок
    """
    current_app.logger.info(f"[API] /statuses - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            current_app.logger.warning(f"[API] /statuses - доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "statuses": []
            }), 403

        try:
            # ИСПРАВЛЕНИЕ: Используем правильный запрос к issue_statuses с локализацией из u_statuses
            current_app.logger.info("[API] /statuses - выполняем запрос к issue_statuses с локализацией из u_statuses")

            # ИСПРАВЛЕНИЕ: Используем правильную конфигурацию
            config = Config()
            mysql_conn = get_connection(
                config.DB_REDMINE_HOST,
                config.DB_REDMINE_USER_NAME,
                config.DB_REDMINE_PASSWORD,
                config.DB_REDMINE_NAME
            )

            if not mysql_conn:
                current_app.logger.error("[API] /statuses - не удалось подключиться к MySQL Redmine")
                # ИСПРАВЛЕНИЕ: Если нет данных, используем актуальные статусы из системы
                statuses_list = [
                    # Открытые статусы (is_closed: False)
                    {"id": 1, "name": "Новая", "is_closed": False},
                    {"id": 17, "name": "Открыта", "is_closed": False},
                    {"id": 19, "name": "В очереди", "is_closed": False},
                    {"id": 15, "name": "На согласовании", "is_closed": False},
                    {"id": 2, "name": "В работе", "is_closed": False},
                    {"id": 9, "name": "Запрошено уточнение", "is_closed": False},
                    {"id": 10, "name": "Приостановлена", "is_closed": False},
                    {"id": 16, "name": "Заморожена", "is_closed": False},
                    {"id": 18, "name": "На тестировании", "is_closed": False},
                    {"id": 13, "name": "Протестирована", "is_closed": False},
                    {"id": 7, "name": "Выполнена", "is_closed": False},
                    # Закрытые статусы (is_closed: True)
                    {"id": 14, "name": "Перенаправлена", "is_closed": True},
                    {"id": 6, "name": "Отклонена", "is_closed": True},
                    {"id": 5, "name": "Закрыта", "is_closed": True}
                ]
                return jsonify({
                    "success": True,
                    "statuses": statuses_list,
                    "source": "fallback_no_connection",
                    "count": len(statuses_list)
                })

            cursor = mysql_conn.cursor()

            try:
                # Запрос к issue_statuses с локализацией из u_statuses
                sql = """
                SELECT
                    s.id,
                    COALESCE(us.name, s.name) as name,
                    s.is_closed
                FROM issue_statuses s
                LEFT JOIN u_statuses us ON s.id = us.id
                WHERE s.id IS NOT NULL
                ORDER BY s.is_closed ASC, s.position ASC, s.id ASC
                """

                current_app.logger.debug(f"[API] /statuses - SQL запрос: {sql}")
                cursor.execute(sql)
                statuses_raw = cursor.fetchall()

                current_app.logger.info(f"[API] /statuses - получено {len(statuses_raw)} записей из MySQL Redmine")

                # Преобразуем в формат для фильтров
                statuses_list = []
                for status in statuses_raw:
                    status_dict = {
                        "id": status['id'],
                        "name": status['name'],
                        "is_closed": bool(status['is_closed'])
                    }
                    statuses_list.append(status_dict)
                    current_app.logger.debug(f"[API] /statuses - добавлен статус: {status_dict}")

                # ИСПРАВЛЕНИЕ: Если нет данных, используем актуальные статусы из системы
                if not statuses_list:
                    current_app.logger.warning("[API] /statuses - нет данных в issue_statuses, используем актуальные статусы")
                    statuses_list = [
                        # Открытые статусы (is_closed: False)
                        {"id": 1, "name": "Новая", "is_closed": False},
                        {"id": 17, "name": "Открыта", "is_closed": False},
                        {"id": 19, "name": "В очереди", "is_closed": False},
                        {"id": 15, "name": "На согласовании", "is_closed": False},
                        {"id": 2, "name": "В работе", "is_closed": False},
                        {"id": 9, "name": "Запрошено уточнение", "is_closed": False},
                        {"id": 10, "name": "Приостановлена", "is_closed": False},
                        {"id": 16, "name": "Заморожена", "is_closed": False},
                        {"id": 18, "name": "На тестировании", "is_closed": False},
                        {"id": 13, "name": "Протестирована", "is_closed": False},
                        {"id": 7, "name": "Выполнена", "is_closed": False},
                        # Закрытые статусы (is_closed: True)
                        {"id": 14, "name": "Перенаправлена", "is_closed": True},
                        {"id": 6, "name": "Отклонена", "is_closed": True},
                        {"id": 5, "name": "Закрыта", "is_closed": True}
                    ]
                    current_app.logger.info(f"[API] /statuses - использованы актуальные статусы: {len(statuses_list)} элементов")

                response_data = {
                    "success": True,
                    "statuses": statuses_list,
                    "source": "mysql_redmine" if len(statuses_raw) > 0 else "fallback",
                    "count": len(statuses_list)
                }

                execution_time = time.time() - start_time
                current_app.logger.info(f"[API] /statuses выполнен за {execution_time:.2f}с, возвращено {len(statuses_list)} статусов")
                current_app.logger.debug(f"[API] /statuses - итоговый ответ: {response_data}")

                return jsonify(response_data)

            finally:
                cursor.close()
                mysql_conn.close()

        except Exception as db_error:
            current_app.logger.error(f"[API] Ошибка БД в /statuses: {str(db_error)}. Traceback: {traceback.format_exc()}")

            # ИСПРАВЛЕНИЕ: Улучшенный fallback с актуальными статусами
            current_app.logger.warning("[API] /statuses - используем fallback к актуальным статусам из-за ошибки БД")
            statuses_list = [
                # Открытые статусы
                {"id": 1, "name": "Новая"},
                {"id": 17, "name": "Открыта"},
                {"id": 19, "name": "В очереди"},
                {"id": 15, "name": "На согласовании"},
                {"id": 2, "name": "В работе"},
                {"id": 9, "name": "Запрошено уточнение"},
                {"id": 10, "name": "Приостановлена"},
                {"id": 16, "name": "Заморожена"},
                {"id": 18, "name": "На тестировании"},
                {"id": 13, "name": "Протестирована"},
                {"id": 7, "name": "Выполнена"},
                # Закрытые статусы
                {"id": 14, "name": "Перенаправлена"},
                {"id": 6, "name": "Отклонена"},
                {"id": 5, "name": "Закрыта"}
            ]

            response_data = {
                "success": True,
                "statuses": statuses_list,
                "source": "fallback_error",
                "count": len(statuses_list),
                "db_error": str(db_error)
            }

            current_app.logger.info(f"[API] /statuses - fallback ответ: {len(statuses_list)} статусов")
            return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /statuses: {str(e)}. Traceback: {traceback.format_exc()}")

        # ИСПРАВЛЕНИЕ: Даже при критической ошибке возвращаем актуальные статусы
        fallback_statuses = [
            # Открытые статусы
            {"id": 1, "name": "Новая"},
            {"id": 17, "name": "Открыта"},
            {"id": 19, "name": "В очереди"},
            {"id": 15, "name": "На согласовании"},
            {"id": 2, "name": "В работе"},
            {"id": 9, "name": "Запрошено уточнение"},
            {"id": 10, "name": "Приостановлена"},
            {"id": 16, "name": "Заморожена"},
            {"id": 18, "name": "На тестировании"},
            {"id": 13, "name": "Протестирована"},
            {"id": 7, "name": "Выполнена"},
            # Закрытые статусы
            {"id": 14, "name": "Перенаправлена"},
            {"id": 6, "name": "Отклонена"},
            {"id": 5, "name": "Закрыта"}
        ]

        return jsonify({
            "success": True,  # Возвращаем success=True чтобы фронтенд мог обработать данные
            "statuses": fallback_statuses,
            "source": "critical_fallback",
            "count": len(fallback_statuses),
            "error_message": str(e)
        }), 200  # Возвращаем 200 вместо 500 для обеспечения работы фильтров


@api_bp.route("/statistics-extended", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_statistics_extended_api():
    """
    НОВЫЙ API для получения расширенной статистики задач с временными периодами
    Заменяет захардкоженные значения на реальные данные из БД
    """
    current_app.logger.info(f"🔥 [API] /statistics-extended - НАЧАЛО ЗАПРОСА от {current_user.username}")
    current_app.logger.info(f"🔥 [API] /statistics-extended - User ID: {current_user.id}")
    current_app.logger.info(f"🔥 [API] /statistics-extended - Redmine User: {current_user.is_redmine_user}")
    current_app.logger.info(f"🔥 [API] /statistics-extended - Redmine ID: {current_user.id_redmine_user}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # ИСПРАВЛЕНИЕ: Используем правильную конфигурацию
        config = Config()
        mysql_conn = get_connection(
            config.DB_REDMINE_HOST,
            config.DB_REDMINE_USER_NAME,
            config.DB_REDMINE_PASSWORD,
            config.DB_REDMINE_NAME
        )

        if not mysql_conn:
            current_app.logger.error("[API] /statistics-extended - не удалось подключиться к MySQL Redmine")
            return jsonify({
                "error": "Ошибка подключения к базе данных Redmine",
                "success": False
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_id = current_user.id_redmine_user
        if not redmine_user_id:
            current_app.logger.warning(f"[API] /statistics-extended - ID пользователя Redmine не найден в БД для {current_user.username}, пытаемся получить из MySQL")

            # Пытаемся найти пользователя в MySQL Redmine
            try:
                cursor = mysql_conn.cursor()

                # ИСПРАВЛЕНИЕ: Обрабатываем случай когда email может быть None
                user_email = current_user.email if current_user.email else ''

                current_app.logger.info(f"🔥 [API] /statistics-extended - Поиск пользователя: login='{current_user.username}', email='{user_email}'")

                sql_find_user = """
                    SELECT id FROM users
                    WHERE login = %s OR mail = %s
                    LIMIT 1
                """
                cursor.execute(sql_find_user, (current_user.username, user_email))
                user_result = cursor.fetchone()

                if user_result:
                    redmine_user_id = user_result['id']
                    current_app.logger.info(f"🔥 [API] /statistics-extended - найден ID пользователя в MySQL: {redmine_user_id}")
                else:
                    current_app.logger.error(f"🔥 [API] /statistics-extended - пользователь {current_user.username} не найден в MySQL Redmine")
                    return jsonify({
                        "error": "Пользователь не найден в системе Redmine",
                        "success": False
                    }), 400
            except Exception as find_error:
                current_app.logger.error(f"🔥 [API] /statistics-extended - ошибка поиска пользователя: {find_error}")
                return jsonify({
                    "error": "Ошибка поиска пользователя в системе Redmine",
                    "success": False
                }), 500
            finally:
                cursor.close()

        # Создаем новый cursor для основных запросов
        cursor = mysql_conn.cursor()

        try:
            # 1. ОБЩАЯ статистика
            sql_total = """
                SELECT COUNT(*) as total_count
                FROM issues i
                WHERE i.assigned_to_id = %s
            """
            cursor.execute(sql_total, (redmine_user_id,))
            result = cursor.fetchone()
            total_tasks = result['total_count'] if result else 0

            # 2. ЗАКРЫТЫЕ задачи
            sql_closed = """
                SELECT COUNT(*) as closed_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s AND s.is_closed = 1
            """
            cursor.execute(sql_closed, (redmine_user_id,))
            result = cursor.fetchone()
            closed_tasks = result['closed_count'] if result else 0

            # 3. НОВЫЕ задачи (созданные сегодня)
            sql_new_today = """
                SELECT COUNT(*) as new_today_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND DATE(i.created_on) = CURDATE()
            """
            cursor.execute(sql_new_today, (redmine_user_id,))
            result = cursor.fetchone()
            new_today = result['new_today_count'] if result else 0

            # 4. НОВЫЕ задачи (созданные за неделю)
            sql_new_week = """
                SELECT COUNT(*) as new_week_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND i.created_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            """
            cursor.execute(sql_new_week, (redmine_user_id,))
            result = cursor.fetchone()
            new_week = result['new_week_count'] if result else 0

            # 5. ЗАВЕРШЕННЫЕ задачи (закрытые сегодня) - УПРОЩЕННАЯ ЛОГИКА
            # Используем только простой подход через updated_on
            sql_closed_today = """
                SELECT COUNT(*) as closed_today_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 1
                AND DATE(i.updated_on) = CURDATE()
            """
            cursor.execute(sql_closed_today, (redmine_user_id,))
            result = cursor.fetchone()
            closed_today = result['closed_today_count'] if result else 0

            current_app.logger.info(f"🔥 [API] /statistics-extended - закрытые сегодня: {closed_today}")

            # ДОПОЛНИТЕЛЬНОЕ ОТЛАДОЧНОЕ ЛОГИРОВАНИЕ
            current_app.logger.info(f"🔥 [API] /statistics-extended - ОТЛАДКА для пользователя {redmine_user_id}:")
            current_app.logger.info(f"   - Логин: {current_user.username}")
            current_app.logger.info(f"   - Email: {current_user.email}")
            current_app.logger.info(f"   - Redmine ID из БД: {current_user.id_redmine_user}")
            current_app.logger.info(f"   - Используемый Redmine ID: {redmine_user_id}")

            # Проверяем, есть ли вообще задачи сегодня для этого пользователя
            sql_debug_today = """
                SELECT
                    i.id,
                    i.subject,
                    s.name as status_name,
                    s.is_closed,
                    i.updated_on
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND DATE(i.updated_on) = CURDATE()
                ORDER BY i.updated_on DESC
                LIMIT 5
            """
            cursor.execute(sql_debug_today, (redmine_user_id,))
            debug_tasks = cursor.fetchall()

            current_app.logger.info(f"🔥   - Задач обновленных сегодня: {len(debug_tasks)}")
            for task in debug_tasks:
                current_app.logger.info(f"🔥     * #{task['id']}: {task['subject'][:50]}... - {task['status_name']} (закрыт: {task['is_closed']}) - {task['updated_on']}")

            # Проверяем конкретно закрытые задачи сегодня
            sql_debug_closed = """
                SELECT
                    i.id,
                    i.subject,
                    s.name as status_name,
                    i.updated_on
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 1
                AND DATE(i.updated_on) = CURDATE()
                ORDER BY i.updated_on DESC
            """
            cursor.execute(sql_debug_closed, (redmine_user_id,))
            debug_closed = cursor.fetchall()

            current_app.logger.info(f"🔥   - Закрытых задач сегодня: {len(debug_closed)}")
            for task in debug_closed:
                current_app.logger.info(f"🔥     * #{task['id']}: {task['subject'][:50]}... - {task['status_name']} - {task['updated_on']}")

            # 6. ЗАВЕРШЕННЫЕ задачи (закрытые за неделю) - УПРОЩЕННАЯ ЛОГИКА
            sql_closed_week = """
                SELECT COUNT(*) as closed_week_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 1
                AND i.updated_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            """
            cursor.execute(sql_closed_week, (redmine_user_id,))
            result = cursor.fetchone()
            closed_week = result['closed_week_count'] if result else 0

            current_app.logger.info(f"🔥 [API] /statistics-extended - закрытые за неделю: {closed_week}")

            # 7. ЗАДАЧИ В РАБОТЕ (открытые, не новые)
            sql_in_progress = """
                SELECT COUNT(*) as in_progress_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                LEFT JOIN u_statuses us ON s.id = us.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND LOWER(COALESCE(us.name, s.name)) NOT LIKE '%%новая%%'
                AND LOWER(COALESCE(us.name, s.name)) NOT LIKE '%%new%%'
                AND LOWER(COALESCE(us.name, s.name)) NOT LIKE '%%открыт%%'
            """
            cursor.execute(sql_in_progress, (redmine_user_id,))
            result = cursor.fetchone()
            in_progress_tasks = result['in_progress_count'] if result else 0

            current_app.logger.info(f"🔥 [API] /statistics-extended - задачи в работе: {in_progress_tasks}")

            # 8. ИЗМЕНЕНИЯ В РАБОТЕ (обновленные сегодня, не закрытые)
            sql_progress_today = """
                SELECT COUNT(*) as progress_today_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND DATE(i.updated_on) = CURDATE()
                AND DATE(i.created_on) != CURDATE()
            """
            cursor.execute(sql_progress_today, (redmine_user_id,))
            result = cursor.fetchone()
            progress_today = result['progress_today_count'] if result else 0

            # 9. ИЗМЕНЕНИЯ В РАБОТЕ (обновленные за неделю, не закрытые)
            sql_progress_week = """
                SELECT COUNT(*) as progress_week_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND i.updated_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                AND DATE(i.created_on) != DATE(i.updated_on)
            """
            cursor.execute(sql_progress_week, (redmine_user_id,))
            result = cursor.fetchone()
            progress_week = result['progress_week_count'] if result else 0

            # 10. ДЕТАЛЬНАЯ статистика по статусам с локализацией
            sql_detailed = """
                SELECT
                    s.id as status_id,
                    s.name as original_name,
                    COALESCE(us.name, s.name) as localized_name,
                    s.is_closed,
                    COUNT(i.id) as task_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                LEFT JOIN u_statuses us ON s.id = us.id
                WHERE i.assigned_to_id = %s
                GROUP BY s.id, s.name, us.name, s.is_closed
                ORDER BY s.is_closed ASC, task_count DESC
            """
            cursor.execute(sql_detailed, (redmine_user_id,))
            status_details = cursor.fetchall()

            # Обрабатываем детальную статистику
            status_breakdown = {}
            new_tasks_count = 0  # Для подсчета новых задач

            # НОВОЕ: Группировка статусов для аккордеона
            status_groups = {
                "new": {
                    "name": "Новые",
                    "total": 0,
                    "statuses": []
                },
                "in_progress": {
                    "name": "В работе",
                    "total": 0,
                    "statuses": []
                },
                "closed": {
                    "name": "Завершённые",
                    "total": 0,
                    "statuses": []
                }
            }

            for status_row in status_details:
                status_id = status_row['status_id']
                original_name = status_row['original_name']
                localized_name = status_row['localized_name']
                task_count = status_row['task_count']
                is_closed = bool(status_row['is_closed'])

                status_breakdown[localized_name] = task_count

                # Создаем объект статуса для детализации
                status_detail = {
                    "id": status_id,
                    "original_name": original_name,
                    "localized_name": localized_name,
                    "count": task_count,
                    "is_closed": is_closed
                }

                # Группируем статусы
                if is_closed:
                    # Завершённые задачи
                    status_groups["closed"]["statuses"].append(status_detail)
                    status_groups["closed"]["total"] += task_count
                else:
                    # Открытые задачи - разделяем на новые и в работе
                    status_name_lower = localized_name.lower().strip()
                    if any(keyword in status_name_lower for keyword in ['новая', 'новый', 'новое', 'new', 'открыт']):
                        # Новые задачи
                        status_groups["new"]["statuses"].append(status_detail)
                        status_groups["new"]["total"] += task_count
                        new_tasks_count += task_count
                    else:
                        # В работе
                        status_groups["in_progress"]["statuses"].append(status_detail)
                        status_groups["in_progress"]["total"] += task_count

            # Сортируем статусы в каждой группе по количеству задач (убывание)
            for group in status_groups.values():
                group["statuses"].sort(key=lambda x: x["count"], reverse=True)

            # Вычисляем изменения для отображения - ИСПРАВЛЕНО
            # ИСПРАВЛЕНИЕ: Правильная логика подсчета изменений
            # Вместо new_week - closed_week используем более точный подход

            # Подсчет чистого изменения: задачи созданные минус задачи закрытые за неделю
            # Но учитываем только те задачи, которые реально влияют на общее количество
            sql_net_change_week = """
                SELECT
                    (SELECT COUNT(*) FROM issues i
                     WHERE i.assigned_to_id = %s
                     AND i.created_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)) -
                    (SELECT COUNT(*) FROM issues i
                     INNER JOIN issue_statuses s ON i.status_id = s.id
                     WHERE i.assigned_to_id = %s
                     AND s.is_closed = 1
                     AND i.updated_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                     AND i.created_on < DATE_SUB(CURDATE(), INTERVAL 7 DAY)) as net_change
            """
            cursor.execute(sql_net_change_week, (redmine_user_id, redmine_user_id))
            result = cursor.fetchone()
            net_change_week = result['net_change'] if result else 0

            # Альтернативный подход: простое вычисление разности
            total_change_week = new_week - closed_week

            # Добавляем отладочную информацию для анализа
            current_app.logger.info(f"🔥 [API] /statistics-extended - ДЕТАЛЬНАЯ ОТЛАДКА изменений за неделю:")
            current_app.logger.info(f"  new_week = {new_week} (новые задачи за неделю)")
            current_app.logger.info(f"  closed_week = {closed_week} (закрытые задачи за неделю)")
            current_app.logger.info(f"  total_change_week = {total_change_week} (new_week - closed_week)")
            current_app.logger.info(f"  net_change_week = {net_change_week} (чистое изменение)")

            # ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА: Проверяем каждый запрос отдельно
            current_app.logger.info(f"🔥 [DEBUG] ДЕТАЛЬНАЯ ПРОВЕРКА ЗАПРОСОВ:")

            # Проверяем новые задачи за неделю
            sql_debug_new_week = """
                SELECT
                    i.id,
                    i.subject,
                    i.created_on,
                    s.name as status_name,
                    s.is_closed
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 0
                AND i.created_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY i.created_on DESC
            """
            cursor.execute(sql_debug_new_week, (redmine_user_id,))
            debug_new_week = cursor.fetchall()

            current_app.logger.info(f"🔥   НОВЫЕ за неделю: {len(debug_new_week)} задач")
            for task in debug_new_week:
                current_app.logger.info(f"🔥     * #{task['id']}: создана {task['created_on']} - {task['status_name']}")

            # Проверяем закрытые задачи за неделю
            sql_debug_closed_week = """
                SELECT
                    i.id,
                    i.subject,
                    i.created_on,
                    i.updated_on,
                    s.name as status_name
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 1
                AND i.updated_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY i.updated_on DESC
            """
            cursor.execute(sql_debug_closed_week, (redmine_user_id,))
            debug_closed_week = cursor.fetchall()

            current_app.logger.info(f"🔥   ЗАКРЫТЫЕ за неделю: {len(debug_closed_week)} задач")
            for task in debug_closed_week:
                current_app.logger.info(f"🔥     * #{task['id']}: создана {task['created_on']}, закрыта {task['updated_on']} - {task['status_name']}")

            # Проверяем, есть ли задачи, созданные И закрытые на этой неделе
            sql_debug_created_and_closed = """
                SELECT
                    i.id,
                    i.subject,
                    i.created_on,
                    i.updated_on,
                    s.name as status_name
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s
                AND s.is_closed = 1
                AND i.created_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                AND i.updated_on >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY i.created_on DESC
            """
            cursor.execute(sql_debug_created_and_closed, (redmine_user_id,))
            debug_created_and_closed = cursor.fetchall()

            current_app.logger.info(f"🔥   СОЗДАНЫ И ЗАКРЫТЫ за неделю: {len(debug_created_and_closed)} задач")
            for task in debug_created_and_closed:
                current_app.logger.info(f"🔥     * #{task['id']}: создана {task['created_on']}, закрыта {task['updated_on']}")

            # Используем более точное значение для отображения
            final_change_week = net_change_week if net_change_week != 0 else total_change_week

            # Формируем ответ с реальными данными
            response_data = {
                "success": True,
                "total_tasks": total_tasks,
                "new_tasks": new_tasks_count,
                "in_progress_tasks": in_progress_tasks,
                "closed_tasks": closed_tasks,
                "status_breakdown": status_breakdown,

                # НОВОЕ: Детализация статусов для аккордеона
                "status_groups": status_groups,

                # Изменения за периоды
                "changes": {
                    "total": {
                        "week": total_change_week,
                        "week_text": f"создано {new_week}, закрыто {closed_week} за неделю" if total_change_week != 0 else "без изменений за неделю"
                    },
                    "new": {
                        "today": new_today,
                        "today_text": f"+{new_today} сегодня" if new_today > 0 else "без новых сегодня"
                    },
                    "progress": {
                        "today": progress_today,
                        "today_text": f"+{progress_today} обновлено сегодня" if progress_today > 0 else "без изменений"
                    },
                    "closed": {
                        "today": closed_today,
                        "today_text": f"+{closed_today} сегодня" if closed_today > 0 else "без завершений сегодня"
                    }
                },

                # Дополнительная статистика
                "details": {
                    "new_today": new_today,
                    "new_week": new_week,
                    "closed_today": closed_today,
                    "closed_week": closed_week,
                    "progress_today": progress_today,
                    "progress_week": progress_week
                },

                "source": "mysql_redmine_extended"
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /statistics-extended выполнен за {execution_time:.2f}с")
            current_app.logger.info(f"[API] /statistics-extended - статистика: Всего={total_tasks}, Новые={new_tasks_count}, В работе={in_progress_tasks}, Закрытые={closed_tasks}")

            return jsonify(response_data)

        except Exception as db_error:
            current_app.logger.error(f"[API] Ошибка БД в /statistics-extended: {str(db_error)}. Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": f"Ошибка базы данных: {str(db_error)}",
                "success": False
            }), 500
        finally:
            cursor.close()
            mysql_conn.close()

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /statistics-extended: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/statistics-debug", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_statistics_debug_api():
    """
    ОТЛАДОЧНЫЙ API для диагностики проблемы с SQL запросами
    Максимально простые запросы по одному
    """
    current_app.logger.info(f"🔥 [DEBUG] /statistics-debug - НАЧАЛО ОТЛАДОЧНОГО ЗАПРОСА от {current_user.username}")

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # ИСПРАВЛЕНИЕ: Используем правильную конфигурацию
        config = Config()
        mysql_conn = get_connection(
            config.DB_REDMINE_HOST,
            config.DB_REDMINE_USER_NAME,
            config.DB_REDMINE_PASSWORD,
            config.DB_REDMINE_NAME
        )

        if not mysql_conn:
            current_app.logger.error("🔥 [DEBUG] - не удалось подключиться к MySQL Redmine")
            return jsonify({
                "error": "Ошибка подключения к базе данных Redmine",
                "success": False
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_id = current_user.id_redmine_user
        current_app.logger.info(f"🔥 [DEBUG] - redmine_user_id из БД: {redmine_user_id}")

        if not redmine_user_id:
            current_app.logger.info(f"🔥 [DEBUG] - Поиск пользователя в MySQL")

            cursor = mysql_conn.cursor()
            user_email = current_user.email if current_user.email else ''

            current_app.logger.info(f"🔥 [DEBUG] - Поиск: login='{current_user.username}', email='{user_email}'")

            try:
                # ТЕСТ 1: Самый простой запрос
                current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 1: Поиск по логину")
                cursor.execute("SELECT id FROM users WHERE login = %s LIMIT 1", (current_user.username,))
                user_result = cursor.fetchone()

                if user_result:
                    redmine_user_id = user_result['id']
                    current_app.logger.info(f"🔥 [DEBUG] - найден ID по логину: {redmine_user_id}")
                else:
                    current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 2: Поиск по email")
                    if user_email:
                        cursor.execute("SELECT id FROM users WHERE mail = %s LIMIT 1", (user_email,))
                        user_result = cursor.fetchone()
                        if user_result:
                            redmine_user_id = user_result['id']
                            current_app.logger.info(f"🔥 [DEBUG] - найден ID по email: {redmine_user_id}")

                if not redmine_user_id:
                    current_app.logger.error(f"🔥 [DEBUG] - пользователь не найден")
                    return jsonify({
                        "error": "Пользователь не найден",
                        "success": False
                    }), 400
            except Exception as find_error:
                current_app.logger.error(f"🔥 [DEBUG] - ошибка поиска: {find_error}")
                return jsonify({
                    "error": f"Ошибка поиска: {str(find_error)}",
                    "success": False
                }), 500
            finally:
                cursor.close()

        # ТЕСТ 3: Простейший запрос количества задач
        cursor = mysql_conn.cursor()

        try:
            current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 3: Простой подсчет задач для пользователя {redmine_user_id}")

            cursor.execute("SELECT COUNT(*) as total FROM issues WHERE assigned_to_id = %s", (redmine_user_id,))
            result = cursor.fetchone()
            total_tasks = result['total'] if result else 0

            current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 3 УСПЕШЕН: {total_tasks} задач")

            # ТЕСТ 4: Простой запрос статусов
            current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 4: Простой запрос статусов")

            cursor.execute("SELECT COUNT(*) as closed FROM issues i JOIN issue_statuses s ON i.status_id = s.id WHERE i.assigned_to_id = %s AND s.is_closed = 1", (redmine_user_id,))
            result = cursor.fetchone()
            closed_tasks = result['closed'] if result else 0

            current_app.logger.info(f"🔥 [DEBUG] - ТЕСТ 4 УСПЕШЕН: {closed_tasks} закрытых задач")

            response_data = {
                "success": True,
                "debug_info": {
                    "redmine_user_id": redmine_user_id,
                    "total_tasks": total_tasks,
                    "closed_tasks": closed_tasks,
                    "username": current_user.username,
                    "email": user_email
                },
                "message": "Отладочные тесты прошли успешно"
            }

            current_app.logger.info(f"🔥 [DEBUG] - ВСЕ ТЕСТЫ УСПЕШНЫ: {response_data}")
            return jsonify(response_data)

        except Exception as db_error:
            current_app.logger.error(f"🔥 [DEBUG] - Ошибка БД в тестах: {str(db_error)}")
            import traceback
            current_app.logger.error(f"🔥 [DEBUG] - Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": f"Ошибка базы данных: {str(db_error)}",
                "success": False
            }), 500
        finally:
            cursor.close()
            mysql_conn.close()

    except Exception as e:
        current_app.logger.error(f"🔥 [DEBUG] - Критическая ошибка: {str(e)}")
        import traceback
        current_app.logger.error(f"🔥 [DEBUG] - Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


# ===== УТИЛИТЫ ДЛЯ API =====

def validate_api_request(required_params=None):
    """
    Декоратор для валидации API запросов
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if required_params:
                for param in required_params:
                    if param not in request.args and param not in request.json:
                        return jsonify({
                            "error": f"Отсутствует обязательный параметр: {param}",
                            "success": False
                        }), 400
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


def handle_api_error(error_message, exception=None, status_code=500):
    """
    Стандартная обработка ошибок API
    """
    if exception:
        current_app.logger.error(f"[API] {error_message}: {str(exception)}. Traceback: {traceback.format_exc()}")
    else:
        current_app.logger.error(f"[API] {error_message}")

    return jsonify({
        "error": error_message,
        "success": False
    }), status_code
