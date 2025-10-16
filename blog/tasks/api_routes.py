# blog/tasks/api_routes.py
"""
API endpoints для функционала изменения статуса задач
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
import time
import traceback
from datetime import datetime

# Импорты из существующих модулей
from blog.utils.cache_manager import weekend_performance_optimizer
from blog.tasks.utils import create_redmine_connector
from redmine import (
    get_connection,
    db_redmine_host,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name
)


# Получаем экземпляр CSRF для исключений
from blog import csrf

# Создаем Blueprint для API
api_bp = Blueprint('tasks_api', __name__, url_prefix='/tasks/api')

# ===== API ENDPOINTS ДЛЯ ИЗМЕНЕНИЯ СТАТУСА =====

@api_bp.route("/task/<int:task_id>", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_by_id(task_id):
    """
    API для получения задачи по ID
    """
    current_app.logger.info(f"[API] GET /task/{task_id} - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "data": None
            }), 403

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False,
                "data": None
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "data": None
            }), 500

        try:
            # Получаем задачу из Redmine
            task = redmine_connector.redmine.issue.get(task_id, include=['status', 'priority', 'project', 'assigned_to', 'start_date', 'due_date', 'closed_on', 'easy_email_to', 'easy_email_cc'])

            # Получаем локализованные названия из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            task_data = {
                "id": task.id,
                "subject": task.subject,
                "description": getattr(task, 'description', ''),
                "status_id": task.status.id if hasattr(task, 'status') and task.status else None,
                "status_name": task.status.name if hasattr(task, 'status') and task.status else "Неизвестен",
                "priority_id": task.priority.id if hasattr(task, 'priority') and task.priority else None,
                "priority_name": task.priority.name if hasattr(task, 'priority') and task.priority else "Неизвестен",
                "project_id": task.project.id if hasattr(task, 'project') and task.project else None,
                "project_name": task.project.name if hasattr(task, 'project') and task.project else "Неизвестен",
                "assigned_to_id": task.assigned_to.id if hasattr(task, 'assigned_to') and task.assigned_to else None,
                "assigned_to_name": task.assigned_to.name if hasattr(task, 'assigned_to') and task.assigned_to else "Неизвестен",
                "created_on": task.created_on.isoformat() if hasattr(task, 'created_on') and task.created_on else None,
                "updated_on": task.updated_on.isoformat() if hasattr(task, 'updated_on') and task.updated_on else None,
                "start_date": task.start_date.isoformat() if hasattr(task, 'start_date') and task.start_date else None,
                "due_date": task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None,
                "closed_on": task.closed_on.isoformat() if hasattr(task, 'closed_on') and task.closed_on else None,
                "easy_email_to": getattr(task, 'easy_email_to', None),
                "easy_email_cc": getattr(task, 'easy_email_cc', None),
                "done_ratio": getattr(task, 'done_ratio', 0),
                "tracker_id": task.tracker.id if hasattr(task, 'tracker') and task.tracker else None,
                "tracker_name": task.tracker.name if hasattr(task, 'tracker') and task.tracker else None
            }

            # Получаем локализованные названия
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    # Статусы
                    if task_data["status_id"]:
                        try:
                            cursor.execute("SELECT name FROM u_statuses WHERE id = %s", (task_data["status_id"],))
                            status_row = cursor.fetchone()
                            if status_row:
                                task_data["status_name"] = status_row['name']
                        except Exception as status_error:
                            current_app.logger.warning(f"[API] Ошибка получения статуса {task_data['status_id']}: {status_error}")
                            # Используем название из Redmine API
                            task_data["status_name"] = task.status.name if hasattr(task, 'status') and task.status else "Неизвестен"

                    # Приоритеты
                    if task_data["priority_id"]:
                        try:
                            cursor.execute("SELECT name FROM enumerations WHERE id = %s AND type = 'IssuePriority'", (task_data["priority_id"],))
                            priority_row = cursor.fetchone()
                            if priority_row:
                                task_data["priority_name"] = priority_row['name']
                        except Exception as priority_error:
                            current_app.logger.warning(f"[API] Ошибка получения приоритета {task_data['priority_id']}: {priority_error}")
                            # Используем название из Redmine API
                            task_data["priority_name"] = task.priority.name if hasattr(task, 'priority') and task.priority else "Неизвестен"

                    # Проекты
                    if task_data["project_id"]:
                        try:
                            cursor.execute("SELECT name FROM projects WHERE id = %s", (task_data["project_id"],))
                            project_row = cursor.fetchone()
                            if project_row:
                                task_data["project_name"] = project_row['name']
                        except Exception as project_error:
                            current_app.logger.warning(f"[API] Ошибка получения проекта {task_data['project_id']}: {project_error}")
                            # Используем название из Redmine API
                            task_data["project_name"] = task.project.name if hasattr(task, 'project') and task.project else "Неизвестен"

                    # Назначенные пользователи
                    if task_data["assigned_to_id"]:
                        try:
                            cursor.execute("SELECT firstname, lastname FROM users WHERE id = %s", (task_data["assigned_to_id"],))
                            user_row = cursor.fetchone()
                            if user_row:
                                task_data["assigned_to_name"] = f"{user_row['firstname']} {user_row['lastname']}".strip()
                        except Exception as user_error:
                            current_app.logger.warning(f"[API] Ошибка получения пользователя {task_data['assigned_to_id']}: {user_error}")
                            # Используем название из Redmine API
                            task_data["assigned_to_name"] = task.assigned_to.name if hasattr(task, 'assigned_to') and task.assigned_to else "Неизвестен"

                finally:
                    cursor.close()
                    mysql_conn.close()

            response_data = {
                "success": True,
                "data": task_data
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] GET /task/{task_id} выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения данных задачи: {str(redmine_error)}",
                "success": False,
                "data": None
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в GET /task/{task_id}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "data": None
        }), 500


@api_bp.route("/task/<int:task_id>/statuses", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_available_statuses(task_id):
    """
    API для получения доступных статусов для конкретной задачи
    """
    current_app.logger.info(f"[API] /task/{task_id}/statuses - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "statuses": []
            }), 403

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False,
                "statuses": []
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "statuses": []
            }), 500

        try:
            # Получаем детали задачи для определения доступных статусов
            task = redmine_connector.redmine.issue.get(task_id)
            current_status_id = task.status.id if hasattr(task, 'status') and task.status else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий статус ID = {current_status_id}")

            # Получаем все доступные статусы из Redmine
            all_statuses = redmine_connector.redmine.issue_status.all()

            # Получаем локализованные названия статусов из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            localized_statuses = {}
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    cursor.execute("SELECT id, name FROM u_statuses")
                    for row in cursor.fetchall():
                        localized_statuses[row['id']] = row['name']
                finally:
                    cursor.close()
                    mysql_conn.close()

            # Формируем список доступных статусов
            available_statuses = []
            for status in all_statuses:
                # Пропускаем текущий статус
                if status.id == current_status_id:
                    continue

                status_name = localized_statuses.get(status.id, status.name)
                available_statuses.append({
                    "id": status.id,
                    "name": status_name,
                    "original_name": status.name
                })

            # Также включаем текущий статус для отображения
            current_status_name = localized_statuses.get(current_status_id, "Неизвестен")
            current_status = {
                "id": current_status_id,
                "name": current_status_name,
                "original_name": task.status.name if hasattr(task, 'status') and task.status else "Unknown"
            }

            response_data = {
                "success": True,
                "task_id": task_id,
                "current_status": current_status,
                "available_statuses": available_statuses,
                "total_available": len(available_statuses)
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /task/{task_id}/statuses выполнен за {execution_time:.2f}с, доступно {len(available_statuses)} статусов")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения статусов для задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения данных задачи: {str(redmine_error)}",
                "success": False,
                "statuses": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /task/{task_id}/statuses: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "statuses": []
        }), 500


@api_bp.route("/task/<int:task_id>/status", methods=["PUT"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def update_task_status(task_id):
    """
    API для изменения статуса задачи через Redmine REST API
    """
    current_app.logger.info(f"[API] PUT /task/{task_id}/status - запрос от {current_user.username}")
    current_app.logger.info(f"[API] Заголовки запроса: {dict(request.headers)}")
    current_app.logger.info(f"[API] Данные запроса: {request.get_json()}")
    start_time = time.time()

    try:
        current_app.logger.info(f"[API] Проверка прав доступа: current_user.is_redmine_user = {current_user.is_redmine_user}")

        if not current_user.is_redmine_user:
            current_app.logger.error(f"[API] Доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'status_id' not in data:
            return jsonify({
                "error": "Не указан новый статус (status_id)",
                "success": False
            }), 400

        new_status_id = data['status_id']
        comment = data.get('comment', '')  # Необязательный комментарий

        current_app.logger.info(f"[API] Изменение статуса задачи {task_id} на {new_status_id}, комментарий: '{comment}'")

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id)
            old_status_id = task.status.id if hasattr(task, 'status') and task.status else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий статус {old_status_id} -> новый статус {new_status_id}")

            # Проверяем, что статус действительно изменился
            if old_status_id == new_status_id:
                return jsonify({
                    "error": "Новый статус совпадает с текущим",
                    "success": False
                }), 400

            # Подготавливаем данные для обновления
            update_data = {
                "status_id": new_status_id
            }

            # Добавляем комментарий если указан
            if comment.strip():
                update_data["notes"] = comment.strip()

            # Выполняем обновление через Redmine REST API
            result = redmine_connector.redmine.issue.update(task_id, **update_data)

            current_app.logger.info(f"[API] Статус задачи {task_id} успешно изменен на {new_status_id}")

            # Получаем обновленную задачу для возврата актуальных данных
            updated_task = redmine_connector.redmine.issue.get(task_id, include=['status', 'priority', 'project'])

            # Получаем локализованное название нового статуса
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            new_status_name = "Неизвестен"
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    cursor.execute("SELECT name FROM u_statuses WHERE id = %s", (new_status_id,))
                    result_row = cursor.fetchone()
                    if result_row:
                        new_status_name = result_row['name']
                    else:
                        new_status_name = updated_task.status.name if hasattr(updated_task, 'status') and updated_task.status else "Неизвестен"
                finally:
                    cursor.close()
                    mysql_conn.close()

            response_data = {
                "success": True,
                "task_id": task_id,
                "old_status_id": old_status_id,
                "new_status_id": new_status_id,
                "new_status_name": new_status_name,
                "comment": comment,
                "updated_at": datetime.now().isoformat(),
                "message": f"Статус задачи успешно изменен на '{new_status_name}'"
            }

            # Обрабатываем уведомления после изменения статуса
            try:
                from blog.notification_service import check_notifications_improved
                current_app.logger.info(f"[API] Запуск обработки уведомлений для пользователя {current_user.username}")
                notifications_processed = check_notifications_improved(current_user.email, current_user.id)
                current_app.logger.info(f"[API] Обработано {notifications_processed} уведомлений для пользователя {current_user.username}")
            except Exception as notification_error:
                current_app.logger.error(f"[API] Ошибка при обработке уведомлений: {notification_error}")

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] PUT /task/{task_id}/status выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка изменения статуса задачи {task_id}: {str(redmine_error)}")

            # Обработка специфических ошибок Redmine
            error_message = str(redmine_error)
            if "422" in error_message or "Unprocessable Entity" in error_message:
                error_message = "Некорректные данные для изменения статуса. Проверьте права доступа."
            elif "401" in error_message or "Unauthorized" in error_message:
                error_message = "Отсутствуют права для изменения статуса этой задачи."
            elif "403" in error_message or "Forbidden" in error_message:
                error_message = "Доступ запрещен. Недостаточно прав для изменения статуса."
            elif "404" in error_message or "Not Found" in error_message:
                error_message = f"Задача #{task_id} не найдена."

            return jsonify({
                "error": error_message,
                "success": False,
                "technical_error": str(redmine_error)
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в PUT /task/{task_id}/status: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/task/<int:task_id>/priorities", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_available_priorities(task_id):
    """
    API для получения доступных приоритетов для конкретной задачи
    """
    current_app.logger.info(f"[API] /task/{task_id}/priorities - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "priorities": []
            }), 403

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False,
                "priorities": []
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "priorities": []
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id, include=['priority'])
            current_priority = task.priority if hasattr(task, 'priority') and task.priority else None

            # Получаем все доступные приоритеты из Redmine
            redmine_priorities = redmine_connector.redmine.enumeration.filter(resource='issue_priorities')
            available_priorities = [{"id": priority.id, "name": priority.name} for priority in redmine_priorities]

            # Получаем локализованные названия приоритетов из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    # Получаем локализованные названия приоритетов
                    cursor.execute("""
                        SELECT e.id, up.name
                        FROM enumerations e
                        JOIN u_Priority up ON e.id = up.id
                        WHERE e.type = 'IssuePriority'
                        AND e.active = 1
                        ORDER BY e.position, up.name
                    """)
                    localized_priorities = {row["id"]: row["name"] for row in cursor.fetchall()}

                    # Обновляем названия приоритетов локализованными версиями
                    for priority in available_priorities:
                        if priority["id"] in localized_priorities:
                            priority["name"] = localized_priorities[priority["id"]]

                    # Получаем локализованное название текущего приоритета
                    if current_priority:
                        current_priority_name = localized_priorities.get(current_priority.id, current_priority.name)
                        current_priority_data = {
                            "id": current_priority.id,
                            "name": current_priority_name
                        }
                    else:
                        current_priority_data = None

                finally:
                    cursor.close()
                    mysql_conn.close()
            else:
                # Если нет подключения к MySQL, используем данные из Redmine
                current_priority_data = {
                    "id": current_priority.id,
                    "name": current_priority.name
                } if current_priority else None

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /task/{task_id}/priorities выполнен за {execution_time:.2f}с")

            return jsonify({
                "success": True,
                "current_priority": current_priority_data,
                "available_priorities": available_priorities
            })

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения приоритетов для задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения приоритетов: {str(redmine_error)}",
                "success": False,
                "priorities": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /task/{task_id}/priorities: {str(e)}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "priorities": []
        }), 500


@api_bp.route("/task/<int:task_id>/priority", methods=["PUT"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def update_task_priority(task_id):
    """
    API для изменения приоритета задачи через Redmine REST API
    """
    current_app.logger.info(f"[API] PUT /task/{task_id}/priority - запрос от {current_user.username}")
    current_app.logger.info(f"[API] Заголовки запроса: {dict(request.headers)}")
    current_app.logger.info(f"[API] Данные запроса: {request.get_json()}")
    start_time = time.time()

    try:
        current_app.logger.info(f"[API] Проверка прав доступа: current_user.is_redmine_user = {current_user.is_redmine_user}")

        if not current_user.is_redmine_user:
            current_app.logger.error(f"[API] Доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'priority_id' not in data:
            return jsonify({
                "error": "Не указан новый приоритет (priority_id)",
                "success": False
            }), 400

        new_priority_id = data['priority_id']
        comment = data.get('comment', '')  # Необязательный комментарий

        current_app.logger.info(f"[API] Изменение приоритета задачи {task_id} на {new_priority_id}, комментарий: '{comment}'")

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id)
            old_priority_id = task.priority.id if hasattr(task, 'priority') and task.priority else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий приоритет {old_priority_id} -> новый приоритет {new_priority_id}")

            # Проверяем, что приоритет действительно изменился
            if old_priority_id == new_priority_id:
                return jsonify({
                    "error": "Новый приоритет совпадает с текущим",
                    "success": False
                }), 400

            # Подготавливаем данные для обновления
            update_data = {
                "priority_id": new_priority_id
            }

            # Добавляем комментарий если указан
            if comment.strip():
                update_data["notes"] = comment.strip()

            # Выполняем обновление через Redmine REST API
            result = redmine_connector.redmine.issue.update(task_id, **update_data)

            current_app.logger.info(f"[API] Приоритет задачи {task_id} успешно изменен на {new_priority_id}")

            # Получаем обновленную задачу для возврата актуальных данных
            updated_task = redmine_connector.redmine.issue.get(task_id, include=['priority'])

            # Получаем локализованное название нового приоритета
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            new_priority_name = "Неизвестен"
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    cursor.execute("SELECT name FROM u_Priority WHERE id = %s", (new_priority_id,))
                    result_row = cursor.fetchone()
                    if result_row:
                        new_priority_name = result_row['name']
                    else:
                        new_priority_name = updated_task.priority.name if hasattr(updated_task, 'priority') and updated_task.priority else "Неизвестен"
                finally:
                    cursor.close()
                    mysql_conn.close()

            response_data = {
                "success": True,
                "task_id": task_id,
                "old_priority_id": old_priority_id,
                "new_priority_id": new_priority_id,
                "new_priority_name": new_priority_name,
                "comment": comment,
                "updated_at": datetime.now().isoformat(),
                "message": f"Приоритет задачи успешно изменен на '{new_priority_name}'"
            }

            # Обрабатываем уведомления после изменения приоритета
            try:
                from blog.notification_service import check_notifications_improved
                current_app.logger.info(f"[API] Запуск обработки уведомлений для пользователя {current_user.username}")
                notifications_processed = check_notifications_improved(current_user.email, current_user.id)
                current_app.logger.info(f"[API] Обработано {notifications_processed} уведомлений для пользователя {current_user.username}")
            except Exception as notification_error:
                current_app.logger.error(f"[API] Ошибка при обработке уведомлений: {notification_error}")

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] PUT /task/{task_id}/priority выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка изменения приоритета задачи {task_id}: {str(redmine_error)}")

            # Обработка специфических ошибок Redmine
            error_message = str(redmine_error)
            if "422" in error_message or "Unprocessable Entity" in error_message:
                error_message = "Некорректные данные для изменения приоритета. Проверьте права доступа."
            elif "401" in error_message or "Unauthorized" in error_message:
                error_message = "Отсутствуют права для изменения приоритета этой задачи."
            elif "403" in error_message or "Forbidden" in error_message:
                error_message = "Доступ запрещен. Недостаточно прав для изменения приоритета."
            elif "404" in error_message or "Not Found" in error_message:
                error_message = f"Задача #{task_id} не найдена."

            return jsonify({
                "error": error_message,
                "success": False,
                "technical_error": str(redmine_error)
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в PUT /task/{task_id}/priority: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/users", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_available_users():
    """
    API для получения списка доступных пользователей для назначения исполнителем
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

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False,
                "users": []
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "users": []
            }), 500

        try:
            # Получаем всех пользователей из Redmine
            redmine_users = redmine_connector.redmine.user.all()
            available_users = []

            # Получаем локализованные названия из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    # Получаем активных пользователей из MySQL
                    cursor.execute("""
                        SELECT id, firstname, lastname, login, type, status
                        FROM users
                        WHERE status = 1 AND type = 'User'
                        ORDER BY lastname, firstname
                    """)

                    mysql_users = {row["id"]: {
                        "id": row["id"],
                        "firstname": row["firstname"],
                        "lastname": row["lastname"],
                        "login": row["login"],
                        "full_name": f"{row['lastname'] or ''} {row['firstname'] or ''}".strip()
                    } for row in cursor.fetchall()}

                    # Объединяем данные из Redmine и MySQL
                    for user in redmine_users:
                        if hasattr(user, 'id') and user.id in mysql_users:
                            mysql_user = mysql_users[user.id]
                            available_users.append({
                                "id": mysql_user["id"],
                                "name": mysql_user["full_name"],
                                "login": mysql_user["login"],
                                "firstname": mysql_user["firstname"],
                                "lastname": mysql_user["lastname"]
                            })
                        else:
                            # Если нет в MySQL, используем данные из Redmine
                            available_users.append({
                                "id": user.id,
                                "name": user.name if hasattr(user, 'name') else f"{getattr(user, 'lastname', '')} {getattr(user, 'firstname', '')}".strip(),
                                "login": user.login if hasattr(user, 'login') else '',
                                "firstname": getattr(user, 'firstname', ''),
                                "lastname": getattr(user, 'lastname', '')
                            })

                finally:
                    cursor.close()
                    mysql_conn.close()
            else:
                # Если нет подключения к MySQL, используем данные из Redmine
                for user in redmine_users:
                    available_users.append({
                        "id": user.id,
                        "name": user.name if hasattr(user, 'name') else f"{getattr(user, 'lastname', '')} {getattr(user, 'firstname', '')}".strip(),
                        "login": user.login if hasattr(user, 'login') else '',
                        "firstname": getattr(user, 'firstname', ''),
                        "lastname": getattr(user, 'lastname', '')
                    })

            # Сортируем по имени
            available_users.sort(key=lambda x: x["name"])

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /users выполнен за {execution_time:.2f}с ({len(available_users)} пользователей)")

            return jsonify({
                "success": True,
                "users": available_users
            })

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения пользователей: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения пользователей: {str(redmine_error)}",
                "success": False,
                "users": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /users: {str(e)}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "users": []
        }), 500


@api_bp.route("/task/<int:task_id>/assignee", methods=["PUT"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def update_task_assignee(task_id):
    """
    API для изменения исполнителя задачи через Redmine REST API
    """
    current_app.logger.info(f"[API] PUT /task/{task_id}/assignee - запрос от {current_user.username}")
    current_app.logger.info(f"[API] Заголовки запроса: {dict(request.headers)}")
    current_app.logger.info(f"[API] Данные запроса: {request.get_json()}")
    start_time = time.time()

    try:
        current_app.logger.info(f"[API] Проверка прав доступа: current_user.is_redmine_user = {current_user.is_redmine_user}")

        if not current_user.is_redmine_user:
            current_app.logger.error(f"[API] Доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'assignee_id' not in data:
            return jsonify({
                "error": "Не указан новый исполнитель (assignee_id)",
                "success": False
            }), 400

        new_assignee_id = data['assignee_id']
        comment = data.get('comment', '')  # Необязательный комментарий

        current_app.logger.info(f"[API] Изменение исполнителя задачи {task_id} на {new_assignee_id}, комментарий: '{comment}'")

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id)
            old_assignee_id = task.assigned_to.id if hasattr(task, 'assigned_to') and task.assigned_to else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий исполнитель {old_assignee_id} -> новый исполнитель {new_assignee_id}")

            # Проверяем, что исполнитель действительно изменился
            if old_assignee_id == new_assignee_id:
                return jsonify({
                    "error": "Новый исполнитель совпадает с текущим",
                    "success": False
                }), 400

            # Подготавливаем данные для обновления (поддержка снятия назначения)
            update_data = {
                "assigned_to_id": new_assignee_id  # None приведет к снятию исполнителя
            }

            # Добавляем комментарий если указан
            if comment.strip():
                update_data["notes"] = comment.strip()

            # Выполняем обновление через Redmine REST API
            result = redmine_connector.redmine.issue.update(task_id, **update_data)

            current_app.logger.info(f"[API] Исполнитель задачи {task_id} успешно изменен на {new_assignee_id}")

            # Получаем обновленную задачу для возврата актуальных данных
            updated_task = redmine_connector.redmine.issue.get(task_id, include=['assigned_to'])

            # Если исполнитель снят, имя = "Не назначен" и пропускаем запрос к БД
            if new_assignee_id is None:
                new_assignee_name = "Не назначен"
            else:
                # Получаем локализованное название нового исполнителя
                mysql_conn = get_connection(
                    db_redmine_host,
                    db_redmine_user_name,
                    db_redmine_password,
                    db_redmine_name
                )

                new_assignee_name = "Неизвестен"
                if mysql_conn:
                    cursor = mysql_conn.cursor()
                    try:
                        cursor.execute("SELECT CONCAT(IFNULL(lastname, ''), ' ', IFNULL(firstname, '')) as full_name FROM users WHERE id = %s", (new_assignee_id,))
                        result_row = cursor.fetchone()
                        if result_row:
                            new_assignee_name = result_row['full_name'].strip()
                        else:
                            new_assignee_name = updated_task.assigned_to.name if hasattr(updated_task, 'assigned_to') and updated_task.assigned_to else "Неизвестен"
                    finally:
                        cursor.close()
                        mysql_conn.close()

            response_data = {
                "success": True,
                "task_id": task_id,
                "old_assignee_id": old_assignee_id,
                "new_assignee_id": new_assignee_id,
                "new_assignee_name": new_assignee_name,
                "comment": comment,
                "updated_at": datetime.now().isoformat(),
                "message": ("Назначение исполнителя снято" if new_assignee_id is None else f"Исполнитель задачи успешно изменен на '{new_assignee_name}'")
            }

            # Обрабатываем уведомления после изменения исполнителя
            try:
                from blog.notification_service import check_notifications_improved
                current_app.logger.info(f"[API] Запуск обработки уведомлений для пользователя {current_user.username}")
                notifications_processed = check_notifications_improved(current_user.email, current_user.id)
                current_app.logger.info(f"[API] Обработано {notifications_processed} уведомлений для пользователя {current_user.username}")
            except Exception as notification_error:
                current_app.logger.error(f"[API] Ошибка при обработке уведомлений: {notification_error}")

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] PUT /task/{task_id}/assignee выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка изменения исполнителя задачи {task_id}: {str(redmine_error)}")

            # Обработка специфических ошибок Redmine
            error_message = str(redmine_error)
            if "422" in error_message or "Unprocessable Entity" in error_message:
                error_message = "Некорректные данные для изменения исполнителя. Проверьте права доступа."
            elif "401" in error_message or "Unauthorized" in error_message:
                error_message = "Отсутствуют права для изменения исполнителя этой задачи."
            elif "403" in error_message or "Forbidden" in error_message:
                error_message = "Доступ запрещен. Недостаточно прав для изменения исполнителя."
            elif "404" in error_message or "Not Found" in error_message:
                error_message = f"Задача #{task_id} не найдена."

            return jsonify({
                "error": error_message,
                "success": False,
                "technical_error": str(redmine_error)
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в PUT /task/{task_id}/assignee: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/task/<int:task_id>/attachment/<int:attachment_id>/download", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def download_task_attachment(task_id, attachment_id):
    """
    API для скачивания вложения задачи
    """
    current_app.logger.info(f"[API] GET /task/{task_id}/attachment/{attachment_id}/download - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Получаем оригинальный пароль из Oracle для подключения к Redmine
        from blog.tasks.utils import get_user_redmine_password

        actual_password = get_user_redmine_password(current_user.username)
        if not actual_password:
            return jsonify({
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "success": False
            }), 500

        # Создаем коннектор Redmine с оригинальным паролем
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=actual_password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id, include=['attachments'])
            current_app.logger.info(f"[API] Получена задача {task_id} с {len(task.attachments)} вложениями")

            # Ищем нужное вложение
            attachment = None
            for att in task.attachments:
                current_app.logger.info(f"[API] Проверяем вложение {att.id}: {att.filename}")
                if att.id == attachment_id:
                    attachment = att
                    break

            if not attachment:
                current_app.logger.error(f"[API] Вложение #{attachment_id} не найдено в задаче {task_id}")
                return jsonify({
                    "error": f"Вложение #{attachment_id} не найдено",
                    "success": False
                }), 404

            current_app.logger.info(f"[API] Найдено вложение: {attachment.filename} (размер: {attachment.filesize} байт)")

                        # Формируем URL для прямого скачивания из Redmine
            redmine_download_url = f"{redmine_connector.redmine.url}/attachments/download/{attachment_id}"
            current_app.logger.info(f"[API] URL для скачивания: {redmine_download_url}")

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] GET /task/{task_id}/attachment/{attachment_id}/download выполнен за {execution_time:.2f}с")

            # Возвращаем JSON с URL для скачивания
            return jsonify({
                "success": True,
                "download_url": redmine_download_url,
                "filename": attachment.filename,
                "filesize": attachment.filesize
            })

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка скачивания вложения {attachment_id} для задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка скачивания файла: {str(redmine_error)}",
                "success": False
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в GET /task/{task_id}/attachment/{attachment_id}/download: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500


@api_bp.route("/log-performance", methods=["POST"])
@csrf.exempt
@login_required
def log_performance_metrics():
    """
    API для логирования метрик производительности с клиентской стороны
    """
    try:
        data = request.get_json()
        metric = data.get('metric')
        value = data.get('value')
        additional_data = data.get('additional_data', {})

        # Логируем метрики производительности
        current_app.logger.info(f"[PERFORMANCE] {metric}: {value}ms - User: {current_user.username} - Data: {additional_data}")

        # Можно добавить сохранение в базу данных для анализа трендов
        # save_performance_metric(metric, value, current_user.id, additional_data)

        return jsonify({"success": True, "message": "Performance metric logged"})

    except Exception as e:
        current_app.logger.error(f"[PERFORMANCE] Error logging metric: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
