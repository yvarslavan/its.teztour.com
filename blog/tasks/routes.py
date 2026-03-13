# blog/tasks/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from blog.utils.decorators import debug_only
import time # Перенесен в начало файла из функций
import traceback # Добавлен traceback
# from datetime import datetime, date # Закомментируем, если не используется напрямую

# === НЕОБХОДИМЫЕ ИМПОРТЫ ИЗ blog.main.routes (НУЖНО БУДЕТ ТЩАТЕЛЬНО ПРОВЕРИТЬ И ДОПОЛНИТЬ) ===
import os
# from redmine import RedmineConnector, ... (и другие из redmine.py)
# from erp_oracle import connect_oracle, ... (и другие из erp_oracle.py)
from blog.utils.cache_manager import weekend_performance_optimizer, tasks_cache_optimizer # Добавлен tasks_cache_optimizer
from blog.models import User, Notifications, NotificationsAddNotes # Исправлены имена моделей
from redmine import RedmineConnector # Правильный путь импорта
from erp_oracle import connect_oracle, get_user_erp_password, db_host, db_port, db_service_name, db_user_name, db_password # Правильный путь импорта
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
    db_redmine_port,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name
)

# Импорты для нового маршрута
from blog.tasks.utils import get_redmine_connector, get_user_assigned_tasks_paginated_optimized, task_to_dict, create_redmine_connector # Исправлен относительный импорт
from redminelib.exceptions import ResourceNotFoundError # Для обработки ошибок Redmine

# Импорт формы для комментариев
from blog.user.forms import AddCommentRedmine, SendEmailForm

# Импорт для отправки email
from blog.utils.email_sender import email_sender

# Импорт для работы с файлами
import os
import uuid
from werkzeug.utils import secure_filename





# Константы для анонимного пользователя (из main/routes.py)
ANONYMOUS_USER_ID = 4  # ID анонимного пользователя в Redmine
DEFAULT_STATIC_ASSET_VERSION = "20260211"


def _parse_bool_query_param(value, default=False):
    """Безопасно парсит bool-параметры из query string."""
    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _tasks_debug_enabled():
    return bool(current_app.config.get('TASKS_DEBUG', False))


def _tasks_debug_log(level, message, *args, **kwargs):
    if not _tasks_debug_enabled():
        return

    log_method = getattr(current_app.logger, level, None)
    if callable(log_method):
        log_method(message, *args, **kwargs)


def _get_query_filter_values(param_name):
    values = request.args.getlist(f"{param_name}[]")
    if not values:
        raw_value = request.args.get(param_name, '')
        if raw_value:
            values = str(raw_value).split(',')

    return [str(value).strip() for value in values if str(value).strip()]


def _append_sql_in_filter(where_clauses, params, column_name, values):
    if not values:
        return

    placeholders = ', '.join(['%s'] * len(values))
    where_clauses.append(f"{column_name} IN ({placeholders})")
    params.extend(values)


def _get_direct_sql_cache_store():
    cache_store = getattr(current_app, '_tasks_direct_sql_cache', None)
    if cache_store is None:
        cache_store = {}
        current_app._tasks_direct_sql_cache = cache_store
    return cache_store


def _prune_direct_sql_cache(cache_store, ttl_seconds):
    if not cache_store:
        return

    now = time.time()
    expired_keys = [
        key for key, value in cache_store.items()
        if now - value.get('ts', 0) >= ttl_seconds
    ]
    for key in expired_keys:
        cache_store.pop(key, None)

def get_support_email():
    """
    Получает email службы технической поддержки из конфига

    Возвращает:
        str: Email службы технической поддержки
    """
    try:
        email = os.getenv('SENDER_EMAIL')
        if email is None:
            current_app.logger.warning("❌ [CONFIG] Не удалось получить SENDER_EMAIL из переменных окружения, используем fallback")
            return 'help@tez-tour.com'
        current_app.logger.info(f"✅ [CONFIG] Получен email из конфига: {email}")
        return email
    except Exception as e:
        current_app.logger.error(f"❌ [CONFIG] Ошибка при получении sender_email: {e}")
        return 'help@tez-tour.com'  # fallback

def generate_email_signature():
    """
    email HTML подпись службы технической поддержки TEZ TOUR

    Возвращает:
        str: HTML код email подписи
    """
    email_signature = """
    <div style="font-family: Tahoma, Verdana, Arial, sans-serif; font-size: 14px; color: #252525; line-height: 18px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #d1cdc7;">
        <p style="text-align: justify;">
            <ins>
                <small>
                    <em>
                        Это автоматическое сообщение. Пожалуйста, дождитесь нашего ответа и не создавайте новые заявки, отправляя письма на
                        <a href="mailto:help@tez-tour.com" target="_blank">help@tez-tour.com</a>, так как это может увеличить время обработки вашего запроса.<br>
                        При ответах, пожалуйста, не изменяйте тему письма.
                    </em>
                </small>
            </ins>
        </p>
        <p>
            Вы также можете просмотреть и обработать свои заявки, зарегистрировавшись на ресурсе
            <a href="https://its.tez-tour.com">https://its.tez-tour.com</a> с использованием вашего аккаунта TEZ ERP.
        </p>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
            <p style="margin: 0;">
                <strong>Международный туроператор TEZ TOUR</strong><br>
                <a href="http://www.tez-tour.com" target="_blank">www.tez-tour.com</a>
            </p>
        </div>
    </div>
    """
    return email_signature

def handle_task_comment_submission(form, task_id, redmine_connector):
    """Обработка добавления комментария к задаче.
    Аналогично handle_comment_submission из main/routes.py"""
    comment = form.comment.data

    # Для пользователей Redmine используем их ID, для остальных - анонимный ID
    if current_user.is_redmine_user and hasattr(current_user, 'id_redmine_user') and current_user.id_redmine_user:
        user_id = current_user.id_redmine_user
    else:
        user_id = ANONYMOUS_USER_ID

    current_app.logger.info(f"[handle_task_comment_submission] Добавление комментария с user_id: {user_id}")
    success, message = redmine_connector.add_comment(
        issue_id=task_id, notes=comment, user_id=user_id
    )

    if success:
        flash("Комментарий успешно добавлен к задаче!", "success")
        return True
    flash(message, "danger")
    return False

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

    # Стабильная версия ассетов: сохраняет кэш браузера между запросами.
    # Обновляется через STATIC_ASSET_VERSION в окружении при деплое.
    cache_buster = os.getenv("STATIC_ASSET_VERSION", DEFAULT_STATIC_ASSET_VERSION)

    # Получаем настройку показа баннера Kanban для текущего пользователя
    show_kanban_tips = getattr(current_user, 'show_kanban_tips', True)

    return render_template("my_tasks.html", title="Мои задачи", count_notifications=count_notifications,
                         cache_buster=cache_buster, show_kanban_tips=show_kanban_tips)

@tasks_bp.route("/my-tasks/<int:task_id>", methods=["GET", "POST"])
@login_required
@weekend_performance_optimizer
def task_detail(task_id):
    """Оптимизированная версия страницы деталей задачи"""

    start_time = time.time()
    debug_tasks = current_app.config.get("TASKS_DEBUG", False)
    if debug_tasks:
        current_app.logger.info(f"🚀 [PERFORMANCE] Загрузка задачи {task_id} - начало")

    if not current_user.is_redmine_user:
        flash("У вас нет доступа к этой функциональности.", "warning")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

    # Инициализация форм
    form = AddCommentRedmine()
    email_form = SendEmailForm()

    # Генерируем HTML подпись службы технической поддержки
    email_signature_html = generate_email_signature()

    # Получаем email службы технической поддержки
    support_email = get_support_email()
    if debug_tasks:
        current_app.logger.info(f"📧 [TASK_DETAIL] support_email для задачи {task_id}: {support_email}")

    try:
        # Получаем коннектор Redmine, используя локально сохранённый синхронный ERP-пароль
        redmine_conn_obj = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_conn_obj or not hasattr(redmine_conn_obj, 'redmine'):
            flash("Не удалось подключиться к Redmine.", "error")
            return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

        # Обработка POST запроса для добавления комментария
        if request.method == 'POST' and form.validate_on_submit():
            if handle_task_comment_submission(form, task_id, redmine_conn_obj):
                return redirect(url_for('tasks.task_detail', task_id=task_id))

        # Получаем детали задачи (без изменений)
        task = redmine_conn_obj.redmine.issue.get(
            task_id,
            include=['status', 'priority', 'project', 'tracker', 'author', 'assigned_to', 'journals', 'done_ratio', 'attachments', 'start_date', 'due_date', 'closed_on', 'easy_email_to', 'easy_email_cc']
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
        if debug_tasks:
            current_app.logger.info(f"🔍 [PERFORMANCE] Собрано ID: users={len(ids_data['user_ids'])}, statuses={len(ids_data['status_ids'])}, projects={len(ids_data['project_ids'])}, priorities={len(ids_data['priority_ids'])}")

        # ✅ НОВОЕ: Создаем ОДНО соединение для всех запросов
        connection = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)

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

            if debug_tasks:
                current_app.logger.info(f"✅ [PERFORMANCE] Загружено данных: users={len(user_names)}, projects={len(project_names)}, statuses={len(status_names)}, priorities={len(priority_names)}")

        finally:
            # ✅ ВАЖНО: Закрываем соединение
            connection.close()
            if debug_tasks:
                current_app.logger.info("🔒 [PERFORMANCE] Соединение с MySQL закрыто")

        # Получаем все статусы для создания словаря ID -> название (без изменений)
        status_mapping = {}
        try:
            redmine_statuses = redmine_conn_obj.redmine.issue_status.all()
            for status in redmine_statuses:
                status_mapping[status.id] = status.name
            if debug_tasks:
                current_app.logger.info(f"✅ Получено {len(status_mapping)} статусов для преобразования")
        except Exception as status_error:
            current_app.logger.error(f"❌ Не удалось получить статусы: {status_error}")
            status_mapping = {}

        # Время выполнения
        execution_time = time.time() - start_time
        if debug_tasks:
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
                             get_property_name=get_property_name_fast,


                             # ✅ Добавляем формы
                             form=form,
                             email_form=email_form,
                             email_signature_html=email_signature_html,
                             support_email=support_email,
                             clear_comment=True)

    except ResourceNotFoundError:
        current_app.logger.warning(f"Задача с ID {task_id} не найдена в Redmine")
        flash(f"Задача #{task_id} не найдена.", "error")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))
    except Exception as e:
        current_app.logger.error(f"[task_detail] Ошибка при получении задачи {task_id}: {e}. Trace: {traceback.format_exc()}")
        flash("Произошла ошибка при загрузке данных задачи.", "error")
        return redirect(url_for(MY_TASKS_PAGE_ENDPOINT))

# ===== API для работы с задачами =====

@tasks_bp.route("/get-my-tasks-paginated", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_my_tasks_paginated_api():
    """API для получения задач с пагинацией (совместимый URL)"""
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

        status_ids = _get_query_filter_values("status_id")
        project_ids = _get_query_filter_values("project_id")
        priority_ids = _get_query_filter_values("priority_id")
        include_description = request.args.get('with_description') == '1'

        # Создаем коннектор Redmine
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

        # Получаем параметры для оптимизации загрузки
        force_load = request.args.get('force_load', '0') == '1'
        exclude_completed = request.args.get('exclude_completed', '0') == '1'
        is_kanban_view = request.args.get('view') == 'kanban'

        # Оптимизация для Kanban: уменьшаем количество загружаемых задач
        if is_kanban_view:
            # Для Kanban загружаем меньше задач, но с лучшей оптимизацией
            per_page = min(per_page, 500)  # Ограничиваем до 500 задач для Kanban

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
            force_load=force_load,
            exclude_completed=exclude_completed
        )

        # Преобразуем задачи в JSON
        tasks_data = [task_to_dict(issue, include_description=include_description) for issue in issues_list]

        # Для Kanban доски применяем специальную логику для закрытых задач
        if is_kanban_view:
            # Разделяем задачи на активные и закрытые
            active_tasks = []
            closed_tasks = []

            for task in tasks_data:
                status_id = task.get('status_id', '')

                # Считаем закрытой по ID статуса (реальные ID хранятся в MySQL локализации)
                if str(status_id) in {'5', '6', '14'}:
                    closed_tasks.append(task)
                else:
                    active_tasks.append(task)

            # Объединяем активные задачи с ограниченными закрытыми
            tasks_data = active_tasks + closed_tasks
            total_count = len(tasks_data)

        # Определяем start_time для расчета времени выполнения
        execution_time = time.time() - start_time
        _tasks_debug_log(
            'info',
            "get-my-tasks-paginated completed in %.4fs for user=%s, page=%s, per_page=%s, rows=%s, total=%s",
            execution_time,
            current_user.username,
            page,
            per_page,
            len(tasks_data),
            total_count,
        )

        return jsonify({
            "draw": draw,
            "recordsTotal": total_count,
            "recordsFiltered": total_count,
            "data": tasks_data,
            "success": True,
            "execution_time": execution_time
        })

    except Exception as e:
        current_app.logger.error(f"Критическая ошибка в /tasks/get-my-tasks-paginated для {current_user.username}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "draw": request.args.get('draw', 1, type=int),
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "data": [],
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "success": False
        }), 500

@tasks_bp.route("/get-my-tasks-statistics-optimized", methods=["GET"])
@login_required
def get_my_tasks_statistics_optimized():
    """API для получения статистики задач"""
    try:
        # === In-memory cache (60s) per-user and query string ===
        try:
            import time as _t
            if not hasattr(current_app, '_tasks_stats_cache'):
                current_app._tasks_stats_cache = {}
            _key = (current_user.id, bytes(request.query_string))
            _entry = current_app._tasks_stats_cache.get(_key)
            if _entry and (_t.time() - _entry['ts'] < 60):
                return jsonify(_entry['data'])
        except Exception:
            pass
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector or not hasattr(redmine_connector, 'redmine'):
            payload = {
                "error": "Не удалось создать коннектор Redmine",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }
            return jsonify(payload), 500

        # Получаем ID пользователя Redmine из SQLite (НЕ из Redmine API!)
        redmine_user_id = current_user.id_redmine_user
        current_app.logger.info(f"🔍 [STATISTICS] Текущий redmine_user_id из SQLite: {redmine_user_id} (current_user.id: {current_user.id})")

        # ИСПРАВЛЕНИЕ: Используем ПРЯМЫЕ SQL-запросы для всей статистики (избегаем LIMIT 1000)
        current_app.logger.info(f"🗄️ [STATISTICS] Запуск ИСПРАВЛЕННОЙ статистики через прямые SQL-запросы для пользователя {redmine_user_id}")

        # Получаем подключение к MySQL Redmine для точного подсчета ВСЕХ задач
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
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

        data = {
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
        }
        try:
            current_app._tasks_stats_cache[_key] = { 'ts': _t.time(), 'data': data }
        except Exception:
            pass
        return jsonify(data)

    except Exception as e:
        current_app.logger.error(f"Ошибка в get_my_tasks_statistics_optimized: {e}")
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

    current_app.logger.info("🚀 [PERFORMANCE] Запуск ОПТИМИЗИРОВАННОГО API фильтров...")

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "У вас нет доступа к модулю 'Мои задачи'.",
                "statuses": [],
                "projects": [],
                "priorities": []
            }), 403

        # Короткий кеш фильтров: данные редко меняются, но запрашиваются часто
        try:
            now_ts = time.time()
            cache_ttl = 300
            cache_key = "global"
            if not hasattr(current_app, "_tasks_filters_cache"):
                current_app._tasks_filters_cache = {}
            cache_entry = current_app._tasks_filters_cache.get(cache_key)
            if cache_entry and (now_ts - cache_entry["ts"] < cache_ttl):
                return jsonify(cache_entry["data"])
        except Exception:
            pass

        # Получаем подключение к MySQL Redmine (ИСПРАВЛЕНО!)
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
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
            current_app.logger.info(f"✅ [PERFORMANCE] Статусы (локализованные) загружены за {status_time:.3f}с ({len(statuses)} записей)")

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
            current_app.logger.info(f"✅ [PERFORMANCE] Проекты (простой список) загружены за {projects_time:.3f}с ({len(projects)} записей)")

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
                current_app.logger.warning("⚠️ [PERFORMANCE] Нет данных в u_Priority, возвращаемся к enumerations")
                cursor.execute("""
                    SELECT id, name
                    FROM enumerations
                    WHERE type = 'IssuePriority'
                    AND active = 1
                    ORDER BY position, name
                """)
                priorities = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

            priorities_time = time.time() - priorities_start
            current_app.logger.info(f"✅ [PERFORMANCE] Приоритеты (локализованные) загружены за {priorities_time:.3f}с ({len(priorities)} записей)")

        except Exception as sql_error:
            current_app.logger.error(f"❌ [PERFORMANCE] Ошибка MySQL запроса: {sql_error}")
            raise sql_error
        finally:
            cursor.close()
            mysql_conn.close()

        total_time = time.time() - start_time
        current_app.logger.info(f"🎯 [PERFORMANCE] ОПТИМИЗИРОВАННЫЙ API завершен за {total_time:.3f}с (статусы: {len(statuses)}, проекты: {len(projects)}, приоритеты: {len(priorities)})")

        response_payload = {
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
        }

        try:
            current_app._tasks_filters_cache["global"] = {
                "ts": time.time(),
                "data": response_payload
            }
        except Exception:
            pass

        return jsonify(response_payload)

    except Exception as e:
        total_time = time.time() - start_time
        current_app.logger.error(f"❌ [PERFORMANCE] Ошибка в оптимизированном API фильтров за {total_time:.3f}с: {e}")
        import traceback
        current_app.logger.error(f"❌ [PERFORMANCE] Traceback: {traceback.format_exc()}")
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

# ===== МАРШРУТЫ ДЛЯ ТЕСТОВЫХ ФАЙЛОВ УДАЛЕНЫ =====

def get_my_tasks_statuses_localized():
    """API для получения локализованных статусов задач с правильной сортировкой по position

    Внимание: Не проверяет авторизацию! Должен вызываться только из авторизованного контекста.
    """
    start_time = time.time()
    logger.info("📋 [STATUSES] Запуск API для получения локализованных статусов...")

    try:
        # Подключение к MySQL Redmine
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
        if not mysql_conn:
            return []

        cursor = mysql_conn.cursor()
        statuses = []

        try:
            # Получаем локализованные статусы с правильной сортировкой по position из issue_statuses
            status_start = time.time()
            # ВАЖНО: не используем алиас "is" (зарезервирован в SQL/логический оператор)
            cursor.execute("""
                SELECT us.id, us.name, ist.position, ist.is_closed
                FROM u_statuses us
                JOIN issue_statuses AS ist ON us.id = ist.id
                ORDER BY ist.position ASC, us.name ASC
            """)

            statuses = []
            for row in cursor.fetchall():
                statuses.append({
                    "id": row["id"],
                    "name": row["name"],
                    "position": row["position"],
                    "is_closed": bool(row["is_closed"])
                })

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
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
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
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
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
@debug_only
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

# ===== API ENDPOINT ДЛЯ ДОБАВЛЕНИЯ КОММЕНТАРИЕВ =====

@tasks_bp.route("/api/task/<int:task_id>/comment", methods=["POST"])
@login_required
def add_task_comment_api(task_id):
    """API endpoint для добавления комментария к задаче через AJAX"""
    try:
        current_app.logger.info(f"[API] Получен запрос на добавление комментария к задаче {task_id}")
        current_app.logger.info(f"[API] Request method: {request.method}")
        current_app.logger.info(f"[API] Request content_type: {request.content_type}")
        current_app.logger.info(f"[API] Request headers: {dict(request.headers)}")

        # Простая проверка для отладки
        if request.method != 'POST':
            current_app.logger.error(f"[API] Неверный HTTP метод: {request.method}")
            return jsonify({
                'success': False,
                'error': 'Метод не поддерживается'
            }), 405

        if not current_user.is_redmine_user:
            current_app.logger.warning(f"[API] Пользователь {current_user.username} не является пользователем Redmine")
            return jsonify({
                'success': False,
                'error': 'У вас нет доступа к этой функциональности'
            }), 403

        # Получаем данные из запроса
        if request.is_json:
            data = request.get_json()
            current_app.logger.info(f"[API] Получены JSON данные: {data}")
        else:
            current_app.logger.error(f"[API] Запрос не содержит JSON данных. Content-Type: {request.content_type}")
            current_app.logger.error(f"[API] Request data: {request.data}")
            current_app.logger.error(f"[API] Request form: {request.form}")

            # Попробуем получить данные другим способом
            try:
                if request.form and 'comment' in request.form:
                    data = {'comment': request.form['comment']}
                    current_app.logger.info(f"[API] Получены данные через form: {data}")
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Неверный формат данных'
                    }), 400
            except Exception as e:
                current_app.logger.error(f"[API] Ошибка при получении данных: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Неверный формат данных'
                }), 400

        if not data or 'comment' not in data:
            current_app.logger.error(f"[API] Отсутствует поле 'comment' в данных: {data}")
            return jsonify({
                'success': False,
                'error': 'Комментарий не может быть пустым'
            }), 400

        comment = data['comment'].strip()
        if not comment:
            current_app.logger.error(f"[API] Пустой комментарий")
            return jsonify({
                'success': False,
                'error': 'Комментарий не может быть пустым'
            }), 400

        current_app.logger.info(f"[API] Создание коннектора Redmine для пользователя {current_user.username}")

        # Получаем коннектор Redmine
        redmine_conn_obj = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_conn_obj or not hasattr(redmine_conn_obj, 'redmine'):
            current_app.logger.error(f"[API] Не удалось создать коннектор Redmine")
            return jsonify({
                'success': False,
                'error': 'Не удалось подключиться к Redmine'
            }), 500

        current_app.logger.info(f"[API] Добавление комментария к задаче {task_id}")

        # Добавляем комментарий
        # Для пользователей Redmine используем их ID, для остальных - анонимный ID
        if current_user.is_redmine_user and hasattr(current_user, 'id_redmine_user') and current_user.id_redmine_user:
            user_id = current_user.id_redmine_user
        else:
            user_id = ANONYMOUS_USER_ID

        current_app.logger.info(f"[API] Добавление комментария с user_id: {user_id}")
        success, message = redmine_conn_obj.add_comment(
            issue_id=task_id, notes=comment, user_id=user_id
        )

        if success:
            current_app.logger.info(f"[API] Комментарий успешно добавлен к задаче {task_id}")
            return jsonify({
                'success': True,
                'message': 'Комментарий успешно добавлен к задаче!'
            })
        else:
            current_app.logger.error(f"[API] Ошибка добавления комментария: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Исключение при добавлении комментария к задаче {task_id}: {e}")
        current_app.logger.error(f"[API] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при добавлении комментария'
        }), 500

# ===== API ENDPOINT ДЛЯ УДАЛЕНИЯ КОММЕНТАРИЕВ =====

@tasks_bp.route("/api/task/<int:task_id>/comment/<int:journal_id>/delete", methods=["DELETE"])
@login_required
def delete_task_comment_api(task_id, journal_id):
    """API endpoint для удаления комментария к задаче через AJAX с прямыми SQL запросами"""
    try:
        current_app.logger.info(f"[API] Получен запрос на удаление комментария {journal_id} из задачи {task_id}")

        if not current_user.is_redmine_user:
            current_app.logger.warning(f"[API] Пользователь {current_user.username} не является пользователем Redmine")
            return jsonify({
                'success': False,
                'error': 'У вас нет доступа к этой функциональности'
            }), 403

        # Импортируем функцию для работы с БД
        from blog.redmine import execute_query

        # Проверяем существование комментария и получаем информацию о нем
        check_query = """
            SELECT j.id, j.user_id, j.journalized_id, j.notes, u.login as user_login
            FROM journals j
            LEFT JOIN users u ON j.user_id = u.id
            WHERE j.id = %s AND j.journalized_type = 'Issue'
        """

        success, result = execute_query(check_query, (journal_id,), fetch='one')

        if not success:
            current_app.logger.error(f"[API] Ошибка при проверке комментария {journal_id}: {result}")
            return jsonify({'success': False, 'error': 'Ошибка при проверке комментария'}), 500

        if not result:
            current_app.logger.error(f"[API] Комментарий {journal_id} не найден")
            return jsonify({'success': False, 'error': 'Комментарий не найден'}), 404

        # Проверяем, что комментарий принадлежит указанной задаче
        if result['journalized_id'] != task_id:
            current_app.logger.error(f"[API] Комментарий {journal_id} не принадлежит задаче {task_id}")
            return jsonify({'success': False, 'error': 'Комментарий не принадлежит этой задаче'}), 400

        # Проверяем права на удаление
        # Только автор комментария или администратор может удалять
        is_author = result['user_id'] == current_user.id_redmine_user if hasattr(current_user, 'id_redmine_user') else False
        is_admin = getattr(current_user, 'is_admin', False)

        # Дополнительная проверка по логину пользователя
        if not is_author and result['user_login']:
            is_author = result['user_login'] == current_user.username

        if not is_author and not is_admin:
            current_app.logger.warning(f"[API] Пользователь {current_user.username} не имеет прав на удаление комментария {journal_id}")
            return jsonify({'success': False, 'error': 'У вас нет прав на удаление этого комментария'}), 403

        # Удаляем комментарий из базы данных
        delete_query = "DELETE FROM journals WHERE id = %s"

        success, affected_rows = execute_query(delete_query, (journal_id,), commit=True)

        if not success:
            current_app.logger.error(f"[API] Ошибка при удалении комментария {journal_id}: {affected_rows}")
            return jsonify({'success': False, 'error': 'Ошибка при удалении комментария'}), 500

        if affected_rows == 0:
            current_app.logger.error(f"[API] Комментарий {journal_id} не был удален (affected_rows = 0)")
            return jsonify({'success': False, 'error': 'Комментарий не был удален'}), 500

        current_app.logger.info(f"[API] Комментарий {journal_id} успешно удален пользователем {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'Комментарий успешно удален!'
        })

    except Exception as e:
        import traceback
        current_app.logger.error(f"[API] Ошибка при удалении комментария {journal_id} из задачи {task_id}: {e}. Trace: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при удалении комментария'
        }), 500

@tasks_bp.route("/api/task/<int:task_id>/comment/<int:journal_id>/edit", methods=["PUT"])
@login_required
def edit_task_comment_api(task_id, journal_id):
    """API endpoint для редактирования комментария к задаче через AJAX с прямыми SQL запросами"""
    try:
        current_app.logger.info(f"[API] Получен запрос на редактирование комментария {journal_id} в задаче {task_id}")

        if not current_user.is_redmine_user:
            return jsonify({'success': False, 'error': 'Нет доступа'}), 403

        data = request.get_json()
        if not data or 'comment' not in data:
            return jsonify({'success': False, 'error': 'Комментарий не может быть пустым'}), 400

        new_comment = data['comment'].strip()
        if not new_comment:
            return jsonify({'success': False, 'error': 'Комментарий не может быть пустым'}), 400

        # Импортируем функцию для работы с БД
        from blog.redmine import execute_query

        # Проверяем существование комментария и получаем информацию о нем
        check_query = """
            SELECT j.id, j.user_id, j.journalized_id, j.notes, u.login as user_login
            FROM journals j
            LEFT JOIN users u ON j.user_id = u.id
            WHERE j.id = %s AND j.journalized_type = 'Issue'
        """

        success, result = execute_query(check_query, (journal_id,), fetch='one')

        if not success:
            current_app.logger.error(f"[API] Ошибка при проверке комментария {journal_id}: {result}")
            return jsonify({'success': False, 'error': 'Ошибка при проверке комментария'}), 500

        if not result:
            current_app.logger.error(f"[API] Комментарий {journal_id} не найден")
            return jsonify({'success': False, 'error': 'Комментарий не найден'}), 404

        # Проверяем, что комментарий принадлежит указанной задаче
        if result['journalized_id'] != task_id:
            current_app.logger.error(f"[API] Комментарий {journal_id} не принадлежит задаче {task_id}")
            return jsonify({'success': False, 'error': 'Комментарий не принадлежит этой задаче'}), 400

        # Проверяем права на редактирование
        # Только автор комментария или администратор может редактировать
        is_author = result['user_id'] == current_user.id_redmine_user if hasattr(current_user, 'id_redmine_user') else False
        is_admin = getattr(current_user, 'is_admin', False)

        # Дополнительная проверка по логину пользователя
        if not is_author and result['user_login']:
            is_author = result['user_login'] == current_user.username

        if not is_author and not is_admin:
            current_app.logger.warning(f"[API] Пользователь {current_user.username} не имеет прав на редактирование комментария {journal_id}")
            return jsonify({'success': False, 'error': 'У вас нет прав на редактирование этого комментария'}), 403

        # Обновляем комментарий в базе данных
        update_query = "UPDATE journals SET notes = %s WHERE id = %s"

        success, affected_rows = execute_query(update_query, (new_comment, journal_id), commit=True)

        if not success:
            current_app.logger.error(f"[API] Ошибка при обновлении комментария {journal_id}: {affected_rows}")
            return jsonify({'success': False, 'error': 'Ошибка при обновлении комментария'}), 500

        if affected_rows == 0:
            current_app.logger.error(f"[API] Комментарий {journal_id} не был обновлен (affected_rows = 0)")
            return jsonify({'success': False, 'error': 'Комментарий не был обновлен'}), 500

        current_app.logger.info(f"[API] Комментарий {journal_id} успешно обновлен пользователем {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'Комментарий успешно обновлен!',
            'journal_id': journal_id,
            'notes': new_comment
        })

    except Exception as e:
        import traceback
        current_app.logger.error(f"[API] Ошибка при редактировании комментария {journal_id} в задаче {task_id}: {e}. Trace: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500

@tasks_bp.route("/get-completed-tasks", methods=["GET"])
@login_required
@weekend_performance_optimizer
def get_completed_tasks():
    """Deprecated compatibility endpoint for legacy clients.

    Внутренний runtime страницы его больше не использует.
    Оставляем только лёгкую SQL-реализацию вместо тяжёлой загрузки через Redmine API.
    """
    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "data": []
            }), 403

        if not getattr(current_user, 'id_redmine_user', None):
            return jsonify({
                "error": "Ошибка: отсутствует ID пользователя Redmine",
                "success": False,
                "data": []
            }), 500

        limit = max(1, min(request.args.get('limit', 25, type=int), 50))
        mysql_conn = get_connection(
            db_redmine_host,
            db_redmine_user_name,
            db_redmine_password,
            db_redmine_name,
            port=db_redmine_port
        )
        if not mysql_conn:
            return jsonify({
                "error": "Не удалось подключиться к базе данных",
                "success": False,
                "data": []
            }), 500

        cursor = mysql_conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    i.id,
                    i.subject,
                    i.status_id,
                    COALESCE(us.name, ist.name) AS status_name,
                    i.priority_id,
                    COALESCE(up.name, e.name) AS priority_name,
                    p.name AS project_name,
                    CONCAT(ua.firstname, ' ', ua.lastname) AS assigned_to_name,
                    i.created_on,
                    i.updated_on
                FROM issues i
                LEFT JOIN issue_statuses ist ON i.status_id = ist.id
                LEFT JOIN u_statuses us ON i.status_id = us.id
                LEFT JOIN projects p ON i.project_id = p.id
                LEFT JOIN enumerations e ON i.priority_id = e.id AND e.type = 'IssuePriority'
                LEFT JOIN u_Priority up ON e.id = up.id
                LEFT JOIN users ua ON i.assigned_to_id = ua.id
                WHERE i.assigned_to_id = %s
                  AND ist.is_closed = 1
                ORDER BY i.updated_on DESC
                LIMIT %s
                """,
                (current_user.id_redmine_user, limit)
            )
            tasks_data = [
                {
                    'id': row['id'],
                    'subject': row['subject'],
                    'status_name': row['status_name'] or 'Неизвестен',
                    'status_id': row['status_id'],
                    'priority_name': row['priority_name'] or 'Обычный',
                    'project_name': row['project_name'] or 'Без проекта',
                    'assigned_to_name': row['assigned_to_name'] or 'Не назначен',
                    'created_on': row['created_on'].isoformat() if row['created_on'] else None,
                    'updated_on': row['updated_on'].isoformat() if row['updated_on'] else None,
                }
                for row in cursor.fetchall()
            ]
        finally:
            cursor.close()
            mysql_conn.close()

        return jsonify({
            "success": True,
            "deprecated": True,
            "data": tasks_data,
            "total": len(tasks_data),
            "limit": limit,
            "offset": 0,
            "has_more": False
        })

    except Exception as e:
        current_app.logger.error(f"Критическая ошибка в /tasks/get-completed-tasks для {current_user.username}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "data": []
        }), 500

# Удален дублирующий маршрут - теперь используется /tasks/api/task/<id>/status из api_routes.py

@tasks_bp.route("/get-my-tasks-statuses", methods=["GET"])
@login_required
def get_my_tasks_statuses():
    """API для получения всех статусов задач из таблицы u_statuses"""
    try:
        if not current_user.is_redmine_user:
            return jsonify({"success": False, "error": "Доступ запрещён"}), 403

        current_app.logger.info(f"Запрос статусов задач для пользователя {current_user.username}")

        # Кешируем список статусов (общий для всех пользователей) на 5 минут
        try:
            now_ts = time.time()
            cache_ttl = 300
            cache_key = "global"
            if not hasattr(current_app, "_tasks_statuses_cache"):
                current_app._tasks_statuses_cache = {}
            cache_entry = current_app._tasks_statuses_cache.get(cache_key)
            if cache_entry and (now_ts - cache_entry["ts"] < cache_ttl):
                return jsonify(cache_entry["data"])
        except Exception:
            pass

        # Получаем локализованные статусы из таблицы u_statuses
        localized_statuses = get_my_tasks_statuses_localized()
        current_app.logger.info(f"📋 Получено локализованных статусов: {len(localized_statuses) if localized_statuses else 0}")

        if localized_statuses:
            current_app.logger.info("📋 Локализованные статусы:")
            for status in localized_statuses:
                current_app.logger.info(f"  - ID: {status['id']}, Name: {status['name']}")

        if not localized_statuses:
            current_app.logger.error("❌ Не удалось получить статусы из таблицы u_statuses")
            return jsonify({"success": False, "error": "Не удалось получить статусы"}), 500

        # Логируем все полученные статусы для мониторинга
        current_app.logger.info("📋 [STATUSES] Все полученные статусы:")
        for status in localized_statuses:
            current_app.logger.info(f"  - ID: {status['id']}, Name: '{status['name']}', Position: {status['position']}, Is_Closed: {status['is_closed']}")

        # Преобразуем в формат для фронтенда
        statuses_list = []
        for status in localized_statuses:
            statuses_list.append({
                'id': status['id'],
                'name': status['name'],
                'position': status['position'],
                'is_closed': status['is_closed']
            })

            current_app.logger.info(f"  Статус: {status['name']} (ID: {status['id']}, Position: {status['position']}, is_closed: {status['is_closed']})")

        current_app.logger.info(f"✅ Получено {len(statuses_list)} статусов из u_statuses для пользователя {current_user.username}")

        response_payload = {
            "success": True,
            "data": statuses_list
        }

        try:
            current_app._tasks_statuses_cache["global"] = {
                "ts": time.time(),
                "data": response_payload
            }
        except Exception:
            pass

        return jsonify(response_payload)

    except Exception as e:
        current_app.logger.error(f"Ошибка получения статусов для {current_user.username}: {str(e)}")
        return jsonify({"success": False, "error": f"Ошибка получения статусов: {str(e)}"}), 500

# debug_statuses endpoint удален

@tasks_bp.route("/get-my-tasks-direct-sql", methods=["GET"])
@login_required
def get_my_tasks_direct_sql():
    """Получение задач напрямую из базы данных через SQL запрос"""
    try:
        if not current_user.is_redmine_user:
            return jsonify({"success": False, "error": "Доступ запрещён"}), 403

        # Получаем параметры
        length = request.args.get('length', 100, type=int)
        start = request.args.get('start', 0, type=int)
        view = request.args.get('view', 'table')
        exclude_completed = _parse_bool_query_param(request.args.get('exclude_completed'), default=False)
        kanban_limit_per_status = request.args.get('kanban_limit_per_status', 10, type=int)
        kanban_limit_per_status = max(1, min(kanban_limit_per_status, 50))
        status_filter_values = _get_query_filter_values('status_id')
        project_filter_values = _get_query_filter_values('project_id')
        priority_filter_values = _get_query_filter_values('priority_id')

        cache_ttl_seconds = 10 if view == 'kanban' else 0
        cache_key = None
        if cache_ttl_seconds:
            cache_store = _get_direct_sql_cache_store()
            _prune_direct_sql_cache(cache_store, cache_ttl_seconds)
            cache_key = (current_user.id, bytes(request.query_string))
            cache_entry = cache_store.get(cache_key)
            if cache_entry and time.time() - cache_entry.get('ts', 0) < cache_ttl_seconds:
                return jsonify(cache_entry['data'])

        # Подключаемся к базе данных
        mysql_conn = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port)
        if not mysql_conn:
            return jsonify({"success": False, "error": "Не удалось подключиться к базе данных"}), 500

        cursor = mysql_conn.cursor()
        try:
            where_clauses = ["i.assigned_to_id = %s"]
            params = [current_user.id_redmine_user]
            # Базовый SQL запрос
            base_select = """
                SELECT
                    i.id,
                    i.subject,
                    i.status_id,
                    i.assigned_to_id,
                    i.author_id,
                    i.priority_id,
                    i.project_id,
                    i.created_on,
                    i.updated_on,
                    i.due_date,
                    i.done_ratio,
                    i.closed_on,
                    p.name as project_name,
                    us.name as status_name,
                    ist.is_closed as status_is_closed,
                    COALESCE(up.name, e.name) as priority_name,
                    e.position as priority_position,
                    CONCAT(ua.firstname, ' ', ua.lastname) as assigned_to_name,
                    CONCAT(uau.firstname, ' ', uau.lastname) as author_name
                FROM issues i
                LEFT JOIN projects p ON i.project_id = p.id
                LEFT JOIN u_statuses us ON i.status_id = us.id
                LEFT JOIN issue_statuses ist ON i.status_id = ist.id
                LEFT JOIN enumerations e ON i.priority_id = e.id AND e.type = 'IssuePriority'
                    LEFT JOIN u_Priority up ON e.id = up.id
                    LEFT JOIN users ua ON i.assigned_to_id = ua.id
                    LEFT JOIN users uau ON i.author_id = uau.id
            """

            kanban_status_counts = {}
            used_window_kanban_query = False

            if exclude_completed:
                # Исключаем статусы, помеченные как закрытые в issue_statuses
                where_clauses.append("ist.is_closed = 0")

            _append_sql_in_filter(where_clauses, params, "i.status_id", status_filter_values)
            _append_sql_in_filter(where_clauses, params, "i.project_id", project_filter_values)
            _append_sql_in_filter(where_clauses, params, "i.priority_id", priority_filter_values)

            where_sql = " WHERE " + " AND ".join(where_clauses)
            base_query_body = base_select + where_sql

            if view == 'kanban':
                # Для Kanban ограничиваем задачи по каждому статусу прямо в SQL (быстрее и меньше данных)
                window_query = f"""
                    SELECT *
                    FROM (
                        SELECT
                            base.*,
                            ROW_NUMBER() OVER (PARTITION BY base.status_id ORDER BY base.updated_on DESC) AS status_rank
                        FROM (
                            {base_query_body}
                        ) AS base
                    ) AS ranked
                    WHERE ranked.status_rank <= %s
                    ORDER BY ranked.updated_on DESC
                """
                window_params = [*params, kanban_limit_per_status]

                try:
                    cursor.execute(window_query, window_params)
                    rows = cursor.fetchall()
                    used_window_kanban_query = True

                    # Подсчёт полных totals по статусам (для UI "shown/total")
                    counts_query = """
                        SELECT i.status_id, COUNT(*) AS total_count
                        FROM issues i
                        LEFT JOIN issue_statuses ist ON i.status_id = ist.id
                    """
                    counts_query += where_sql + " GROUP BY i.status_id"
                    counts_params = list(params)

                    cursor.execute(counts_query, counts_params)
                    for row in cursor.fetchall():
                        status_id = row["status_id"]
                        kanban_status_counts[status_id] = {
                            "shown": 0,
                            "total": row["total_count"]
                        }
                except Exception as window_query_error:
                    current_app.logger.warning(
                        f"⚠️ [DIRECT SQL] Window-функция недоступна, fallback на legacy режим: {window_query_error}"
                    )
                    fallback_query = base_query_body + " ORDER BY i.updated_on DESC"
                    cursor.execute(fallback_query, params)
                    rows = cursor.fetchall()
            else:
                base_query = base_query_body + " ORDER BY i.updated_on DESC LIMIT %s OFFSET %s"
                paged_params = [*params, length, start]
                cursor.execute(base_query, paged_params)
                rows = cursor.fetchall()

            # Преобразуем результаты в формат для фронтенда
            tasks = []
            for row in rows:
                # Приоритеты уже локализованы SQL (COALESCE(up.name, e.name)) —
                # берём значение как есть, без ручного маппинга,
                # чтобы автоматически поддерживать новые значения в u_Priority
                priority_name = row['priority_name'] or "Обычный"

                task = {
                    'id': row['id'],
                    'subject': row['subject'],
                    'status_id': row['status_id'],
                    'status_name': row['status_name'],
                    'status_is_closed': bool(row.get('status_is_closed', 0)),
                    'assigned_to_id': row['assigned_to_id'],
                    'assigned_to_name': row['assigned_to_name'],
                    'author_id': row['author_id'],
                    'author_name': row['author_name'],
                    'priority_id': row['priority_id'],
                    'priority_name': priority_name,
                    'priority_position': row.get('priority_position'),
                    'project_id': row['project_id'],
                    'project_name': row['project_name'],
                    'created_on': row['created_on'].isoformat() if row['created_on'] else None,
                    'updated_on': row['updated_on'].isoformat() if row['updated_on'] else None,
                    'due_date': row['due_date'].isoformat() if row['due_date'] else None,
                    'done_ratio': row['done_ratio'],
                    'closed_on': row['closed_on'].isoformat() if row['closed_on'] else None
                }
                tasks.append(task)

            # Для Kanban в fallback-режиме ограничиваем задачи по статусам в Python
            if view == 'kanban' and not used_window_kanban_query:
                # Группируем задачи по статусам
                tasks_by_status = {}

                for task in tasks:
                    status_id = task['status_id']
                    if status_id not in tasks_by_status:
                        tasks_by_status[status_id] = []
                    tasks_by_status[status_id].append(task)

                # Ограничиваем до 10 задач в каждом статусе
                limited_tasks = []
                status_counts = {}

                for status_id, status_tasks in tasks_by_status.items():
                    # Сортируем по дате обновления (новые сначала)
                    status_tasks.sort(key=lambda x: x['updated_on'] or '', reverse=True)

                    # Берем только первые N задач
                    limited_status_tasks = status_tasks[:kanban_limit_per_status]
                    limited_tasks.extend(limited_status_tasks)

                    # Сохраняем информацию о количестве
                    status_counts[status_id] = {
                        'shown': len(limited_status_tasks),
                        'total': len(status_tasks)
                    }

                tasks = limited_tasks
                kanban_status_counts = status_counts
            elif view == 'kanban':
                for task in tasks:
                    status_id = task.get('status_id')
                    if status_id not in kanban_status_counts:
                        kanban_status_counts[status_id] = {"shown": 0, "total": 0}
                    kanban_status_counts[status_id]["shown"] += 1

            response_data = {
                "success": True,
                "data": tasks,
            }

            # Добавляем информацию о количестве задач для Kanban
            if view == 'kanban':
                response_data["status_counts"] = kanban_status_counts

            if cache_ttl_seconds and cache_key is not None:
                cache_store = _get_direct_sql_cache_store()
                cache_store[cache_key] = {
                    'ts': time.time(),
                    'data': response_data
                }

            return jsonify(response_data)

        finally:
            cursor.close()
            mysql_conn.close()

    except Exception as e:
        current_app.logger.error(f"Ошибка получения задач через SQL: {str(e)}")
        return jsonify({"success": False, "error": f"Ошибка: {str(e)}"}), 500

# test-direct-sql endpoint удален

# test-closed-tasks-count endpoint удален

@tasks_bp.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    """
    Endpoint для загрузки изображений в TinyMCE
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Файл не найден"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Файл не выбран"}), 400

                # Проверяем тип файла
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        if not file.filename or not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({"error": "Неподдерживаемый тип файла"}), 400

        # Создаем уникальное имя файла
        filename = secure_filename(file.filename or 'image')
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        # Создаем папку для загрузок если её нет
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'email_images')
        os.makedirs(upload_folder, exist_ok=True)

        # Сохраняем файл
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Возвращаем URL для TinyMCE
        image_url = url_for('static', filename=f'uploads/email_images/{unique_filename}')

        return jsonify({"location": image_url})

    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке изображения: {e}")
        return jsonify({"error": "Ошибка при загрузке файла"}), 500

@tasks_bp.route("/api/task/<int:task_id>/send-email", methods=["POST"])
@login_required
def send_task_email_api(task_id):
    """API для отправки email из деталей задачи"""
    try:
        current_app.logger.info(f"📨 [API] Получен запрос на отправку email для задачи {task_id}")
        current_app.logger.info(f"   Пользователь: {current_user.username}")

        if not current_user.is_redmine_user:
            current_app.logger.warning(f"⚠️ [API] Доступ запрещен для пользователя {current_user.username}")
            return jsonify({"success": False, "error": "Доступ запрещен"}), 403

        # Получаем данные из FormData
        sender = request.form.get('sender', '').strip()
        recipient = request.form.get('recipient', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        cc = request.form.get('cc', '').strip()
        send_email = request.form.get('send_email', 'y') == 'y'

        # Получаем файлы
        attachments = request.files.getlist('attachments')
        current_app.logger.info(f"📎 [API] Получено файлов: {len(attachments)}")

        # Валидация обязательных полей
        current_app.logger.info(f"🔍 [API] Валидация данных для задачи {task_id}")
        current_app.logger.info(f"   Получатель: '{recipient}'")
        current_app.logger.info(f"   Тема: '{subject}'")
        current_app.logger.info(f"   Сообщение: '{message[:50]}...'")

        if not recipient:
            current_app.logger.error(f"❌ [API] Email получателя отсутствует для задачи {task_id}")
            return jsonify({"success": False, "error": "Email получателя обязателен"}), 400
        if not subject:
            current_app.logger.error(f"❌ [API] Тема письма отсутствует для задачи {task_id}")
            return jsonify({"success": False, "error": "Тема письма обязательна"}), 400
        if not message:
            current_app.logger.error(f"❌ [API] Текст сообщения отсутствует для задачи {task_id}")
            return jsonify({"success": False, "error": "Текст сообщения обязателен"}), 400

        # Если отправка email отключена, просто возвращаем успех
        if not send_email:
            return jsonify({
                "success": True,
                "message": "Email не отправлен (отправка отключена)"
            })

                # Отправляем email
        current_app.logger.info(f"🚀 [API] Начинаем отправку email для задачи {task_id}")
        current_app.logger.info(f"   Получатель: {recipient}")
        current_app.logger.info(f"   Тема: {subject}")
        current_app.logger.info(f"   CC: {cc}")
        current_app.logger.info(f"   email_sender объект: {email_sender}")
        current_app.logger.info(f"   email_sender тип: {type(email_sender)}")

        try:
            # Сохраняем файлы во временную папку
            temp_files = []
            if attachments:
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()

                for attachment in attachments:
                    if attachment.filename:
                        # Создаем уникальное имя файла
                        import uuid
                        file_ext = os.path.splitext(attachment.filename)[1]
                        temp_filename = f"email_attachment_{uuid.uuid4().hex}{file_ext}"
                        temp_path = os.path.join(temp_dir, temp_filename)

                        # Сохраняем файл
                        attachment.save(temp_path)
                        temp_files.append(temp_path)
                        current_app.logger.info(f"📎 [API] Сохранен файл: {attachment.filename} -> {temp_path}")

            success = email_sender.send_task_email(
                task_id=task_id,
                recipient=recipient,
                subject=subject,
                message=message,
                cc=cc if cc else None,
                attachments=temp_files if temp_files else None,
                reply_to=sender if sender else None
            )
        except Exception as e:
            current_app.logger.error(f"❌ [API] Ошибка при вызове send_task_email: {e}")
            current_app.logger.error(f"   Traceback: {traceback.format_exc()}")
            raise

        current_app.logger.info(f"📧 [API] Результат отправки email для задачи {task_id}: {success}")

        # Очищаем временные файлы
        if 'temp_files' in locals():
            import os
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        current_app.logger.info(f"🗑️ [API] Удален временный файл: {temp_file}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ [API] Не удалось удалить временный файл {temp_file}: {e}")

        if success:
            current_app.logger.info(f"✅ [API] Email успешно отправлен для задачи {task_id} на {recipient}")
            return jsonify({
                "success": True,
                "message": "Email успешно отправлен"
            })
        else:
            current_app.logger.error(f"❌ [API] Ошибка при отправке email для задачи {task_id}")
            return jsonify({
                "success": False,
                "error": "Ошибка при отправке email"
            }), 500

    except Exception as e:
        current_app.logger.error(f"💥 [API] Критическая ошибка при отправке email для задачи {task_id}: {e}")
        current_app.logger.error(f"   Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"   Тип ошибки: {type(e).__name__}")
        current_app.logger.error(f"   Детали ошибки: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500
