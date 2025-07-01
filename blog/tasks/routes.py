# blog/tasks/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
import time # Перенесен в начало файла из функций
import traceback # Добавлен traceback
# from datetime import datetime, date # Закомментируем, если не используется напрямую

# === НЕОБХОДИМЫЕ ИМПОРТЫ ИЗ blog.main.routes (НУЖНО БУДЕТ ТЩАТЕЛЬНО ПРОВЕРИТЬ И ДОПОЛНИТЬ) ===
from config import get # Предполагаем, что config.py в корне проекта
# from redmine import RedmineConnector, ... (и другие из redmine.py)
# from erp_oracle import connect_oracle, ... (и другие из erp_oracle.py)
from blog.utils.cache_manager import weekend_performance_optimizer, tasks_cache_optimizer # Добавлен tasks_cache_optimizer
from blog.models import User, Notifications, NotificationsAddNotes # Исправлены имена моделей
from redmine import RedmineConnector # Правильный путь импорта
from erp_oracle import connect_oracle, get_user_erp_password, db_host, db_port, db_service_name, db_user_name, db_password # Правильный путь импорта
from config import get # Для доступа к config.ini
# Используем logger через current_app
import logging
logger = logging.getLogger(__name__)
# ... другие модели, формы, утилиты, которые понадобятся для функций задач ...

# Импорты функций для работы с названиями из redmine.py
from redmine import (
    get_status_name_from_id,
    get_project_name_from_id,
    get_user_full_name_from_id,
    get_priority_name_from_id,
    get_property_name,
    get_connection,
    convert_datetime_msk_format,
    get_multiple_user_names,
    get_multiple_project_names,
    get_multiple_status_names,
    get_multiple_priority_names,
    db_redmine_host,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name
)

# Импорты для нового маршрута
from blog.tasks.utils import get_redmine_connector, get_user_assigned_tasks_paginated_optimized, task_to_dict, create_redmine_connector # Исправлен относительный импорт
from redminelib.exceptions import ResourceNotFoundError # Для обработки ошибок Redmine

def collect_ids_from_task_history(task):
    """Собирает все ID из истории изменений задачи для пакетной загрузки"""
    user_ids = set()
    project_ids = set()
    status_ids = set()
    priority_ids = set()

    # Добавляем ID из основной задачи
    if hasattr(task, 'assigned_to') and task.assigned_to:
        user_ids.add(task.assigned_to.id)
    if hasattr(task, 'author') and task.author:
        user_ids.add(task.author.id)
    if hasattr(task, 'status') and task.status:
        status_ids.add(task.status.id)
    if hasattr(task, 'priority') and task.priority:
        priority_ids.add(task.priority.id)
    if hasattr(task, 'project') and task.project:
        project_ids.add(task.project.id)

    # Собираем ID из истории изменений
    for journal in task.journals:
        for detail in journal.details:
            try:
                field_name = getattr(detail, 'name', '') or (detail.get('name') if isinstance(detail, dict) else '')
                old_value = getattr(detail, 'old_value', None)
                new_value = getattr(detail, 'new_value', None)
                if old_value is None and isinstance(detail, dict):
                    old_value = detail.get('old_value')
                if new_value is None and isinstance(detail, dict):
                    new_value = detail.get('new_value')
            except Exception as collect_err:
                current_app.logger.debug(f"[collect_ids_from_task_history] Ошибка разбора detail: {collect_err}")
                continue

            if field_name == 'assigned_to_id':
                if old_value and str(old_value).isdigit():
                    user_ids.add(int(old_value))
                if new_value and str(new_value).isdigit():
                    user_ids.add(int(new_value))

            elif field_name == 'project_id':
                if old_value and str(old_value).isdigit():
                    project_ids.add(int(old_value))
                if new_value and str(new_value).isdigit():
                    project_ids.add(int(new_value))

            elif field_name == 'status_id':
                if old_value and str(old_value).isdigit():
                    status_ids.add(int(old_value))
                if new_value and str(new_value).isdigit():
                    status_ids.add(int(new_value))

            elif field_name == 'priority_id':
                if old_value and str(old_value).isdigit():
                    priority_ids.add(int(old_value))
                if new_value and str(new_value).isdigit():
                    priority_ids.add(int(new_value))

    return {
        'user_ids': list(user_ids),
        'project_ids': list(project_ids),
        'status_ids': list(status_ids),
        'priority_ids': list(priority_ids)
    }

def format_boolean_field(value, field_name):
    """Форматирование булевых полей для шаблона"""
    # Приводим value к строке для унифицированной проверки
    str_value = str(value).strip().lower() if value is not None else ''

    truthy_values = {'1', 'true', 'yes', 'да'}
    falsy_values = {'0', 'false', 'no', 'нет', ''}

    if field_name == 'easy_helpdesk_need_reaction':
        # Для этого поля значение '1' означает Да, любое другое — Нет
        return 'Да' if str_value == '1' else 'Нет'
    elif field_name == '16':
        # Поле '16' (кастом Redmine) хранит '0' как Нет, всё остальное как Да
        return 'Нет' if str_value in falsy_values else 'Да'
    else:
        # Универсальная логика для прочих boolean-полей
        return 'Да' if str_value in truthy_values else 'Нет'

# Создаем Blueprint 'tasks'
# url_prefix='/tasks' означает, что все маршруты здесь будут начинаться с /tasks
# Например, бывший /my-tasks станет /tasks/my-tasks (или /tasks/ если маршрут в Blueprint будет '/')
tasks_bp = Blueprint('tasks', __name__, template_folder='templates')
# template_folder='templates' - ищем в blog/templates

# Константы
MY_TASKS_PAGE_ENDPOINT = ".my_tasks_page"

# ===== МОДУЛЬ "МОИ ЗАДАЧИ" (перенесено из main) =====


@tasks_bp.route("/my-tasks", methods=["GET"])
@login_required
@weekend_performance_optimizer
def my_tasks_page():
    """Страница 'Мои задачи' для пользователей Redmine с оптимизацией производительности"""
    if not current_user.is_redmine_user:
        flash("У вас нет доступа к модулю 'Мои задачи'", "warning")
        return redirect(url_for("main.home"))

    # Передаем переменную count_notifications для совместимости с layout.html
    count_notifications = 0  # Значение по умолчанию

    # Генерируем cache_buster для принудительного обновления кэша
    import time
    cache_buster = str(int(time.time()))

    return render_template("my_tasks.html", title="Мои задачи", count_notifications=count_notifications,
                         cache_buster=cache_buster)

@tasks_bp.route("/my-tasks/<int:task_id>", methods=["GET"])
@login_required
@weekend_performance_optimizer
def task_detail(task_id):
    """Оптимизированная версия страницы деталей задачи"""
    import time
    start_time = time.time()
    current_app.logger.info(f"🚀 [PERFORMANCE] Загрузка задачи {task_id} - начало")

    if not current_user.is_redmine_user:
        flash("У вас нет доступа к этой функциональности.", "warning")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

    try:
        # Получаем коннектор Redmine (без изменений)
        redmine_conn_obj = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_conn_obj or not hasattr(redmine_conn_obj, 'redmine'):
            flash("Не удалось подключиться к Redmine.", "error")
            return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

        # Получаем детали задачи (без изменений)
        task = redmine_conn_obj.redmine.issue.get(
            task_id,
            include=['status', 'priority', 'project', 'tracker', 'author', 'assigned_to', 'journals', 'done_ratio', 'attachments', 'relations', 'watchers', 'changesets']
        )

        # 🔧 Приводим old_value/new_value к строкам для безопасности шаблона
        try:
            for j in getattr(task, 'journals', []):
                for d in getattr(j, 'details', []):
                    if hasattr(d, 'old_value') and d.old_value is not None:
                        d.old_value = str(d.old_value)
                    if hasattr(d, 'new_value') and d.new_value is not None:
                        d.new_value = str(d.new_value)
        except Exception as journal_cast_err:
            current_app.logger.debug(f"[task_detail] Ошибка приведения типов journal details: {journal_cast_err}")

        # ✅ НОВОЕ: Собираем все ID для пакетной загрузки
        ids_data = collect_ids_from_task_history(task)
        current_app.logger.info(f"🔍 [PERFORMANCE] Собрано ID: users={len(ids_data['user_ids'])}, statuses={len(ids_data['status_ids'])}, projects={len(ids_data['project_ids'])}, priorities={len(ids_data['priority_ids'])}")

        # ✅ НОВОЕ: Создаем ОДНО соединение для всех запросов
        connection = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)

        if not connection:
            current_app.logger.error("❌ [PERFORMANCE] Не удалось создать соединение с MySQL")
            flash("Ошибка соединения с базой данных.", "error")
            return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

        # ✅ НОВОЕ: Пакетная загрузка всех данных
        try:
            user_names = get_multiple_user_names(connection, ids_data['user_ids'])
            project_names = get_multiple_project_names(connection, ids_data['project_ids'])
            status_names = get_multiple_status_names(connection, ids_data['status_ids'])
            priority_names = get_multiple_priority_names(connection, ids_data['priority_ids'])

            current_app.logger.info(f"✅ [PERFORMANCE] Загружено данных: users={len(user_names)}, projects={len(project_names)}, statuses={len(status_names)}, priorities={len(priority_names)}")

        finally:
            # ✅ ВАЖНО: Закрываем соединение
            connection.close()
            current_app.logger.info("🔒 [PERFORMANCE] Соединение с MySQL закрыто")

        # Получаем все статусы для создания словаря ID -> название (без изменений)
        status_mapping = {}
        try:
            redmine_statuses = redmine_conn_obj.redmine.issue_status.all()
            for status in redmine_statuses:
                status_mapping[status.id] = status.name
            current_app.logger.info(f"✅ Получено {len(status_mapping)} статусов для преобразования")
        except Exception as status_error:
            current_app.logger.error(f"❌ Не удалось получить статусы: {status_error}")
            status_mapping = {}

        # Время выполнения
        execution_time = time.time() - start_time
        current_app.logger.info(f"🚀 [PERFORMANCE] Задача {task_id} загружена за {execution_time:.3f}с")

        # ✅ НОВОЕ: Оптимизированная функция описания изменений без дополнительных подключений к БД
        def get_property_name_fast(property_name, prop_key, old_value, value):
            def _val_to_text(val_dict, v):
                if v is None:
                    return 'None'
                if isinstance(v, str) and v.isdigit():
                    v_int = int(v)
                elif isinstance(v, int):
                    v_int = v
                else:
                    return v
                return val_dict.get(v_int, v)

            if prop_key == 'project_id':
                from_txt = _val_to_text(project_names, old_value)
                to_txt = _val_to_text(project_names, value)
                return f"Параметр&nbsp;<b>Проект</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif prop_key == 'assigned_to_id':
                from_txt = _val_to_text(user_names, old_value)
                to_txt = _val_to_text(user_names, value)
                return f"Параметр&nbsp;<b>Исполнитель</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif prop_key == 'status_id':
                from_txt = _val_to_text(status_names, old_value)
                to_txt = _val_to_text(status_names, value)
                return f"Параметр&nbsp;<b>Статус</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif prop_key == 'priority_id':
                from_txt = _val_to_text(priority_names, old_value)
                to_txt = _val_to_text(priority_names, value)
                return f"Параметр&nbsp;<b>Приоритет</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif prop_key == 'subject':
                return f"Параметр&nbsp;<b>Тема</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_value}</b>&nbsp;на&nbsp;<b>{value}</b>"
            elif prop_key == 'easy_helpdesk_need_reaction':
                from_txt = 'Да' if str(old_value) == '1' else 'Нет'
                to_txt = 'Да' if str(value) == '1' else 'Нет'
                return f"Параметр&nbsp;<b>Нужна&nbsp;реакция?</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif prop_key == 'done_ratio':
                return f"Параметр&nbsp;<b>Готовность</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_value}%</b>&nbsp;на&nbsp;<b>{value}%</b>"
            elif prop_key == '16':
                from_txt = 'Да' if old_value and str(old_value) != '0' else 'Нет'
                to_txt = 'Да' if value and str(value) != '0' else 'Нет'
                return f"Параметр&nbsp;<b>Что&nbsp;нового</b>&nbsp;изменился&nbsp;c&nbsp;<b>{from_txt}</b>&nbsp;на&nbsp;<b>{to_txt}</b>"
            elif property_name == 'attachment':
                return f"Файл&nbsp;<b>{value}</b>&nbsp;добавлен"
            elif property_name == 'relation' and prop_key == 'relates':
                return f"Задача&nbsp;связана&nbsp;с&nbsp;задачей&nbsp;<b>#{value}</b>"
            return None

        # ✅ НОВОЕ: Передаем словари данных вместо функций и оптимизированный helper
        return render_template("task_detail.html",
                             task=task,
                             title=f"Задача #{task.id}",
                             count_notifications=0,
                             status_mapping=status_mapping,
                             # ✅ Новые данные для оптимизированного шаблона
                             user_names=user_names,
                             project_names=project_names,
                             status_names=status_names,
                             priority_names=priority_names,
                             # ✅ Оставляем только helper для форматирования
                             convert_datetime_msk_format=convert_datetime_msk_format,
                             format_boolean_field=format_boolean_field,
                             get_property_name=get_property_name_fast)

    except ResourceNotFoundError:
        current_app.logger.warning(f"Задача с ID {task_id} не найдена в Redmine")
        flash(f"Задача #{task_id} не найдена.", "error")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))
    except Exception as e:
        import traceback
        current_app.logger.error(f"[task_detail] Ошибка при получении задачи {task_id}: {e}. Trace: {traceback.format_exc()}")
        flash("Произошла ошибка при загрузке данных задачи.", "error")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

# ===== API для работы с задачами =====

@tasks_bp.route("/get-my-tasks-paginated", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_my_tasks_paginated_api():
    """API для получения задач с пагинацией (совместимый URL)"""
    current_app.logger.info(f"Запрос /tasks/get-my-tasks-paginated для {current_user.username} с параметрами: {request.args}")

    # Замеряем время выполнения запроса
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            current_app.logger.warning(f"Пользователь {current_user.username} не является пользователем Redmine (get_my_tasks_paginated_api).")
            return jsonify({"error": "Доступ запрещен, вы не являетесь пользователем Redmine"}), 403

        draw = request.args.get('draw', 1, type=int)
        page = request.args.get("start", 0, type=int) // request.args.get("length", 25, type=int) + 1
        per_page = request.args.get("length", 25, type=int)

        search_value = request.args.get("search[value]", "", type=str).strip()
        current_app.logger.info(f"🔍 ПОИСК API: получен search_value='{search_value}' от пользователя {current_user.username}")

        order_column_index = request.args.get('order[0][column]', 0, type=int)
        order_column_name_dt = request.args.get(f'columns[{order_column_index}][data]', 'updated_on', type=str)
        order_direction = request.args.get('order[0][dir]', 'desc', type=str)

        # Сопоставление имен столбцов DataTables с полями Redmine
        column_mapping = {
            'id': 'id',
            'project': 'project.name',
            'tracker': 'tracker.name',
            'status': 'status.name',
            'priority': 'priority.name',
            'subject': 'subject',
            'assigned_to': 'assigned_to.name',
            'easy_email_to': 'easy_email_to',
            'updated_on': 'updated_on',
            'created_on': 'created_on',
            'due_date': 'due_date'
        }
        sort_column_redmine = column_mapping.get(order_column_name_dt, 'updated_on')

        status_ids = request.args.getlist("status_id[]")
        project_ids = request.args.getlist("project_id[]")
        priority_ids = request.args.getlist("priority_id[]")

        # ОПТИМИЗАЦИЯ: Используем пароль из локальной базы данных вместо обращения к Oracle
        # Пароль пользователя хранится в модели User
        if not current_user.password:
            current_app.logger.error(f"Не найден пароль в локальной БД для пользователя {current_user.username}")
            return jsonify({"draw": draw, "error": "Ошибка аутентификации: не найден пароль пользователя", "data": [], "recordsTotal": 0, "recordsFiltered": 0}), 401

        # Создаем коннектор Redmine с использованием пароля из локальной БД
        redmine_connector_instance = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector_instance or not hasattr(redmine_connector_instance, 'redmine') or not redmine_connector_instance.redmine:
            current_app.logger.error(f"Не удалось создать/инициализировать Redmine коннектор для {current_user.username} через create_redmine_connector в get_my_tasks_paginated_api.")
            return jsonify({"draw": draw, "error": "Не удалось подключиться к Redmine или инициализировать API", "data": [], "recordsTotal": 0, "recordsFiltered": 0}), 500

        # Используем ID из SQLite вместо Redmine API (для производительности и корректности)
        redmine_user_id = current_user.id_redmine_user
        current_app.logger.info(f"🔍 [API] Используем redmine_user_id из SQLite: {redmine_user_id} для пользователя {current_user.username}")

        # Получаем параметр force_load для принудительной загрузки данных при первом запросе
        force_load = request.args.get('force_load', '0') == '1'
        current_app.logger.info(f"🔍 [API] Параметр force_load: {force_load}")

        issues_list, total_count = get_user_assigned_tasks_paginated_optimized(
            redmine_connector_instance,
            redmine_user_id,
            page=page,
            per_page=per_page,
            search_term=search_value,
            sort_column=sort_column_redmine,
            sort_direction=order_direction,
            status_ids=status_ids,
            project_ids=project_ids,
            priority_ids=priority_ids,
            force_load=force_load
        )

        # Преобразуем задачи в JSON
        tasks_data = [task_to_dict(issue) for issue in issues_list]

        # Определяем start_time для расчета времени выполнения
        execution_time = time.time() - start_time
        current_app.logger.info(
            f"Запрос /tasks/get-my-tasks-paginated для {current_user.username} выполнен за {execution_time:.4f}с. Найдено задач: {len(tasks_data)}, всего: {total_count}"
        )

        return jsonify({
            "draw": draw,
            "recordsTotal": total_count,
            "recordsFiltered": total_count,
            "data": tasks_data
        })

    except Exception as e:
        current_app.logger.error(f"Критическая ошибка в /tasks/get-my-tasks-paginated для {current_user.username}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "draw": request.args.get('draw', 1, type=int),
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "data": [],
            "recordsTotal": 0,
            "recordsFiltered": 0
        }), 500

@tasks_bp.route("/get-my-tasks-statistics-optimized", methods=["GET"])
@login_required
def get_my_tasks_statistics_optimized():
    """API для получения статистики задач"""
    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 403

        # ОПТИМИЗАЦИЯ: Используем пароль из локальной базы данных вместо обращения к Oracle
        if not current_user.password:
            current_app.logger.error(f"Не найден пароль в локальной БД для пользователя {current_user.username}")
            return jsonify({
                "error": "Ошибка аутентификации: не найден пароль пользователя",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 401

        # Создаем коннектор Redmine с использованием пароля из локальной БД
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector or not hasattr(redmine_connector, 'redmine'):
            return jsonify({
                "error": "Не удалось создать коннектор Redmine",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500

        # Получаем ID пользователя Redmine из SQLite (НЕ из Redmine API!)
        redmine_user_id = current_user.id_redmine_user
        current_app.logger.info(f"🔍 [STATISTICS] Текущий redmine_user_id из SQLite: {redmine_user_id} (current_user.id: {current_user.id})")

        # ИСПРАВЛЕНИЕ: Используем ПРЯМЫЕ SQL-запросы для всей статистики (избегаем LIMIT 1000)
        current_app.logger.info(f"🗄️ [STATISTICS] Запуск ИСПРАВЛЕННОЙ статистики через прямые SQL-запросы для пользователя {redmine_user_id}")

        # Получаем подключение к MySQL Redmine для точного подсчета ВСЕХ задач
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if not mysql_conn:
            current_app.logger.error(f"❌ [STATISTICS] Не удалось подключиться к MySQL для подсчета статистики")
            return jsonify({
                "error": "Ошибка подключения к базе данных статистики",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500

        cursor = mysql_conn.cursor()

        total_tasks = 0
        new_tasks = 0
        in_progress_tasks = 0
        closed_tasks = 0
        actually_closed_tasks = 0
        debug_status_counts = {}

        # Структуры для группировки статусов
        open_statuses_breakdown = []
        completed_statuses_breakdown = []
        in_progress_statuses_breakdown = []
        localized_status_names = {}

        try:
            # 1. ОБЩЕЕ количество задач (БЕЗ ЛИМИТОВ!)
            sql_total = """
                SELECT COUNT(*) as total_count
                FROM issues i
                WHERE i.assigned_to_id = %s
            """
            current_app.logger.info(f"🗄️ [STATISTICS] SQL запрос общего количества задач для пользователя {redmine_user_id}")
            cursor.execute(sql_total, (redmine_user_id,))
            result = cursor.fetchone()
            total_tasks = result['total_count'] if result else 0
            current_app.logger.info(f"📊 [STATISTICS] ОБЩЕЕ количество задач (SQL): {total_tasks}")

            # 2. Получаем локализованные названия статусов из u_statuses
            sql_localized_statuses = """
                SELECT id, name
                FROM u_statuses
            """
            cursor.execute(sql_localized_statuses)
            localized_rows = cursor.fetchall()
            for row in localized_rows:
                localized_status_names[row['id']] = row['name']
            current_app.logger.info(f"📊 [STATISTICS] Загружено {len(localized_status_names)} локализованных названий статусов")

            # 3. ЗАВЕРШЁННЫЕ задачи (is_closed=1) с локализованными названиями
            sql_completed_detailed = """
                SELECT s.name as status_name_en, s.id as status_id, COUNT(i.id) as task_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s AND s.is_closed = 1
                GROUP BY s.id, s.name
                ORDER BY task_count DESC
            """
            cursor.execute(sql_completed_detailed, (redmine_user_id,))
            completed_statuses_raw = cursor.fetchall()

            current_app.logger.info(f"📊 [STATISTICS] ЗАВЕРШЁННЫЕ статусы (is_closed=1):")
            for status_row in completed_statuses_raw:
                status_name_en = status_row['status_name_en']
                status_id = status_row['status_id']
                status_count = status_row['task_count']

                # Используем локализованное название если доступно
                status_name_ru = localized_status_names.get(status_id, status_name_en)

                closed_tasks += status_count
                debug_status_counts[status_name_ru] = status_count
                completed_statuses_breakdown.append({
                    'name': status_name_ru,
                    'count': status_count,
                    'id': status_id
                })

                current_app.logger.info(f"   📌 {status_name_ru} (EN: {status_name_en}, ID: {status_id}) = {status_count} задач")

            actually_closed_tasks = closed_tasks

            # 4. ОТКРЫТЫЕ задачи (is_closed=0) с детализацией и локализацией
            sql_open_detailed = """
                SELECT s.name as status_name_en, s.id as status_id, COUNT(i.id) as task_count
                FROM issues i
                INNER JOIN issue_statuses s ON i.status_id = s.id
                WHERE i.assigned_to_id = %s AND s.is_closed = 0
                GROUP BY s.id, s.name
                ORDER BY task_count DESC
            """
            cursor.execute(sql_open_detailed, (redmine_user_id,))
            open_statuses_raw = cursor.fetchall()

            current_app.logger.info(f"📊 [STATISTICS] ОТКРЫТЫЕ статусы (is_closed=0):")
            for status_row in open_statuses_raw:
                status_name_en = status_row['status_name_en']
                status_id = status_row['status_id']
                status_count = status_row['task_count']

                # Используем локализованное название если доступно
                status_name_ru = localized_status_names.get(status_id, status_name_en)
                debug_status_counts[status_name_ru] = status_count

                current_app.logger.info(f"   📌 {status_name_ru} (EN: {status_name_en}, ID: {status_id}) = {status_count} задач")

                # НОВАЯ классификация статусов согласно требованиям пользователя
                status_name_lower = status_name_ru.lower().strip()
                status_name_en_lower = status_name_en.lower().strip()

                # ОТКРЫТЫЕ ЗАДАЧИ: Новая и Открыта
                if (status_name_lower in ['новая', 'новый', 'новое'] or 'нов' in status_name_lower or
                    status_name_en_lower in ['new'] or 'new' in status_name_en_lower or
                    status_name_lower in ['открыта', 'открыт', 'открыто'] or 'открыт' in status_name_lower or
                    status_name_en_lower in ['open'] or 'open' in status_name_en_lower):

                    new_tasks += status_count
                    open_statuses_breakdown.append({
                        'name': status_name_ru,
                        'count': status_count,
                        'id': status_id
                    })
                    current_app.logger.info(f"   ✅ Отнесено к ОТКРЫТЫМ: +{status_count}")

                # В РАБОТЕ: все остальные статусы согласно требованиям
                else:
                    in_progress_tasks += status_count
                    in_progress_statuses_breakdown.append({
                        'name': status_name_ru,
                        'count': status_count,
                        'id': status_id
                    })
                    current_app.logger.info(f"   ✅ Отнесено к В РАБОТЕ: +{status_count}")

            current_app.logger.info(f"🎯 [STATISTICS] НОВАЯ ИТОГОВАЯ СТАТИСТИКА:")
            current_app.logger.info(f"   📊 Всего: {total_tasks}")
            current_app.logger.info(f"   📊 Открытые: {new_tasks}")
            current_app.logger.info(f"   📊 В работе: {in_progress_tasks}")
            current_app.logger.info(f"   📊 Завершённые: {closed_tasks}")
            current_app.logger.info(f"📈 [STATISTICS] ПОЛНАЯ РАЗБИВКА ПО СТАТУСАМ: {debug_status_counts}")

        except Exception as e_sql:
            current_app.logger.error(f"❌ [STATISTICS] Ошибка SQL-запросов статистики: {e_sql}")
            cursor.close()
            mysql_conn.close()
            return jsonify({
                "error": f"Ошибка при получении статистики: {str(e_sql)}",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500
        finally:
            cursor.close()
            mysql_conn.close()

        # Создаем дополнительную статистику для модального окна
        additional_stats = {
            "avg_completion_time": "Не определено",
            "most_active_project": "Не определено",
            "completion_rate": 0,
            "actually_closed_tasks": actually_closed_tasks  # Добавляем реальные закрытые задачи
        }

        # Вычисляем процент завершения
        if total_tasks > 0:
            additional_stats["completion_rate"] = round((closed_tasks / total_tasks) * 100, 1)

        return jsonify({
            "success": True,
            "total_tasks": total_tasks,
            "open_tasks": new_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": closed_tasks,
            "closed_tasks": closed_tasks,  # Для обратной совместимости
            # Данные для JavaScript обработки
            "status_counts": debug_status_counts,
            "detailed_breakdown": {
                "open_statuses": [item['name'] for item in open_statuses_breakdown],
                "in_progress_statuses": [item['name'] for item in in_progress_statuses_breakdown],
                "completed_statuses": [item['name'] for item in completed_statuses_breakdown]
            },
            "statistics": {
                "debug_status_counts": debug_status_counts,
                "additional_stats": additional_stats,
                "breakdown_details": {
                    "open": open_statuses_breakdown,
                    "in_progress": in_progress_statuses_breakdown,
                    "completed": completed_statuses_breakdown
                },
                "focused_data": {
                    "total": {
                        "additional_stats": additional_stats,
                        "status_breakdown": debug_status_counts
                    },
                    "open": {
                        "statuses": open_statuses_breakdown,
                        "filter_description": "Новые и открытые задачи"
                    },
                    "in_progress": {
                        "statuses": in_progress_statuses_breakdown,
                        "filter_description": "В процессе выполнения, на согласовании, тестировании"
                    },
                    "completed": {
                        "statuses": completed_statuses_breakdown,
                        "filter_description": "Фактически закрытые задачи"
                    }
                }
            }
        })

    except Exception as e:
        logger.error(f"Ошибка в get_my_tasks_statistics_optimized: {e}")
        return jsonify({
            "error": str(e),
            "total_tasks": 0,
            "new_tasks": 0,
            "in_progress_tasks": 0,
            "closed_tasks": 0
        }), 500

@tasks_bp.route("/get-my-tasks-filters-optimized", methods=["GET"])
@login_required
def get_my_tasks_filters_optimized():
    """ОПТИМИЗИРОВАННЫЙ API для получения фильтров задач с использованием прямых SQL запросов"""
    start_time = time.time()

    logger.info("🚀 [PERFORMANCE] Запуск ОПТИМИЗИРОВАННОГО API фильтров...")

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 403

        # Получаем подключение к MySQL Redmine (ИСПРАВЛЕНО!)
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if not mysql_conn:
            return jsonify({
                "error": "Ошибка подключения к MySQL Redmine",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 500

        cursor = mysql_conn.cursor()
        statuses = []
        projects = []
        priorities = []

        try:
            # 1. БЫСТРЫЙ запрос статусов из u_statuses (локализованные)
            status_start = time.time()
            cursor.execute("""
                SELECT DISTINCT id, name
                FROM u_statuses
                ORDER BY id, name
            """)
            statuses = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
            status_time = time.time() - status_start
            logger.info(f"✅ [PERFORMANCE] Статусы (локализованные) загружены за {status_time:.3f}с ({len(statuses)} записей)")

            # 2. БЫСТРЫЙ запрос проектов (ПРОСТОЙ СПИСОК, без иерархии для скорости)
            projects_start = time.time()
            cursor.execute("""
                SELECT id, name, parent_id
                FROM projects
                WHERE status = 1
                ORDER BY name
            """)
            projects_raw = cursor.fetchall()
            projects = []
            for row in projects_raw:
                projects.append({
                    "id": row["id"],
                    "name": row["name"],
                    "original_name": row["name"],
                    "parent_id": row["parent_id"],
                    "level": 0,
                    "has_children": False,
                    "is_parent": False
                })

            projects_time = time.time() - projects_start
            logger.info(f"✅ [PERFORMANCE] Проекты (простой список) загружены за {projects_time:.3f}с ({len(projects)} записей)")

            # 3. БЫСТРЫЙ запрос приоритетов на кириллице из таблицы u_Priority
            priorities_start = time.time()

            # Получаем приоритеты из таблицы u_Priority, где id совпадает с id из таблицы enumerations
            cursor.execute("""
                SELECT e.id, up.name
                FROM enumerations e
                JOIN u_Priority up ON e.id = up.id
                WHERE e.type = 'IssuePriority'
                AND e.active = 1
                ORDER BY e.position, up.name
            """)
            priorities = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

            # Если нет результатов (например, нет соответствия в u_Priority), используем значения из enumerations
            if not priorities:
                logger.warning("⚠️ [PERFORMANCE] Нет данных в u_Priority, возвращаемся к enumerations")
                cursor.execute("""
                    SELECT id, name
                    FROM enumerations
                    WHERE type = 'IssuePriority'
                    AND active = 1
                    ORDER BY position, name
                """)
                priorities = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

            priorities_time = time.time() - priorities_start
            logger.info(f"✅ [PERFORMANCE] Приоритеты (локализованные) загружены за {priorities_time:.3f}с ({len(priorities)} записей)")

        except Exception as sql_error:
            logger.error(f"❌ [PERFORMANCE] Ошибка MySQL запроса: {sql_error}")
            raise sql_error
        finally:
            cursor.close()
            mysql_conn.close()

        total_time = time.time() - start_time
        logger.info(f"🎯 [PERFORMANCE] ОПТИМИЗИРОВАННЫЙ API завершен за {total_time:.3f}с (статусы: {len(statuses)}, проекты: {len(projects)}, приоритеты: {len(priorities)})")

        return jsonify({
            "success": True,
            "statuses": statuses,
            "projects": projects,
            "priorities": priorities,
            "performance": {
                "total_time": round(total_time, 3),
                "status_time": round(status_time, 3),
                "projects_time": round(projects_time, 3),
                "priorities_time": round(priorities_time, 3)
            }
        })

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ [PERFORMANCE] Ошибка в оптимизированном API фильтров за {total_time:.3f}с: {e}")
        import traceback
        logger.error(f"❌ [PERFORMANCE] Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "statuses": [],
            "projects": [],
            "priorities": []
        }), 500

@tasks_bp.route("/get-my-tasks-filters-direct-api", methods=["GET"])
@login_required
def get_my_tasks_filters_direct_api():
    """СТАРЫЙ API для получения фильтров задач (для совместимости)"""
    logger.info("⚠️ ВНИМАНИЕ: Используется СТАРЫЙ API фильтров! Рекомендуется переход на /get-my-tasks-filters-optimized")
    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 403

        # ОПТИМИЗАЦИЯ: Используем пароль из локальной базы данных вместо обращения к Oracle
        if not current_user.password:
            logger.error(f"Не найден пароль в локальной БД для пользователя {current_user.username}")
            return jsonify({
                "error": "Ошибка аутентификации: не найден пароль пользователя",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 401

        # Создаем коннектор Redmine с использованием пароля из локальной БД
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector or not hasattr(redmine_connector, 'redmine'):
            return jsonify({
                "error": "Не удалось создать коннектор Redmine",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 500

        # Получаем фильтры из Redmine
        statuses = []
        projects = []
        priorities = []

        try:
            # Получаем статусы
            redmine_statuses = redmine_connector.redmine.issue_status.all()
            statuses = [{"id": status.id, "name": status.name} for status in redmine_statuses]
        except Exception as e:
            logger.error(f"❌ Ошибка получения статусов: {e}")
            statuses = []

        try:
            # Получаем проекты с базовой обработкой
            redmine_projects = redmine_connector.redmine.project.all()
            projects = [{"id": project.id, "name": project.name, "original_name": project.name, "parent_id": None, "level": 0, "has_children": False, "is_parent": False} for project in redmine_projects]
        except Exception as e:
            logger.error(f"❌ Ошибка получения проектов: {e}")
            projects = []

        try:
            # Получаем приоритеты
            redmine_priorities = redmine_connector.redmine.enumeration.filter(resource='issue_priorities')
            priorities = [{"id": priority.id, "name": priority.name} for priority in redmine_priorities]
        except Exception as e:
            logger.error(f"❌ Ошибка получения приоритетов: {e}")
            priorities = []

        return jsonify({
            "success": True,
            "statuses": statuses,
            "projects": projects,
            "priorities": priorities
        })

    except Exception as e:
        logger.error(f"Ошибка в get_my_tasks_filters_direct_api: {e}")
        return jsonify({
            "error": str(e),
            "statuses": [],
            "projects": [],
            "priorities": []
        }), 500

# Старый API (для совместимости)
@tasks_bp.route("/api/get-paginated", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_my_tasks_paginated_api_old():
    """Старый API для получения задач (для совместимости)"""
    return get_my_tasks_paginated_api()

# ===== МАРШРУТЫ ДЛЯ ТЕСТОВЫХ ФАЙЛОВ =====

@tasks_bp.route("/test-statistics-debug")
def test_statistics_debug():
    """Отладочная страница для тестирования API статистики"""
    try:
        with open('test_statistics_debug.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_statistics_debug.html не найден", 404

@tasks_bp.route("/test-statistics-fix")
def test_statistics_fix():
    """Тестовая страница для проверки исправленной статистики"""
    try:
        with open('test_statistics_fix.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_statistics_fix.html не найден", 404

@tasks_bp.route("/test-closed-tasks-api")
def test_closed_tasks_api():
    """Тестовая страница для отладки проблемы с закрытыми задачами"""
    try:
        with open('test_closed_tasks_api.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_closed_tasks_api.html не найден", 404

@tasks_bp.route("/test-statistics-direct")
def test_statistics_direct():
    """Тестовая страница для прямой отладки API статистики"""
    try:
        with open('test_statistics_direct.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_statistics_direct.html не найден", 404

@tasks_bp.route("/test-search-debug")
def test_search_debug():
    """Тестовая страница для отладки поиска по описанию задач"""
    try:
        with open('test_search_debug.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_search_debug.html не найден", 404

@tasks_bp.route("/test-auth-status")
def test_auth_status():
    """Диагностическая страница для проверки состояния авторизации"""
    try:
        with open('test_auth_status.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_auth_status.html не найден", 404

@tasks_bp.route("/test-search-enhanced")
def test_search_enhanced():
    """Улучшенная тестовая страница для отладки поиска с двумя API"""
    try:
        with open('test_search_enhanced.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return "Файл test_search_enhanced.html не найден", 404

def get_my_tasks_statuses_localized():
    """API для получения локализованных статусов задач из таблицы u_statuses

    Внимание: Не проверяет авторизацию! Должен вызываться только из авторизованного контекста.
    """
    start_time = time.time()
    logger.info("📋 [STATUSES] Запуск API для получения локализованных статусов...")

    try:
        # Подключение к MySQL Redmine
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if not mysql_conn:
            return []

        cursor = mysql_conn.cursor()
        statuses = []

        try:
            # Получаем локализованные статусы из таблицы u_statuses
            status_start = time.time()
            cursor.execute("""
                SELECT DISTINCT id, name
                FROM u_statuses
                ORDER BY id, name
            """)
            statuses = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
            status_time = time.time() - status_start
            logger.info(f"✅ [STATUSES] Локализованные статусы загружены за {status_time:.3f}с ({len(statuses)} записей)")

        finally:
            cursor.close()
            mysql_conn.close()

        total_time = time.time() - start_time
        logger.info(f"🎯 [STATUSES] API статусов завершен за {total_time:.3f}с")

        return statuses

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ [STATUSES] Ошибка в API статусов за {total_time:.3f}с: {e}")
        logger.error(f"❌ [STATUSES] Traceback: {traceback.format_exc()}")
        return []

def get_my_tasks_priorities():
    """API для получения приоритетов задач

    Внимание: Не проверяет авторизацию! Должен вызываться только из авторизованного контекста.
    """
    start_time = time.time()
    logger.info("⚡ [PRIORITIES] Запуск API для получения приоритетов...")

    try:
        # Подключение к MySQL Redmine
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if not mysql_conn:
            return []

        cursor = mysql_conn.cursor()
        priorities = []

        try:
            # Получаем приоритеты из таблицы u_Priority, где id совпадает с id из таблицы enumerations
            priorities_start = time.time()
            cursor.execute("""
                SELECT e.id, up.name
                FROM enumerations e
                JOIN u_Priority up ON e.id = up.id
                WHERE e.type = 'IssuePriority'
                AND e.active = 1
                ORDER BY e.position, up.name
            """)
            priorities = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

            # Если нет результатов (например, нет соответствия в u_Priority), используем значения из enumerations
            if not priorities:
                logger.warning("⚠️ [PRIORITIES] Нет данных в u_Priority, возвращаемся к enumerations")
                cursor.execute("""
                    SELECT id, name
                    FROM enumerations
                    WHERE type = 'IssuePriority'
                    AND active = 1
                    ORDER BY position, name
                """)
                priorities = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

            priorities_time = time.time() - priorities_start
            logger.info(f"✅ [PRIORITIES] Приоритеты загружены за {priorities_time:.3f}с ({len(priorities)} записей)")

        finally:
            cursor.close()
            mysql_conn.close()

        total_time = time.time() - start_time
        logger.info(f"🎯 [PRIORITIES] API приоритетов завершен за {total_time:.3f}с")

        return priorities

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ [PRIORITIES] Ошибка в API приоритетов за {total_time:.3f}с: {e}")
        logger.error(f"❌ [PRIORITIES] Traceback: {traceback.format_exc()}")
        return []

def get_my_tasks_projects_hierarchical():
    """API для получения ТОЛЬКО иерархического дерева проектов из MySQL Redmine

    Внимание: Не проверяет авторизацию! Должен вызываться только из авторизованного контекста.
    """
    start_time = time.time()
    logger.info("🌳 [PROJECTS] Запуск API иерархического дерева проектов...")

    try:
        # Подключение к MySQL Redmine
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if not mysql_conn:
            return []

        cursor = mysql_conn.cursor()
        projects = []

        try:
            # Проекты с иерархией через Nested Set Model (lft/rgt) для MySQL
            projects_start = time.time()

            # Сначала проверим, есть ли поля lft и rgt в таблице projects
            try:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM information_schema.COLUMNS
                    WHERE table_schema = %s AND table_name = 'projects'
                    AND column_name IN ('lft', 'rgt')
                """, (db_redmine_name,))
                lft_rgt_result = cursor.fetchone()
                lft_rgt_count = lft_rgt_result["count"] if lft_rgt_result else 0

                if lft_rgt_count >= 2:
                    # Используем Nested Set Model (lft/rgt) для MySQL
                    logger.info("🌳 [PROJECTS] Используем MySQL Nested Set Model (lft/rgt поля)")
                    cursor.execute("""
                        SELECT p1.id, p1.name, p1.parent_id,
                               (COUNT(p2.id) - 1) as level,
                               CASE WHEN p1.lft + 1 < p1.rgt THEN 1 ELSE 0 END as has_children,
                               CASE WHEN p1.lft + 1 < p1.rgt THEN 1 ELSE 0 END as is_parent,
                               p1.lft, p1.rgt
                        FROM projects p1, projects p2
                        WHERE p1.lft BETWEEN p2.lft AND p2.rgt
                          AND p1.status = 1
                          AND p2.status = 1
                        GROUP BY p1.id, p1.name, p1.parent_id, p1.lft, p1.rgt
                        ORDER BY p1.lft
                    """)
                else:
                    # Fallback на рекурсивную иерархию для MySQL (с CTE)
                    logger.info("🌳 [PROJECTS] Fallback на MySQL рекурсивную иерархию")
                    cursor.execute("""
                        WITH RECURSIVE project_hierarchy AS (
                            -- Базовый случай: корневые проекты
                            SELECT id, name, parent_id, 0 as level,
                                   CASE WHEN EXISTS(SELECT 1 FROM projects c WHERE c.parent_id = p.id AND c.status = 1)
                                        THEN 1 ELSE 0 END as has_children,
                                   CASE WHEN EXISTS(SELECT 1 FROM projects c WHERE c.parent_id = p.id AND c.status = 1)
                                        THEN 1 ELSE 0 END as is_parent,
                                   CAST(name AS CHAR(1000)) as full_path
                            FROM projects p
                            WHERE parent_id IS NULL AND status = 1

                            UNION ALL

                            -- Рекурсивный случай: дочерние проекты
                            SELECT p.id, p.name, p.parent_id, ph.level + 1,
                                   CASE WHEN EXISTS(SELECT 1 FROM projects c WHERE c.parent_id = p.id AND c.status = 1)
                                        THEN 1 ELSE 0 END as has_children,
                                   CASE WHEN EXISTS(SELECT 1 FROM projects c WHERE c.parent_id = p.id AND c.status = 1)
                                        THEN 1 ELSE 0 END as is_parent,
                                   CONCAT(ph.full_path, ' > ', p.name) as full_path
                            FROM projects p
                            INNER JOIN project_hierarchy ph ON p.parent_id = ph.id
                            WHERE p.status = 1
                        )
                        SELECT id, name, parent_id, level, has_children, is_parent,
                               NULL as lft, NULL as rgt
                        FROM project_hierarchy
                        ORDER BY full_path
                    """)

                projects_raw = cursor.fetchall()
                projects = []

                for row in projects_raw:
                    project_data = {
                        "id": row["id"],
                        "name": row["name"],
                        "original_name": row["name"],
                        "parent_id": row["parent_id"],
                        "level": row["level"] if row["level"] is not None else 0,
                        "has_children": bool(row["has_children"]),
                        "is_parent": bool(row["is_parent"])
                    }

                    # Добавляем lft/rgt если доступны
                    if "lft" in row and "rgt" in row and row["lft"] is not None:
                        project_data["lft"] = row["lft"]
                        project_data["rgt"] = row["rgt"]

                    projects.append(project_data)

            except Exception as nested_error:
                logger.warning(f"⚠️ [PROJECTS] Ошибка иерархического запроса: {nested_error}")
                # Fallback на простой запрос проектов
                cursor.execute("""
                    SELECT id, name, parent_id
                    FROM projects
                    WHERE status = 1
                    ORDER BY name
                """)
                projects_raw = cursor.fetchall()
                projects = []
                for row in projects_raw:
                    projects.append({
                        "id": row["id"],
                        "name": row["name"],
                        "original_name": row["name"],
                        "parent_id": row["parent_id"],
                        "level": 0,
                        "has_children": False,
                        "is_parent": False
                    })

            projects_time = time.time() - projects_start
            logger.info(f"✅ [PROJECTS] Проекты загружены за {projects_time:.3f}с ({len(projects)} записей)")

        finally:
            cursor.close()
            mysql_conn.close()

        total_time = time.time() - start_time
        logger.info(f"🎯 [PROJECTS] API проектов завершен за {total_time:.3f}с")

        return projects

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ [PROJECTS] Ошибка в API проектов за {total_time:.3f}с: {e}")
        logger.error(f"❌ [PROJECTS] Traceback: {traceback.format_exc()}")
        return []

@tasks_bp.route("/get-my-tasks-filters-hierarchical", methods=["GET"])
@login_required
def get_my_tasks_filters_hierarchical():
    """КОМБИНИРОВАННЫЙ API для получения всех фильтров (правильная архитектура - разделение ответственности)

    Выполняет проверку авторизации один раз, затем вызывает прямые функции БД.
    """
    start_time = time.time()
    logger.info("🔄 [COMBINED] Запуск комбинированного API фильтров...")

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 403

        # Вызываем правильно разделенные функции (Single Responsibility Principle)
        logger.info("🔄 [COMBINED] Вызов функций с разделением ответственности...")

        # 1. Получаем статусы через внутреннюю функцию
        statuses = get_my_tasks_statuses_localized()
        logger.info(f"🔄 [COMBINED] Статусы: {len(statuses)}")

        # 2. Получаем приоритеты через внутреннюю функцию
        priorities = get_my_tasks_priorities()
        logger.info(f"🔄 [COMBINED] Приоритеты: {len(priorities)}")

        # 3. Получаем проекты через внутреннюю функцию
        projects = get_my_tasks_projects_hierarchical()
        logger.info(f"🔄 [COMBINED] Проекты: {len(projects)}")

        total_time = time.time() - start_time
        logger.info(f"🎯 [COMBINED] Оптимизированный комбинированный API завершен за {total_time:.3f}с (статусы: {len(statuses)}, проекты: {len(projects)}, приоритеты: {len(priorities)})")

        return jsonify({
            "success": True,
            "statuses": statuses,
            "projects": projects,
            "priorities": priorities,
            "hierarchical": True,
            "performance": {
                "total_time": round(total_time, 3),
                "architecture": "separated_responsibility",
                "optimization": "no_duplicate_auth_checks"
            }
        })

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ [COMBINED] Ошибка в комбинированном API за {total_time:.3f}с: {e}")
        logger.error(f"❌ [COMBINED] Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "statuses": [],
            "projects": [],
            "priorities": []
        }), 500

@tasks_bp.route("/debug-search-api", methods=["GET"])
@login_required
def debug_search_api():
    """Специальный API для отладки поиска по описанию"""
    current_app.logger.info(f"🔍 DEBUG SEARCH API: Запрос от {current_user.username}")

    # Замеряем время выполнения запроса
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({"error": "Доступ запрещен"}), 403

        search_term = request.args.get("q", "", type=str).strip()
        current_app.logger.info(f"🔍 DEBUG: Поисковый термин = '{search_term}'")

        if not search_term:
            return jsonify({"error": "Не указан поисковый термин (параметр q)"}), 400

        # ОПТИМИЗАЦИЯ: Используем пароль из локальной базы данных вместо обращения к Oracle
        if not current_user.password:
            current_app.logger.error(f"Не найден пароль в локальной БД для пользователя {current_user.username}")
            return jsonify({"error": "Ошибка аутентификации: не найден пароль пользователя"}), 401

        # Создаем коннектор Redmine с использованием пароля из локальной БД
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector or not hasattr(redmine_connector, 'redmine'):
            return jsonify({"error": "Не удалось создать коннектор Redmine"}), 500

        redmine_user_id = current_user.id_redmine_user
        current_app.logger.info(f"🔍 DEBUG: redmine_user_id = {redmine_user_id}")

        # Используем нашу функцию поиска
        issues_list, total_count = get_user_assigned_tasks_paginated_optimized(
            redmine_connector,
            redmine_user_id,
            page=1,
            per_page=10,
            search_term=search_term,
            sort_column='updated_on',
            sort_direction='desc'
        )

        current_app.logger.info(f"🔍 DEBUG: Найдено {len(issues_list)} задач, total_count = {total_count}")

        # ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ: Проверим что есть в задачах
        if len(issues_list) == 0 and search_term:
            current_app.logger.info(f"🔍 DEBUG: ПОИСК НЕ ДАЕТ РЕЗУЛЬТАТОВ! Проанализируем ВСЕ задачи пользователя...")

            # Загружаем ВСЕ задачи пользователя без поиска для анализа
            all_issues_list, _ = get_user_assigned_tasks_paginated_optimized(
                redmine_connector,
                redmine_user_id,
                page=1,
                per_page=20,
                search_term='',  # БЕЗ поиска
                sort_column='updated_on',
                sort_direction='desc'
            )

            current_app.logger.info(f"🔍 DEBUG: Загружено {len(all_issues_list)} задач БЕЗ поиска для анализа")

            # Анализируем содержимое первых задач
            for i, issue in enumerate(all_issues_list[:5]):
                issue_id = getattr(issue, 'id', 'unknown')
                issue_subject = getattr(issue, 'subject', '')
                issue_description = getattr(issue, 'description', '')

                current_app.logger.info(f"🔍 DEBUG: Задача #{issue_id}:")
                current_app.logger.info(f"  subject: '{issue_subject[:100]}'")
                current_app.logger.info(f"  description: '{issue_description[:100]}'")

                # Проверяем наличие поискового термина
                if search_term.lower() in issue_subject.lower() or search_term.lower() in issue_description.lower():
                    current_app.logger.info(f"  ✅ СОДЕРЖИТ поисковый термин '{search_term}'!")
                else:
                    current_app.logger.info(f"  ❌ НЕ содержит поисковый термин '{search_term}'")

        # Преобразуем задачи в JSON
        tasks_data = [task for task in (task_to_dict(issue) for issue in issues_list) if task]

        # Расчет времени выполнения
        execution_time = time.time() - start_time
        current_app.logger.info(
            f"Запрос /tasks/debug-search-api для {current_user.username} выполнен за {execution_time:.4f}с. Найдено задач: {len(tasks_data)}, всего: {total_count}"
        )

        return jsonify({
            "success": True,
            "search_term": search_term,
            "found_count": len(tasks_data),
            "total_count": total_count,
            "user_id": redmine_user_id,
            "tasks": tasks_data
        })

    except Exception as e:
        current_app.logger.error(f"🔍 DEBUG: Критическая ошибка: {e}")
        current_app.logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Критическая ошибка: {str(e)}"}), 500

# ===== NOTIFICATION COUNT API =====
@tasks_bp.route('/notifications-count', methods=['GET'])
@login_required
def get_tasks_notification_count():
    """Возвращает количество непрочитанных уведомлений (задач) для текущего пользователя"""
    try:
        # Можно переиспользовать существующую логику helpdesk-уведомлений
        from redmine import get_count_notifications
        count = get_count_notifications(current_user.id)
        return jsonify({'count': count})
    except Exception as e:
        current_app.logger.error(f'[tasks.notifications-count] error: {e}')
        return jsonify({'count': 0}), 500
