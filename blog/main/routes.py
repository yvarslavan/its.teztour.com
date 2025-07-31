import traceback
import os
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import pymysql.cursors
from datetime import datetime, timedelta, timezone, date
from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    jsonify,
    g,
    abort,
    current_app,
    Response
)
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
from blog import csrf
from sqlalchemy import or_, desc, text, inspect
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count
from config import get
from blog import db
from blog.utils.connection_monitor import check_database_connections, get_connection_health
from blog.models import Post, User, Notifications, NotificationsAddNotes, PushSubscription
from blog.user.forms import AddCommentRedmine
from blog.main.forms import IssueForm
from blog.notification_service import (
    get_notification_service,
    NotificationData,
    NotificationType,
    NotificationService
)
from mysql_db import (
    Issue,
    Status,
    Session,
    get_quality_connection,
    CustomValue,
    Tracker,
    QualitySession,
    execute_quality_query_safe,
    db_manager,
)
from redmine import (
    RedmineConnector,
    get_connection,
    convert_datetime_msk_format,
    get_property_name,
    get_status_name_from_id,
    get_project_name_from_id,
    get_user_full_name_from_id,
    get_priority_name_from_id,
    check_user_active_redmine,
    get_issues_redmine_author_id,
    save_and_get_filepath,
    generate_email_signature,
    get_count_notifications,
    get_count_notifications_add_notes,
    execute_query,
    generate_optimized_property_names,
)

from erp_oracle import (
    connect_oracle,
    db_host,
    db_port,
    db_service_name,
    db_user_name,
    db_password,
    get_user_erp_password,
)

from blog.utils.cache_manager import (
    CacheManager,
    TasksCacheOptimizer,
    cached_response,
    weekend_performance_optimizer
)

# Импорты из blog.tasks.utils
from blog.tasks.utils import get_redmine_connector, get_user_assigned_tasks_paginated_optimized, task_to_dict
from concurrent.futures import ThreadPoolExecutor



cache_manager = CacheManager()
tasks_cache_optimizer = TasksCacheOptimizer()

main = Blueprint("main", __name__)

@main.app_template_filter('format_datetime')
def format_datetime_filter(value):
    """Jinja2 filter to format datetime objects or ISO strings into human-readable format."""
    if not value:
        return ""

    try:
        # Ensure we have a datetime object
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
        else:
            dt = value

        # Ensure the datetime is naive for comparison with datetime.now()
        if dt.tzinfo:
            dt = dt.astimezone(None).replace(tzinfo=None)

        now = datetime.now()
        diff = now - dt

        seconds = int(diff.total_seconds())

        if seconds < 5:
            return "Только что"
        if seconds < 60:
            return f"{seconds} сек назад"
        if seconds < 3600: # less than an hour
            minutes = seconds // 60
            return f"{minutes} мин назад"
        if seconds < 86400: # less than a day
            hours = seconds // 3600
            return f"{hours} ч назад"
        if seconds < 172800: # less than 2 days
            return "Вчера"

        return dt.strftime('%d.%m.%Y')

    except (ValueError, TypeError) as e:
        # Fallback for unexpected formats
        logger.warning(f"Could not format datetime value '{value}'. Error: {e}")
        return str(value)


MY_TASKS_REDIRECT = "main.my_tasks"

# ИСПРАВЛЕНИЕ: Функция configure_blog_logger перенесена в blog.utils.logger для избежания циклического импорта
logger = logging.getLogger(__name__) # Локальный логгер для текущего модуля


config = ConfigParser()
config_path = os.path.join(os.getcwd(), "config.ini")
config.read(config_path)
redmine_url = config.get("redmine", "url")
redmine_api_key = config.get("redmine", "api_key")
redmine_login_admin = config.get("redmine", "login_admin")
redmine_password_admin = config.get("redmine", "password_admin")
ANONYMOUS_USER_ID = int(config.get("redmine", "anonymous_user_id"))

DB_REDMINE_HOST = config.get("mysql", "host")
DB_REDMINE_DB = config.get("mysql", "database")
DB_REDMINE_USER = config.get("mysql", "user")
DB_REDMINE_PASSWORD = config.get("mysql", "password")

# Глобальная переменная для хранения статуса подключения
db_connection_status = {
    'connected': False,
    'last_check': None,
    'error': None
}

@main.before_request
def set_current_user():
    g.current_user = current_user if current_user.is_authenticated else None


def get_total_notification_count(user):
    """Подсчет общего количества уведомлений для пользователя.

    Теперь используем NotificationService для получения полного
    количества, включая Redmine-уведомления. Если по какой-то причине
    сервис недоступен, gracefully откатываемся к старой логике с двумя
    локальными таблицами, чтобы не сломать функциональность.
    """

    if user is None:
        return 0

    try:
        service = get_notification_service()
        data = service.get_user_notifications(user.id)
        # Требуемое поле total_count уже агрегирует все типы уведомлений.
        return data.get('total_count', 0)
    except Exception as e:
        # Логируем предупреждение и возвращаем подсчёт по старой схеме
        logger.warning(
            "Не удалось получить total_count из NotificationService: %s. "
            "Fallback к get_count_notifications().", str(e)
        )
        return get_count_notifications(user.id) + get_count_notifications_add_notes(user.id)


def get_total_notification_count_for_page(user):
    """Подсчет общего количества уведомлений для страницы /notifications (включая прочитанные)"""
    if user is None:
        return 0

    try:
        service = get_notification_service()
        data = service.get_notifications_for_page(user.id)
        # Возвращаем total_count который включает все уведомления (и прочитанные, и непрочитанные)
        return data.get('total_count', 0)
    except Exception as e:
        logger.warning(
            "Не удалось получить total_count для страницы из NotificationService: %s. "
            "Fallback к прямому подсчёту.", str(e)
        )
        # Fallback: считаем все уведомления напрямую из базы
        from blog.models import Notifications, NotificationsAddNotes, RedmineNotification
        status_count = Notifications.query.filter_by(user_id=user.id).count()
        comment_count = NotificationsAddNotes.query.filter_by(user_id=user.id).count()
        redmine_count = RedmineNotification.query.filter_by(user_id=user.id).count()
        return status_count + comment_count + redmine_count


# Использование в контекстном процессоре
@main.context_processor
def inject_notification_count():
    # ИЗМЕНЕНО: Теперь везде показываем все уведомления для согласованности
    user = g.current_user if hasattr(g, "current_user") else None
    count = get_total_notification_count_for_page(user)

    # Для страницы /notifications тот же счётчик
    page_count = 0
    if request.endpoint == 'main.my_notifications':
        page_count = count  # Используем тот же счетчик

    return dict(count_notifications=count, count_notifications_page=page_count)


@main.route("/get-notification-count", methods=["GET"])
@login_required
def get_notification_count():
    try:
        logger.info(f"🔄 Запрос количества уведомлений для пользователя {current_user.username}")

        # ИЗМЕНЕНО: Используем get_total_notification_count_for_page для показа всех уведомлений
        # чтобы красный счетчик был согласован со страницей /notifications
        count = get_total_notification_count_for_page(current_user)

        logger.info(f"✅ Получено количество уведомлений: {count}")
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"❌ Ошибка в get_notification_count: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({"count": 0, "error": str(e)}), 500


@main.route("/api/notifications/poll", methods=["GET"])
@login_required
def poll_notifications():
    """API для опроса уведомлений (для JavaScript)"""
    try:
        from datetime import datetime

        logger.info(f"🔄 Запрос уведомлений для пользователя {current_user.username}")

        # Получаем уведомления пользователя (теперь включая Redmine)
        notifications_data = get_notification_service().get_user_notifications(current_user.id)

        logger.info(f"✅ Получены уведомления: {notifications_data.get('total_count', 0)} шт.")

        # Формируем ответ в ожидаемом формате
        response_data = {
            'success': True,
            'notifications': {
                'status_notifications': notifications_data['status_notifications'],
                'comment_notifications': notifications_data['comment_notifications'],
                'redmine_notifications': notifications_data['redmine_notifications']  # НОВОЕ
            },
            'timestamp': datetime.now().isoformat(),
            'total_count': notifications_data['total_count']
        }

        logger.info(f"✅ API уведомлений успешно завершён")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка при опросе уведомлений: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'notifications': {
                'status_notifications': [],
                'comment_notifications': [],
                'redmine_notifications': []  # НОВОЕ
            },
            'timestamp': datetime.now().isoformat(),
            'total_count': 0
        }), 500


@main.route("/check-connection", methods=["GET"])
@login_required
def check_connection():
    """API для проверки соединения с базой данных"""
    try:
        # Простая проверка - пытаемся получить количество уведомлений
        count = get_total_notification_count(current_user)
        return jsonify({
            'connected': True,
            'status': 'ok'
        })
    except Exception as e:
        logger.error(f"Ошибка соединения с БД: {e}")
        return jsonify({
            'connected': False,
            'status': 'error',
            'error': str(e)
        })


@main.route("/get-my-tasks-paginated", methods=["GET"])
@login_required
def get_my_tasks_paginated():
    """API для получения задач с пагинацией (перенаправление на новый модуль tasks)"""
    try:
        # Проверяем, является ли пользователь пользователем Redmine
        if not current_user.is_redmine_user:
            return jsonify({
                "success": False,
                "error": "У вас нет доступа к модулю 'Мои задачи'. Этот раздел доступен только для пользователей Redmine.",
                "tasks": [],
                "pagination": {
                    "page": 1,
                    "per_page": 25,
                    "total": 0,
                    "total_display_records": 0
                }
            }), 403

        # Получаем параметры DataTables
        draw = request.args.get('draw', 1, type=int)
        page = request.args.get("start", 0, type=int) // request.args.get("length", 25, type=int) + 1
        per_page = request.args.get("length", 25, type=int)
        search_term = request.args.get("search[value]", "", type=str).strip()

        order_column_index = request.args.get('order[0][column]', 0, type=int)
        order_column_name_dt = request.args.get(f'columns[{order_column_index}][data]', 'updated_on', type=str)
        sort_direction = request.args.get('order[0][dir]', 'desc', type=str)

        # Сопоставление имен столбцов DataTables с полями Redmine
        column_mapping = {
            'id': 'id',
            'subject': 'subject',
            'status_name': 'status.name',
            'priority_name': 'priority.name',
            'updated_on': 'updated_on',
            'created_on': 'created_on',
            'start_date': 'start_date'
        }
        sort_column = column_mapping.get(order_column_name_dt, 'updated_on')

        # Получаем фильтры
        status_ids = [x for x in request.args.getlist('status_id[]') if x]  # Убираем пустые значения
        project_ids = [x for x in request.args.getlist('project_id[]') if x]
        priority_ids = [x for x in request.args.getlist('priority_id[]') if x]

        logger.info(f"API пагинации - параметры: draw={draw}, page={page}, per_page={per_page}, search_term='{search_term}'")
        logger.info(f"Фильтры из запроса: status_ids={status_ids}, project_ids={project_ids}, priority_ids={priority_ids}")

        # Получаем коннектор Redmine
        from erp_oracle import connect_oracle, get_user_erp_password, db_host, db_port, db_service_name, db_user_name, db_password
        oracle_conn = connect_oracle(db_host, db_port, db_service_name, db_user_name, db_password)
        if not oracle_conn:
            return jsonify({
                "success": False,
                "error": "Ошибка подключения к Oracle для получения пароля Redmine.",
                "tasks": [],
                "pagination": {"page": page, "per_page": per_page, "total": 0, "total_display_records": 0}
            }), 500

        user_password_erp = get_user_erp_password(oracle_conn, current_user.username)
        if not user_password_erp:
            return jsonify({
                "success": False,
                "error": "Не удалось получить пароль пользователя Redmine из ERP.",
                "tasks": [],
                "pagination": {"page": page, "per_page": per_page, "total": 0, "total_display_records": 0}
            }), 500

        actual_password = user_password_erp[0] if isinstance(user_password_erp, tuple) else user_password_erp

        # Создаем коннектор
        redmine_connector = get_redmine_connector(current_user, actual_password)
        if not redmine_connector or not hasattr(redmine_connector, 'redmine') or not redmine_connector.redmine:
            return jsonify({
                "success": False,
                "error": "Не удалось создать коннектор Redmine.",
                "tasks": [],
                "pagination": {"page": page, "per_page": per_page, "total": 0, "total_display_records": 0}
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_obj = redmine_connector.redmine.user.get('current')
        redmine_user_id = redmine_user_obj.id

        # Получаем задачи
        issues_list, total_count = get_user_assigned_tasks_paginated_optimized(
            redmine_connector,
            redmine_user_id,
            page=page,
            per_page=per_page,
            search_term=search_term,
            sort_column=sort_column,
            sort_direction=sort_direction,
            status_ids=status_ids,
            project_ids=project_ids,
            priority_ids=priority_ids
        )

        # Преобразуем задачи в словари
        tasks_data = [task_to_dict(issue) for issue in issues_list]

        # Возвращаем формат DataTables
        return jsonify({
            "draw": draw,
            "recordsTotal": total_count,
            "recordsFiltered": total_count,
            "data": tasks_data
        })

    except Exception as e:
        logger.error(f"Ошибка в get_my_tasks_paginated: {e}")
        return jsonify({
            "draw": request.args.get('draw', 1, type=int),
            "error": str(e),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }), 500


@main.route("/get-my-tasks-statistics-optimized", methods=["GET"])
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

        # Получаем коннектор Redmine
        from erp_oracle import connect_oracle, get_user_erp_password, db_host, db_port, db_service_name, db_user_name, db_password
        oracle_conn = connect_oracle(db_host, db_port, db_service_name, db_user_name, db_password)
        if not oracle_conn:
            return jsonify({
                "error": "Ошибка подключения к Oracle",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500

        user_password_erp = get_user_erp_password(oracle_conn, current_user.username)
        if not user_password_erp:
            return jsonify({
                "error": "Не удалось получить пароль пользователя",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500

        actual_password = user_password_erp[0] if isinstance(user_password_erp, tuple) else user_password_erp
        redmine_connector = get_redmine_connector(current_user, actual_password)

        if not redmine_connector or not hasattr(redmine_connector, 'redmine'):
            return jsonify({
                "error": "Не удалось создать коннектор Redmine",
                "total_tasks": 0,
                "new_tasks": 0,
                "in_progress_tasks": 0,
                "closed_tasks": 0
            }), 500

        # Получаем ID пользователя Redmine
        redmine_user_obj = redmine_connector.redmine.user.get('current')
        redmine_user_id = redmine_user_obj.id

        # Получаем статистику задач
        all_issues = redmine_connector.redmine.issue.filter(assigned_to_id=redmine_user_id, limit=1000)

        total_tasks = 0
        new_tasks = 0
        in_progress_tasks = 0
        closed_tasks = 0

        # Получаем все статусы для корректной классификации
        redmine_statuses = redmine_connector.redmine.issue_status.all()
        status_mapping = {}

        for status in redmine_statuses:
            status_name_lower = status.name.lower()
            logger.debug(f"Классификация статуса: '{status.name}' (ID: {status.id}) -> '{status_name_lower}'")

            # NEW (новые задачи)
            if any(keyword in status_name_lower for keyword in ['новая', 'новый', 'new', 'создан', 'создана', 'открыта', 'открыт', 'в очереди', 'очереди']):
                status_mapping[status.id] = 'new'
                logger.debug(f"Статус '{status.name}' классифицирован как NEW")
            # CLOSED (завершенные задачи)
            elif any(keyword in status_name_lower for keyword in ['закрыт', 'закрыта', 'closed', 'отклонена', 'отклонен', 'перенаправлена', 'перенаправлен']):
                status_mapping[status.id] = 'closed'
                logger.debug(f"Статус '{status.name}' классифицирован как CLOSED")
            # IN_PROGRESS (все остальные - задачи в процессе работы)
            else:
                status_mapping[status.id] = 'in_progress'
                logger.debug(f"Статус '{status.name}' классифицирован как IN_PROGRESS")

        for issue in all_issues:
            total_tasks += 1
            status_id = issue.status.id if hasattr(issue, 'status') and issue.status else None
            status_name = issue.status.name if hasattr(issue, 'status') and issue.status else "Unknown"
            status_category = status_mapping.get(status_id, 'other')

            logger.debug(f"Задача #{issue.id}: статус '{status_name}' (ID: {status_id}) -> категория '{status_category}'")

            if status_category == 'new':
                new_tasks += 1
            elif status_category == 'in_progress':
                in_progress_tasks += 1
            elif status_category == 'closed':
                closed_tasks += 1

        # Создаем детальную статистику для модального окна
        debug_status_counts = {}
        additional_stats = {
            "avg_completion_time": "Не определено",
            "most_active_project": "Не определено",
            "completion_rate": 0
        }

        # Подсчитываем статистику по статусам
        for issue in all_issues:
            status_name = issue.status.name if hasattr(issue, 'status') and issue.status else "Неизвестно"
            if status_name in debug_status_counts:
                debug_status_counts[status_name] += 1
            else:
                debug_status_counts[status_name] = 1

        # Вычисляем процент завершения
        if total_tasks > 0:
            additional_stats["completion_rate"] = round((closed_tasks / total_tasks) * 100, 1)

        # Логируем итоговую статистику
        logger.info(f"СТАТИСТИКА для {current_user.username}: ВСЕГО={total_tasks}, НОВЫХ={new_tasks}, В РАБОТЕ={in_progress_tasks}, ЗАКРЫТЫХ={closed_tasks}")

        return jsonify({
            "success": True,
            "total_tasks": total_tasks,
            "new_tasks": new_tasks,
            "in_progress_tasks": in_progress_tasks,
            "closed_tasks": closed_tasks,
            "statistics": {
                "debug_status_counts": debug_status_counts,
                "additional_stats": additional_stats,
                "focused_data": {
                    "total": {
                        "additional_stats": additional_stats,
                        "status_breakdown": debug_status_counts
                    },
                    "new": {
                        "debug_status_counts": debug_status_counts,
                        "filter_description": f"Отображены задачи со статусом 'Новый' или 'New'"
                    },
                    "progress": {
                        "debug_status_counts": debug_status_counts,
                        "filter_description": f"Отображены задачи в статусе 'В работе' или 'Progress'"
                    },
                    "closed": {
                        "debug_status_counts": debug_status_counts,
                        "filter_description": f"Отображены завершенные задачи"
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



@main.route("/notifications-polling", methods=["GET"])
@login_required
def notifications_polling():
    """Страница тестирования уведомлений"""
    return render_template("notifications_polling.html", title="Тестирование уведомлений")


@main.route("/sw.js", methods=["GET"])
def service_worker():
    """Обслуживает Service Worker файл из корня"""
    from flask import send_from_directory
    return send_from_directory('static/js', 'sw.js', mimetype='application/javascript')


@main.route("/api/notifications/widget/status", methods=["GET"])
@login_required
def notifications_widget_status():
    """API для получения статуса виджета уведомлений"""
    try:
        # Возвращаем настройки виджета с enabled: true для включения
        return jsonify({
            "success": True,
            "enabled": True,  # ВАЖНО: ключ enabled для проверки в JavaScript
            "widget_enabled": True,
            "position": "bottom-right",
            "sound_enabled": True,
            "notifications_enabled": True,
            "polling_interval": 30000,  # 30 секунд
            "widget_settings": {
                "position": "bottom-right",
                "theme": "light",
                "auto_hide": False,
                "show_counter": True
            }
        })
    except Exception as e:
        logger.error(f"Ошибка в notifications_widget_status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "enabled": False,
            "widget_enabled": False
        }), 500


@main.route("/api/notifications/clear", methods=["POST"])
@login_required
def api_clear_notifications():
    """API эндпоинт для очистки всех уведомлений пользователя."""
    try:
        # ИСПРАВЛЕНО: Используем get_notification_service() для получения синглтона
        service = get_notification_service()
        success = service.clear_user_notifications(current_user.id)
        if success:
            logger.info(f"Все уведомления для пользователя {current_user.id} успешно очищены.")
            return jsonify({'success': True})
        else:
            logger.error(f"Не удалось очистить уведомления для пользователя {current_user.id} на стороне сервиса.")
            return jsonify({'success': False, 'error': 'Не удалось выполнить операцию в базе данных Redmine'}), 500
    except Exception as e:
        logger.critical(f"Критическая ошибка при очистке уведомлений для пользователя {current_user.id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Неизвестная критическая ошибка на сервере'}), 500


@main.route("/api/notifications/redmine/mark-read", methods=["POST"])
@login_required
def api_mark_redmine_notification_read():
    """API для отметки Redmine уведомления как прочитанного"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        if not notification_id:
            return jsonify({'success': False, 'error': 'notification_id is required'})

        # Используем NotificationService для отметки как прочитанного
        success = get_notification_service().mark_redmine_notification_as_read(current_user.id, notification_id)

        if success:
            return jsonify({'success': True, 'message': 'Уведомление отмечено как прочитанное'})
        else:
            return jsonify({'success': False, 'error': 'Уведомление не найдено или уже прочитано'})

    except Exception as e:
        current_app.logger.error(f"Ошибка при отметке Redmine уведомления как прочитанного: {str(e)}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})


@main.route("/api/notifications/mark-all-read", methods=["POST"])
@login_required
def api_mark_all_notifications_read():
    """API для отметки всех уведомлений как прочитанных (для кнопки Очистить в виджете)"""
    try:
        # Используем NotificationService для отметки всех уведомлений как прочитанных
        success = get_notification_service().mark_all_notifications_as_read(current_user.id)

        if success:
            return jsonify({'success': True, 'message': 'Все уведомления отмечены как прочитанные'})
        else:
            return jsonify({'success': False, 'error': 'Ошибка при отметке уведомлений как прочитанных'})

    except Exception as e:
        current_app.logger.error(f"Ошибка при отметке всех уведомлений как прочитанных: {str(e)}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})


@main.route("/api/notifications/mark-read", methods=["POST"])
@login_required
def api_mark_notification_read():
    """API для отметки уведомлений заявок как прочитанных"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        notification_type = data.get('notification_type')

        if not notification_id or not notification_type:
            return jsonify({'success': False, 'error': 'notification_id and notification_type are required'})

        # Извлекаем реальный ID из составного ID (например, "status_123" -> 123)
        if '_' in str(notification_id):
            real_id = str(notification_id).split('_')[1]
        else:
            real_id = notification_id

        try:
            real_id = int(real_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid notification_id format'})

        if notification_type == 'status-change':
            # Отмечаем уведомление об изменении статуса как прочитанное
            notification = Notifications.query.filter_by(
                id=real_id,
                user_id=current_user.id
            ).first()

            if not notification:
                # Попытка найти без user_id (на случай рассинхронизации)
                notification = Notifications.query.filter_by(id=real_id).first()

            if notification and (notification.is_read is None or notification.is_read is False):
                notification.is_read = True
                db.session.commit()
                return jsonify({'success': True, 'message': 'Уведомление об изменении статуса отмечено как прочитанное'})
            else:
                return jsonify({'success': False, 'error': 'Уведомление не найдено или уже прочитано'})

        elif notification_type == 'comment':
            # Отмечаем уведомление о комментарии как прочитанное
            notification = NotificationsAddNotes.query.filter_by(
                id=real_id,
                user_id=current_user.id
            ).first()

            if not notification:
                notification = NotificationsAddNotes.query.filter_by(id=real_id).first()

            if notification and (notification.is_read is None or notification.is_read is False):
                notification.is_read = True
                db.session.commit()
                return jsonify({'success': True, 'message': 'Уведомление о комментарии отмечено как прочитанное'})
            else:
                return jsonify({'success': False, 'error': 'Уведомление не найдено или уже прочитано'})
        else:
            return jsonify({'success': False, 'error': 'Неподдерживаемый тип уведомления'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при отметке уведомления как прочитанного: {str(e)}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})


@main.route("/api/notifications/redmine/clear", methods=["POST"])
@login_required
def api_clear_redmine_notifications():
    """API для очистки всех Redmine уведомлений пользователя"""
    try:
        # Получаем подключение к MySQL Redmine
        connection = get_connection(
            DB_REDMINE_HOST,
            DB_REDMINE_USER,
            DB_REDMINE_PASSWORD,
            DB_REDMINE_DB
        )

        if not connection:
            return jsonify({
                "success": False,
                "error": "Ошибка подключения к базе данных"
            }), 500

        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE u_redmine_notifications SET is_read = 1 WHERE user_id = %s",
                (current_user.id,)
            )
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()

            logger.info(f"Очищено {affected_rows} Redmine уведомлений для пользователя {current_user.id}")
            return jsonify({
                "success": True,
                "message": f"Очищено {affected_rows} уведомлений Redmine"
            })

        finally:
            connection.close()

    except Exception as e:
        logger.error(f"Ошибка очистки Redmine уведомлений: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@main.route("/")
@main.route("/home")
@main.route("/index")
def home():
    return render_template("index.html", title="Главная")


@main.route("/my-issues", methods=["GET"])
@login_required
def my_issues():
    try:
        # Проверяем уведомления только если пользователь аутентифицирован
        if current_user.is_authenticated:
            # check_notifications(g.current_user.email, g.current_user.id) # ЗАКОММЕНТИРОВАНО
            logger.info(f"Вызов check_notifications ЗАКОММЕНТИРОВАН для пользователя {g.current_user.id} в /my-issues")
        return render_template("issues.html", title="Мои заявки")
    except Exception as e:
        current_app.logger.error(f"Error in my_issues: {str(e)}")
        flash("Произошла ошибка при загрузке заявок", "error")
        return redirect(url_for("main.index"))


@main.route("/debug-statuses", methods=["GET"])
@login_required
def debug_statuses():
    """Отладочная страница для проверки статусов"""
    if not current_user.is_redmine_user:
        flash("У вас нет доступа к этому разделу", "warning")
        return redirect(url_for("main.home"))

    import os
    debug_file_path = os.path.join(os.getcwd(), 'debug_statuses.html')
    with open(debug_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

@main.route("/test-filters-api", methods=["GET"])
@login_required
def test_filters_api():
    """Тестовая страница для проверки API фильтров"""
    if not current_user.is_redmine_user:
        flash("У вас нет доступа к этому разделу", "warning")
        return redirect(url_for("main.home"))

    import os
    test_file_path = os.path.join(os.getcwd(), 'test_filters_api.html')
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

@main.route("/simple-api-test", methods=["GET"])
@login_required
def simple_api_test():
    """Простая тестовая страница для проверки базового API"""
    if not current_user.is_redmine_user:
        flash("У вас нет доступа к этому разделу", "warning")
        return redirect(url_for("main.home"))

    import os
    test_file_path = os.path.join(os.getcwd(), 'simple_api_test.html')
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


@main.route("/get-my-issues", methods=["GET"])
@login_required
def get_my_issues():
    # Проверяем параметр кеширования
    use_cached = request.args.get('cached', '0') == '1'

    if use_cached:
        # Возвращаем сигнал клиенту использовать кеш
        return jsonify({"use_cached_data": True})
    with Session() as session:
        conn = get_connection(
            DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
        )
        if conn is None:
            flash(
                "Ошибка подключения к HelpDesk (Easy Redmine). Проверьте ваше VPN соединение",
                "danger",
            )
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        check_user_redmine = check_user_active_redmine(conn, current_user.email)

        # Получаем все возможные статусы
        statuses = session.query(Status).all()
        status_list = [{"id": status.id, "name": status.name} for status in statuses]

        if check_user_redmine == ANONYMOUS_USER_ID:
            issues_data = get_issues_by_email(session, current_user.email)
        else:
            issues_data = get_issues_redmine_author_id(
                conn, check_user_redmine, current_user.email
            )

        return jsonify(
            {
                "issues": issues_data,
                "statuses": status_list,  # Добавляем список всех статусов
            }
        )


def get_issues_by_email(session, email):
    filtered_issues = (
        session.query(Issue)
        .options(joinedload(Issue.status))
        .join(Status, Issue.status_id == Status.id)
        .filter(
            or_(
                Issue.easy_email_to == email,
                Issue.easy_email_to
                == email.replace("@tez-tour.com", "@msk.tez-tour.com"),
            )
        )
        .order_by(desc(Issue.updated_on))
        .all()
    )
    return [
        {
            "id": issue.id,
            "updated_on": issue.updated_on.isoformat(),
            "subject": issue.subject,
            "status_name": issue.status.name,
            "status_id": issue.status_id,  # Добавляем ID статуса
        }
        for issue in filtered_issues
    ]


@main.route("/blog", methods=["POST", "GET"])
@login_required
def blog():
    all_posts = Post.query.order_by(Post.title.desc()).all()
    all_users = User.query.all()
    # Определение текущей страницы
    page = request.args.get("page", 1, type=int)
    # Получение постов с пагинацией
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=9)
    # Рендер шаблона с постами и объектом пагинации
    return render_template(
        "blog.html",
        title="Все статьи",
        posts=posts,
        all_posts=all_posts,
        all_users=all_users,
    )


# REDIRECT: /my-tasks/ -> /tasks/my-tasks/ (для совместимости)
@main.route("/my-tasks", methods=["GET"])
@login_required
def my_tasks_redirect():
    """Перенаправление со старого URL на новый tasks blueprint"""
    return redirect(url_for('tasks.my_tasks_page'))

@main.route("/my-tasks/<int:task_id>", methods=["GET"])
@login_required
def task_detail_redirect(task_id):
    """Перенаправление со старого URL детализации на новый tasks blueprint"""
    return redirect(url_for('tasks.task_detail', task_id=task_id))

@main.route("/my-issues/<int:issue_id>", methods=["GET", "POST"])
@login_required
def issue(issue_id):
    """Оптимизированный вывод истории заявки с минимальными подключениями к БД"""
    form = AddCommentRedmine()

    # === ЭТАП 1: Подключения к внешним системам ===
    logger.info(f"Загрузка заявки #{issue_id} для пользователя {current_user.id}")
    start_time = time.time()

    # Подключение к Oracle (для получения пароля пользователя)
    oracle_connect_instance = connect_oracle(
        db_host, db_port, db_service_name, db_user_name, db_password
    )

    user_password_erp = get_user_erp_password(oracle_connect_instance, current_user.username)
    if not oracle_connect_instance or not user_password_erp:
        flash("Не удалось подключиться к базе данных Oracle или получить пароль пользователя для Redmine.", "error")
        return redirect(url_for("main.my_issues"))

    # Получаем пароль пользователя
    actual_user_password = user_password_erp[0] if isinstance(user_password_erp, tuple) else user_password_erp

    # === ЭТАП 2: Создание Redmine коннектора ===
    redmine_connector_user = get_redmine_connector(current_user, actual_user_password)

    if not redmine_connector_user or not hasattr(redmine_connector_user, 'redmine'):
        flash("Не удалось создать пользовательский коннектор Redmine.", "error")
        current_app.logger.error(f"Не удалось создать redmine_connector_user для {current_user.username}")
        return redirect(url_for("main.my_issues"))

    # === ЭТАП 3: Загрузка данных заявки ===
    issue_detail_obj = None
    attachment_list = []
    issue_history = None

    try:
        # Загружаем основные данные задачи
        issue_detail_obj = redmine_connector_user.redmine.issue.get(
            issue_id,
            include=['attachments', 'journals']
        )

        # Получаем вложения
        if hasattr(issue_detail_obj, 'attachments'):
            attachment_list = issue_detail_obj.attachments

        # Получаем историю изменений
        issue_history = redmine_connector_user.get_issue_history(issue_id)

    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке задачи #{issue_id}: {e}")
        flash(f"Не удалось загрузить задачу #{issue_id}.", "error")
        return redirect(url_for("main.my_issues"))

    # === ЭТАП 4: КРИТИЧЕСКАЯ ОПТИМИЗАЦИЯ - Предзагрузка данных для истории ===
    property_descriptions = {}
    redmine_connection = None

    if issue_history:
        try:
            # Создаем ОДНО соединение для всех операций с БД
            redmine_connection = get_connection(
                DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
            )

            if redmine_connection:
                # Используем оптимизированную функцию для пакетной загрузки
                property_descriptions = generate_optimized_property_names(
                    redmine_connection, issue_history
                )
                logger.info(f"Предзагружено {len(property_descriptions)} описаний изменений")
            else:
                logger.warning("Не удалось создать соединение с Redmine DB для оптимизации")

        except Exception as e:
            logger.error(f"Ошибка при предзагрузке данных для истории: {e}")
        finally:
            if redmine_connection:
                redmine_connection.close()

    # === ЭТАП 5: Обработка формы комментария ===
    if form.validate_on_submit() and handle_comment_submission(
        form, issue_id, redmine_connector_user
    ):
        return redirect(url_for("main.issue", issue_id=issue_id))

    # === ЭТАП 6: Рендеринг шаблона с предзагруженными данными ===
    end_time = time.time()
    logger.info(f"Заявка #{issue_id} загружена за {end_time - start_time:.2f} сек")

    return render_template(
        "issue.html",
        title=f"#{issue_detail_obj.id} - {issue_detail_obj.subject}",
        issue_detail=issue_detail_obj,
        issue_history=issue_history,
        attachment_list=attachment_list,
        form=form,
        clear_comment=True,
        convert_datetime_msk_format=convert_datetime_msk_format,
        # КРИТИЧНО: Передаем предзагруженные данные вместо функций
        property_descriptions=property_descriptions,
        # НЕ передаем функции get_property_name и другие!
        # get_property_name=get_property_name,  # УДАЛИТЬ ЭТУ СТРОКУ!
        # get_status_name_from_id=get_status_name_from_id,  # УДАЛИТЬ!
        # get_project_name_from_id=get_project_name_from_id,  # УДАЛИТЬ!
        # get_user_full_name_from_id=get_user_full_name_from_id,  # УДАЛИТЬ!
        # get_priority_name_from_id=get_priority_name_from_id,  # УДАЛИТЬ!
        # get_connection=get_connection,  # УДАЛИТЬ!
    )




def handle_comment_submission(form, issue_id, redmine_connector):
    """Обработка добавления комментария.
    Для пользователей Redmine используем их ID, для остальных - анонимный ID.
    """
    comment = form.comment.data

    # Для пользователей Redmine используем их ID, для остальных - анонимный ID
    if current_user.is_redmine_user and hasattr(current_user, 'id_redmine_user') and current_user.id_redmine_user:
        user_id = current_user.id_redmine_user
    else:
        user_id = ANONYMOUS_USER_ID

    current_app.logger.info(f"[handle_comment_submission] Добавление комментария с user_id: {user_id}")
    success, message = redmine_connector.add_comment(
        issue_id=issue_id, notes=comment, user_id=user_id
    )

    if success:
        flash("Комментарий успешно добавлен в задачу!", "success")
        return True
    flash(message, "danger")
    return False



@main.route("/my-issues/new", methods=["GET", "POST"])
@login_required
def new_issue():
    form = IssueForm()
    user_data = {
        "full_name": current_user.full_name,
        "position": current_user.position,
        "department": current_user.department,
        "phone": current_user.phone,
        "email": current_user.email,
    }
    temp_file_path = None
    if form.validate_on_submit():
        # Получаем значение атрибутов из формы
        subject = form.subject.data
        description = form.description.data
        email_signature_html = generate_email_signature(user_data)
        description_with_signature = f"{description}<br><br>{email_signature_html}"
        # Получаем файл как объект
        filedata = form.upload_files.data
        if filedata[0].filename != "":
            # Сохраняем файл во временной папке на диске и получаем путь к нему
            temp_file_path = save_and_get_filepath(filedata)
        else:
            # Действия, если файл не был прикреплен
            temp_file_path = None
        # Проверяем, тек. пользователь пользователь имеет акааунт в Redmine?
        oracle_connect = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )
        current_user_password_erp = get_user_erp_password(
            oracle_connect, current_user.username
        )
        if current_user_password_erp is not None:
            redmine_connector = RedmineConnector(
                url=redmine_url,
                username=current_user.username,
                password=current_user_password_erp[0],
                api_key=None,
            )
        else:
            # Обработка ситуации, когда пароль не был получен
            # Создаем redmine_connector с пустым паролем как Аноним
            redmine_connector = RedmineConnector(
                url=redmine_url, username=None, password=None, api_key=redmine_api_key
            )

        if redmine_connector.is_user_authenticated():
            author_result = redmine_connector.get_current_user("current")
            # Извлекаем объект пользователя из кортежа (success, user_object)
            author_id = author_result[1] if isinstance(author_result, tuple) and author_result[0] else author_result
            # Если это пользователь Redmine cоздаем заявку в Redmine от имени (Автора) этого пользователя Redmine
            success_create_issue = redmine_connector.create_issue(
                subject=subject,
                description=description_with_signature,
                project_id=1,  # Входящие (Москва)
                author_id=author_id.id,  # type: ignore
                easy_email_to=current_user.email,
                file_path=temp_file_path,
            )
            if success_create_issue:
                # Выводим сообщение об успешном добавлении задачи в Redmine
                flash("Задача успешно добавлена в HelpDesk (EasyRedmine)!", "success")
                return redirect(url_for("main.my_issues"))
            if temp_file_path is not None:
                # Удаляем этот временный сохраненый файл
                if isinstance(temp_file_path, list) and temp_file_path:
                    os.remove(temp_file_path[0])  # type: ignore
                else:
                    os.remove(temp_file_path)  # type: ignore
        else:
            # Если это не пользователь Redmine, авторизуемся в Redmine по api ключу как Аноним
            redmine_connector = RedmineConnector(
                url=redmine_url, username=None, password=None, api_key=redmine_api_key
            )
            success_create_issue = redmine_connector.create_issue(
                subject=subject,
                description=description_with_signature,
                project_id=1,  # Входящие (Москва)
                file_path=temp_file_path,
                author_id=4,  # Аноним
                easy_email_to=current_user.email,
            )
            if success_create_issue:
                # Выводим сообщение об успешном добавлении задачи в Redmine
                flash("Задача успешно добавлена в HelpDesk (EasyRedmine)!", "success")
                return redirect(url_for("main.my_issues"))
            if temp_file_path is not None:
                # Удаляем этот временный сохраненный файл
                if isinstance(temp_file_path, list) and temp_file_path:
                    os.remove(temp_file_path[0])  # type: ignore
                else:
                    os.remove(temp_file_path)  # type: ignore

    return render_template("create_issue.html", title="Новая заявка", form=form)


@main.route("/notifications", methods=["GET"])
@login_required
def my_notifications():
    # ИСПРАВЛЕНО: Используем метод для страницы уведомлений (локальная база blog.db)
    notifications_data = get_notification_service().get_notifications_for_page(current_user.id)

    if notifications_data['total_count'] > 0:
        return render_template(
            "notifications.html",
            title="Уведомления",
            combined_notifications={
                'notifications_data': notifications_data['status_notifications'],
                'notifications_add_notes_data': notifications_data['comment_notifications'],
                'redmine_notifications_data': notifications_data['redmine_notifications']  # Из локальной базы
            }
        )
    return render_template("notifications.html", title="Уведомления", combined_notifications={})


@main.route("/clear-notifications", methods=["POST"])
@login_required
def clear_notifications():
    """Удаляем уведомления после нажатия кнопки 'Очистить уведомления'"""
    print(f"[DEBUG] clear_notifications вызван для пользователя: {current_user.id}")
    try:
        success = get_notification_service().clear_user_notifications(current_user.id)

        if success:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message="Уведомления успешно удалены")
            flash("Уведомления успешно удалены", "success")
        else:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, error="Ошибка при удалении уведомлений")
            flash("Ошибка при удалении уведомлений", "error")

    except Exception as e:
        print(f"[DEBUG] Ошибка при удалении: {str(e)}")
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error=str(e))
        flash(f"Ошибка при удалении уведомлений: {str(e)}", "error")
        logger.error(f"Ошибка при удалении всех уведомлений: {str(e)}")

    print(f"[DEBUG] Перенаправляем на страницу уведомлений")
    return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления об измнении статуса
@main.route("/delete_notification_status/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification_status(notification_id):
    print(f"[DEBUG] delete_notification_status called with ID: {notification_id}")
    print(f"[DEBUG] User ID: {current_user.id}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    print(f"[DEBUG] Request form data: {dict(request.form)}")
    print(f"[DEBUG] Is AJAX request: {request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")

    try:
        notification = Notifications.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True)
            flash("Уведомление успешно удалено", "success")
        else:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, error="Уведомление не найдено")
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error=str(e))
        flash(f"Ошибка при удалении уведомления: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


# Маршрут для удаления уведомления о добавлении комментария
@main.route("/delete_notification_add_notes/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification_add_notes(notification_id):
    print(f"[DEBUG] delete_notification_add_notes called with ID: {notification_id}")
    print(f"[DEBUG] User ID: {current_user.id}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    print(f"[DEBUG] Request form data: {dict(request.form)}")
    print(f"[DEBUG] Is AJAX request: {request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")

    try:
        notification = NotificationsAddNotes.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()

        if notification:
            db.session.delete(notification)
            db.session.commit()
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True)
            flash("Уведомление успешно удалено", "success")
        else:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, error="Уведомление не найдено")
            flash("Уведомление не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error=str(e))
        flash(f"Ошибка при удалении уведомления: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


@main.route("/delete_notification_redmine/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification_redmine(notification_id):
    print(f"[DEBUG] delete_notification_redmine called with ID: {notification_id}")
    print(f"[DEBUG] User ID: {current_user.id}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    print(f"[DEBUG] Request form data: {dict(request.form)}")
    print(f"[DEBUG] Is AJAX request: {request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")

    try:
        success = get_notification_service().delete_redmine_notification(notification_id, current_user.id)

        if success:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True)
            flash("Уведомление Redmine успешно удалено", "success")
        else:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, error="Уведомление Redmine не найдено")
            flash("Уведомление Redmine не найдено", "error")

        return redirect(url_for("main.my_notifications"))

    except Exception as e:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error=str(e))
        flash(f"Ошибка при удалении уведомления Redmine: {str(e)}", "error")
        return redirect(url_for("main.my_notifications"))


@main.route("/write_tech_support")
def write_tech_support():
    return render_template(
        "write_tech_support.html", title="Как написать в техподдержку"
    )


@main.route("/questionable_email")
def questionable_email():
    return render_template(
        "questionable_email.html", title="Получили подозрительное письмо?"
    )


@main.route("/ciscoanyconnect")
def ciscoanyconnect():
    return render_template(
        "ciscoanyconnect.html", title="Как пользоваться Cisco AnyConnect"
    )


@main.route("/setup_mail_account")
def setup_mail_account():
    return render_template(
        "setup_mail_account.html", title="Не получается настроить почту?"
    )


@main.route("/setup_mail_forwarding")
def setup_mail_forwarding():
    return render_template(
        "setup_mail_forwarding.html", title="Как переадресовать почту?"
    )


@main.route("/adress_book")
def adress_book():
    return render_template("address_book.html", title="Корпоративная адресная книга")


@main.route("/remote_connection")
def remote_connection():
    return render_template(
        "remote_connection.html", title="Удаленное подключение к Вам специалиста"
    )


@main.route("/no_access_site")
def no_access_site():
    return render_template("no_access_site.html", title="Веб-айты не загружаются?")


@main.route("/vacuum_setup")
def vacuum_setup():
    return render_template(
        "vacuum_setup.html", title="Как настроить аккаунт Vacuum-IM?"
    )


@main.route("/tez_cloud")
def tez_cloud():
    return render_template(
        "tez_cloud.html", title="Корпоративный файловый сервер CLOUD TEZ TOUR"
    )


@main.route("/auto_resp")
def auto_resp():
    return render_template("auto_resp.html", title="Настройка автоответчика почты")


@main.route("/vdi")
def vdi():
    return render_template(
        "vdi.html",
        title="Инструкция по подключению к виртуальному рабочему столу (VDI)",
    )


@main.route("/reports")
@login_required
def reports():
    try:
        config = ConfigParser()
        config_path = os.path.join(os.getcwd(), "config.ini")
        config.read(config_path)

        DB_REDMINE_HOST = config.get("mysql", "host")
        DB_REDMINE_DB = config.get("mysql", "database")
        DB_REDMINE_USER = config.get("mysql", "user")
        DB_REDMINE_PASSWORD = config.get("mysql", "password")

        conn = get_connection(
            DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
        )

        if conn is None:
            raise Exception("Не удалось подключиться к базе данных")

        session = Session()

        # Проверяем, является ли пользователь активным пользователем Redmine
        check_user_redmine = check_user_active_redmine(conn, current_user.email)

        # Получаем статистику по заявкам в зависимости от типа пользователя
        if check_user_redmine == ANONYMOUS_USER_ID:
            # Для анонимных пользователей используем фильтр по email
            issues_stats = (
                session.query(
                    Issue.status_id,
                    Status.name.label("status_name"),
                    count(Issue.id).label("count"),
                )
                .join(Status, Issue.status_id == Status.id)
                .filter(
                    or_(
                        Issue.easy_email_to == current_user.email,
                        Issue.easy_email_to
                        == current_user.email.replace(
                            "@tez-tour.com", "@msk.tez-tour.com"
                        ),
                    )
                )
                .group_by(Issue.status_id, Status.name)
                .all()
            )
        else:
            # Для пользователей Redmine используем фильтр по author_id или email
            issues_stats = (
                session.query(
                    Issue.status_id,
                    Status.name.label("status_name"),
                    count(Issue.id).label("count"),
                )
                .join(Status, Issue.status_id == Status.id)
                .filter(
                    or_(
                        Issue.author_id == check_user_redmine,
                        Issue.easy_email_to.like(f"%{current_user.email}%"),
                    )
                )
                .group_by(Issue.status_id, Status.name)
                .all()
            )

        # Подготавливаем данные для графиков
        labels = [stat.status_name for stat in issues_stats]
        data = [stat.count for stat in issues_stats]

        return render_template("reports.html", title="Статистика заявок", labels=labels, data=data) # Добавляем title

    except Exception as e:
        print("Ошибка в reports:", str(e))
        raise e
    finally:
        if "session" in locals():
            session.close()


@main.route("/status-demo")
def status_demo():
    """Демонстрационная страница для современных статусных индикаторов"""
    return render_template('status-demo.html', title="Демонстрация статусных индикаторов")


@main.route("/quality-control")
@login_required
def quality_control():
    try:
        session = get_quality_connection()
        if session is None:
            flash("Ошибка подключения к базе данных качества", "danger")
            return redirect(url_for("main.home"))

        # Получаем типы обращений для обоих отчетов
        request_types = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        session.close()
        return render_template(
            "quality_control.html",
            title="Контроль качества",
            request_types=request_types,  # Передаем типы обращений в шаблон
        )
    except Exception as e:
        flash(f"Произошла ошибка: {str(e)}", "danger")
        return redirect(url_for("main.home"))


@main.route("/get-assigned-to-values")
@login_required
def get_assigned_to_values():
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        values = (
            session.query(CustomValue.value)
            .filter(CustomValue.custom_field_id == 21)
            .distinct()
            .order_by(CustomValue.value)
            .all()
        )

        assigned_to_list = [value[0] for value in values if value[0]]

        session.close()
        return jsonify({"values": assigned_to_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/get-request-types")
@login_required
def get_request_types():
    try:
        logger.info("Starting request type fetch")
        session = get_quality_connection()
        if session is None:
            logger.error("Failed to establish database connection")
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Получаем список типов обращений с их ID
        trackers = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        request_types = [
            {"id": tracker.id, "name": tracker.name} for tracker in trackers
        ]
        logger.info(f"Successfully fetched {len(request_types)} request types")

        return jsonify({"values": request_types})
    except Exception as e:
        logger.error(f"Error in get_request_types: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if session is not None:
            session.close()


@main.route("/get-tracker-ids")
def get_tracker_ids():
    session = get_quality_connection()
    try:
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        trackers = (
            session.query(Tracker.id, Tracker.name)
            .filter(Tracker.default_status_id == 22)
            .order_by(Tracker.name)
            .all()
        )

        tracker_map = {
            "gratitude": next(
                (str(t.id) for t in trackers if t.name == "Благодарность"), ""
            ),
            "complaint": next((str(t.id) for t in trackers if t.name == "Жалоба"), ""),
            "question": next((str(t.id) for t in trackers if t.name == "Вопрос"), ""),
            "suggestion": next(
                (str(t.id) for t in trackers if t.name == "Предложение"), ""
            ),
        }

        return jsonify(tracker_map)
    finally:
        if session is not None:
            session.close()


@main.route("/get-classification-report", methods=["POST"])
@csrf.exempt
@login_required
def get_classification_report():
    session = None
    connection = None
    cursor = None
    try:
        # Добавляем детальное логирование
        logger.info(f"get_classification_report called by user: {current_user.username}")

        # Проверяем, что запрос содержит JSON
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No JSON data received"}), 400

        logger.info(f"Request data: {data}")

        # Проверяем наличие обязательных полей
        if not data.get('dateFrom') or not data.get('dateTo'):
            logger.error(f"Missing required fields: dateFrom={data.get('dateFrom')}, dateTo={data.get('dateTo')}")
            return jsonify({"error": "Missing required fields: dateFrom and dateTo"}), 400

        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"

        logger.info(f"Formatted dates: from={date_from}, to={date_to}")

        session = get_quality_connection()
        if session is None:
            logger.error("Failed to get quality database connection")
            return jsonify({"error": "Ошибка подключения к базе данных quality"}), 500

        # Получаем низкоуровневое соединение MySQL
        connection = session.connection().connection
        cursor = connection.cursor()

        logger.info("Calling stored procedure Classific")
        # Выполняем процедуру и сразу получаем результаты
        cursor.callproc("Classific", (date_from, date_to))

        # Получаем результаты
        result_found = False
        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                result_found = True
                logger.info("Data received from stored procedure")

                # Преобразуем кортеж в словарь, используя описание столбцов
                columns = [desc[0] for desc in result.description]
                data = dict(zip(columns, row))

                # Формируем структуру отчета
                report_data = {
                    "classifications": [
                        {
                            "name": "Авиакомпанию",
                            "complaints": data.get("ComplaintIssueAvia", 0),
                            "gratitude": data.get("GrateIssueAvia", 0),
                            "questions": data.get("QuestionIssueAvia", 0),
                            "suggestions": data.get("OfferIssueAvia", 0),
                            "total": data.get("ItogoIssueAvia", 0),
                        },
                        {
                            "name": "Агентство",
                            "complaints": data.get("ComplaintIssueAgent", 0),
                            "gratitude": data.get("GrateIssueAgent", 0),
                            "questions": data.get("QuestionIssueAgent", 0),
                            "suggestions": data.get("OfferIssueAgent", 0),
                            "total": data.get("ItogoIssueAgent", 0),
                        },
                        {
                            "name": "Агентство ТТР",
                            "complaints": data.get("ComplaintIssueAgentTTR", 0),
                            "gratitude": data.get("GrateIssueAgentTTR", 0),
                            "questions": data.get("QuestionIssueAgentTTR", 0),
                            "suggestions": data.get("OfferIssueAgentTTR", 0),
                            "total": data.get("ItogoIssueAgentTTR", 0),
                        },
                        {
                            "name": "Водителя",
                            "complaints": data.get("ComplaintIssueDriver", 0),
                            "gratitude": data.get("GrateIssueDriver", 0),
                            "questions": data.get("QuestionIssueDriver", 0),
                            "suggestions": data.get("OfferIssueDriver", 0),
                            "total": data.get("ItogoIssueDriver", 0),
                        },
                        {
                            "name": "Всё понравилось",
                            "complaints": data.get("ComplaintIssueOk", 0),
                            "gratitude": data.get("GrateIssueOk", 0),
                            "questions": data.get("QuestionIssueOk", 0),
                            "suggestions": data.get("OfferIssueOk", 0),
                            "total": data.get("ItogoIssueOk", 0),
                        },
                        {
                            "name": "Гида на трансфере",
                            "complaints": data.get("ComplaintIssueGuideTransfer", 0),
                            "gratitude": data.get("GrateIssueGuideTransfer", 0),
                            "questions": data.get("QuestionIssueGuideTransfer", 0),
                            "suggestions": data.get("OfferIssueGuideTransfer", 0),
                            "total": data.get("ItogoIssueGuideTransfer", 0),
                        },
                        {
                            "name": "Гида отельного",
                            "complaints": data.get("ComplaintIssueGuideHotel", 0),
                            "gratitude": data.get("GrateIssueGuideHotel", 0),
                            "questions": data.get("QuestionIssueGuideHotel", 0),
                            "suggestions": data.get("OfferIssueGuideHotel", 0),
                            "total": data.get("ItogoIssueGuideHotel", 0),
                        },
                        {
                            "name": "Гида экскурсионного",
                            "complaints": data.get("ComplaintIssueGuideTour", 0),
                            "gratitude": data.get("GrateIssueGuideTour", 0),
                            "questions": data.get("QuestionIssueGuideTour", 0),
                            "suggestions": data.get("OfferIssueGuideTour", 0),
                            "total": data.get("ItogoIssueGuideTour", 0),
                        },
                        {
                            "name": "Отель",
                            "complaints": data.get("ComplaintIssueHotel", 0),
                            "gratitude": data.get("GrateIssueHotel", 0),
                            "questions": data.get("QuestionIssueHotel", 0),
                            "suggestions": data.get("OfferIssueHotel", 0),
                            "total": data.get("ItogoIssueHotel", 0),
                        },
                        {
                            "name": "Встреча в порту",
                            "complaints": data.get("ComplaintMeetingPort", 0),
                            "gratitude": data.get("GrateMeetingPort", 0),
                            "questions": data.get("QuestionMeetingPort", 0),
                            "suggestions": data.get("OfferMeetingPort", 0),
                            "total": data.get("ItogoMeetingPort", 0),
                        },
                        {
                            "name": "Сотрудника отправляющего офиса",
                            "complaints": data.get("ComplaintIssueSeeingOffice", 0),
                            "gratitude": data.get("GrateIssueSeeingOffice", 0),
                            "questions": data.get("QuestionIssueSeeingOffice", 0),
                            "suggestions": data.get("OfferIssueSeeingOffice", 0),
                            "total": data.get("ItogoIssueSeeingOffice", 0),
                        },
                        {
                            "name": "Сотрудника принимающего офиса",
                            "complaints": data.get("ComplaintIssueHostOffice", 0),
                            "gratitude": data.get("GrateIssueHostOffice", 0),
                            "questions": data.get("QuestionIssueHostOffice", 0),
                            "suggestions": data.get("OfferIssueHostOffice", 0),
                            "total": data.get("ItogoIssueHostOffice", 0),
                        },
                        {
                            "name": "Страховая компания",
                            "complaints": data.get("ComplaintIssueInsurance", 0),
                            "gratitude": data.get("GrateIssueInsurance", 0),
                            "questions": data.get("QuestionIssueInsurance", 0),
                            "suggestions": data.get("OfferIssueInsurance", 0),
                            "total": data.get("ItogoIssueInsurance", 0),
                        },
                        {
                            "name": "Экскурсия",
                            "complaints": data.get("ComplaintExcursion", 0),
                            "gratitude": data.get("GrateExcursion", 0),
                            "questions": data.get("QuestionExcursion", 0),
                            "suggestions": data.get("OfferExcursion", 0),
                            "total": data.get("ItogoExcursion", 0),
                        },
                        {
                            "name": "Экскурсионный тур",
                            "complaints": data.get("ComplaintIssueExcursion", 0),
                            "gratitude": data.get("GrateIssueExcursion", 0),
                            "questions": data.get("QuestionIssueExcursion", 0),
                            "suggestions": data.get("OfferIssueExcursion", 0),
                            "total": data.get("ItogoIssueExcursion", 0),
                        },
                        {
                            "name": "Другое",
                            "complaints": data.get("ComplaintIssueAnother", 0),
                            "gratitude": data.get("GrateIssueAnother", 0),
                            "questions": data.get("QuestionIssueAnother", 0),
                            "suggestions": data.get("OfferIssueAnother", 0),
                            "total": data.get("ItogoIssueAnother", 0),
                        },
                        {
                            "name": "Трансфер групповой",
                            "complaints": data.get("ComplaintGrateGroupTransfer", 0),
                            "gratitude": data.get("GrateGroupTransfer", 0),
                            "questions": data.get("QuestionGrateGroupTransfer", 0),
                            "suggestions": data.get("OfferGrateGroupTransfer", 0),
                            "total": data.get("ItogoGrateGroupTransfer", 0),
                        },
                        {
                            "name": "Трансфер индивидуальный",
                            "complaints": data.get("ComplaintTransferIndividual", 0),
                            "gratitude": data.get("GrateTransferIndividual", 0),
                            "questions": data.get("QuestionTransferIndividual", 0),
                            "suggestions": data.get("OfferTransferIndividual", 0),
                            "total": data.get("ItogoTransferIndividual", 0),
                        },
                        {
                            "name": "Трансфер VIP",
                            "complaints": data.get("ComplaintTransferVIP", 0),
                            "gratitude": data.get("GrateTransferVIP", 0),
                            "questions": data.get("QuestionTransferVIP", 0),
                            "suggestions": data.get("OfferTransferVIP", 0),
                            "total": data.get("ItogoTransferVIP", 0),
                        },
                        {
                            "name": "Колл центр на курорте",
                            "complaints": data.get("ComplaintCallCenterResort", 0),
                            "gratitude": data.get("GrateCallCenterResort", 0),
                            "questions": data.get("QuestionCallCenterResort", 0),
                            "suggestions": data.get("OfferCallCenterResort", 0),
                            "total": data.get("ItogoCallCenterResort", 0),
                        },
                        {
                            "name": "Колл центр отправляющего офиса",
                            "complaints": data.get(
                                "ComplaintCallCenterSendingOffice", 0
                            ),
                            "gratitude": data.get("GrateCallCenterSendingOffice", 0),
                            "questions": data.get("QuestionCallCenterSendingOffice", 0),
                            "suggestions": data.get("OfferCallCenterSendingOffice", 0),
                            "total": data.get("ItogoCallCenterSendingOffice", 0),
                        },
                        {
                            "name": "GDS Webbeds(DOTW)",
                            "complaints": data.get("Complaint_GDS", 0),
                            "gratitude": data.get("Grate_GDS", 0),
                            "questions": data.get("Question_GDS", 0),
                            "suggestions": data.get("Offer_GDS", 0),
                            "total": data.get("ItogoGDS", 0),
                        },
                        {
                            "name": "GDS Expedia",
                            "complaints": data.get("ComplaintGDSExpedia", 0),
                            "gratitude": data.get("GrateGDSExpedia", 0),
                            "questions": data.get("QuestionGDSExpedia", 0),
                            "suggestions": data.get("OfferGDSExpedia", 0),
                            "total": data.get("ItogoGDSExpedia", 0),
                        },
                        {
                            "name": "GDS GoGlobal",
                            "complaints": data.get("ComplaintGDSGoGlobal", 0),
                            "gratitude": data.get("GrateGDSGoGlobal", 0),
                            "questions": data.get("QuestionGDSGoGlobal", 0),
                            "suggestions": data.get("OfferGDSGoGlobal", 0),
                            "total": data.get("ItogoGDSGoGlobal", 0),
                        },
                    ],
                    "unclassified": {
                        "total": data.get("Obracheniya", 0),
                        "surveys": data.get("ObracheniyaAnket", 0),
                    },
                    "surveys": {
                        "complaints": data.get("ItogoAnketJalob", 0),
                        "gratitude": data.get("ItogoAnketBlagodarnoct", 0),
                        "questions": data.get("ItogoAnketVopros", 0),
                        "suggestions": data.get("ItogoAnketPredlojenie", 0),
                        "total": (
                            data.get("ItogoAnketJalob", 0)
                            + data.get("ItogoAnketBlagodarnoct", 0)
                            + data.get("ItogoAnketVopros", 0)
                            + data.get("ItogoAnketPredlojenie", 0)
                        ),
                    },
                }

                logger.info("Successfully created report data")
                return jsonify(report_data)

        if not result_found:
            logger.warning("No data returned from stored procedure")
            return jsonify({"error": "Нет данных за указанный период"}), 404

    except Exception as e:
        logger.error(f"Ошибка в get_classification_report: {str(e)}", exc_info=True)
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500
    finally:
        # Закрываем ресурсы в правильном порядке
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if session:
            try:
                session.close()
            except:
                pass

    # Fallback return (не должен быть достигнут при нормальном выполнении)
    return jsonify({"error": "Неожиданная ошибка выполнения"}), 500


@main.route("/test-quality-db", methods=["GET"])
@csrf.exempt
@login_required
def test_quality_db():
    """Временная функция для тестирования подключения к базе данных quality"""
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Не удалось получить подключение к базе данных quality"}), 500

        # Простой тест подключения
        connection = session.connection().connection
        cursor = connection.cursor()

        # Выполняем простой запрос
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()

        if result and result[0] == 1:
            cursor.close()
            session.close()
            return jsonify({"status": "success", "message": "Подключение к базе данных quality работает"})
        else:
            cursor.close()
            session.close()
            return jsonify({"error": "Неожиданный результат запроса"}), 500

    except Exception as e:
        logger.error(f"Ошибка в test_quality_db: {str(e)}", exc_info=True)
        return jsonify({"error": f"Ошибка тестирования базы данных: {str(e)}"}), 500


@main.route("/get-resorts-report", methods=["POST"])
@csrf.exempt
@login_required
def get_resorts_report():
    session = None
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"

        if not date_from or not date_to:
            return jsonify({"error": "Не указан период"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Получаем низкоуровневое соединение MySQL
        connection = session.connection().connection

        # Используем курсор для вызова процедуры
        cursor = connection.cursor()
            # Вызываем хранимую процедуру resorts с параметрами
        cursor.callproc("resorts", (date_from, date_to))

            # Получаем результаты
        for result in cursor.stored_results():
            resorts_data = []
            for row in result.fetchall():
                # Convert tuple to dictionary using column descriptions
                columns = [desc[0] for desc in result.description]
                data = dict(zip(columns, row))

                resort = {
                    "name": data.get("ResortName", ""),
                    "complaints": data.get("JalobaIssueResort_out", 0),
                    "gratitude": data.get("GrateIssueResort_out", 0),
                    "questions": data.get("QuestionIssueResort_out", 0),
                    "suggestions": data.get("OfferIssueResort_out", 0),
                }
                resorts_data.append(resort)

            if not resorts_data:
                return jsonify({"error": "Нет данных за указанный период"}), 404

            # Очищаем временную таблицу с помощью процедуры del_u_Resorts
            cursor.callproc("del_u_Resorts")
            connection.commit()

            return jsonify(resorts_data)

        return jsonify({"error": "Нет данных от хранимой процедуры"}), 404

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        return jsonify({"error": f"Ошибка при получении данных: {str(e)}"}), 500
    finally:
        if session:
            session.close()


@main.route("/get-resort-types-data", methods=["POST"])
@csrf.exempt
@login_required
def get_resort_types_data():
    session = None
    try:
        data = request.get_json()
        date_from = data.get("dateFrom")
        date_to = data.get("dateTo")
        tracker_id = data.get("trackerId")

        if not all([date_from, date_to, tracker_id]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        # Модифицируем дату окончания, добавляя время конца дня
        date_to = f"{date_to} 23:59:59"
        # Добавляем время начала дня для начальной даты для полноты
        date_from = f"{date_from} 00:00:00"

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            connection = session.connection().connection
            cursor = connection.cursor()
            cursor.callproc(
                "up_TypesRequests_ITS", (date_from, date_to, tracker_id)
            )

            results = []
            for result in cursor.stored_results():
                data = result.fetchall()
                logger.info(f"Получено записей: {len(data)}")

                for row in data:
                    try:
                        # Convert tuple to dictionary using column descriptions
                        columns = [desc[0] for desc in result.description]
                        row_dict = dict(zip(columns, row))

                        processed_row = {}
                        for key, value in row_dict.items():
                            try:
                                if key == "resort_name":
                                    processed_row[key] = value if value else ""
                                else:
                                    processed_row[key] = (
                                        0 if value is None else int(value)
                                    )
                            except ValueError as ve:
                                logger.error(
                                    f"Ошибка преобразования значения: key={key}, value={value}, error={str(ve)}"
                                )
                                processed_row[key] = 0
                        results.append(processed_row)
                    except Exception as row_error:
                        logger.error(
                            f"Ошибка обработки строки: {str(row_error)}, row={row}"
                        )
                        continue

            if not results:
                logger.warning("Нет данных в результате выполнения процедуры")
                return jsonify({"error": "Нет данных за указанный период"}), 404

            logger.info(f"Успешно обработано записей: {len(results)}")
            return jsonify(results)

        except Exception as e:
            logger.error(f"Ошибка при выполнении процедуры: {str(e)}")
            return jsonify({"error": f"Ошибка при выполнении запроса: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return jsonify({"error": f"Ошибка при получении данных: {str(e)}"}), 500
    finally:
        if session:
            session.close()


@main.route("/get-issues", methods=["POST"])
@csrf.exempt
@login_required
def get_issues():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-type", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_type():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-resort", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_resort():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-employee", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_employee():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-status", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_status():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-priority", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_priority():
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND t.name = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            result = session.execute(
                text(query),
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "assigned_to": assigned_to,
                    "request_type": request_type,
                },
            )

            issues = [{"id": row[0], "subject": row[1]} for row in result]
            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Ошибка при выполнении запроса: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@main.route("/get-issues-by-category", methods=["POST"])
@csrf.exempt
@login_required
def get_issues_by_category():
    session = None
    try:
        data = request.get_json()
        date_from = f"{data.get('dateFrom')} 00:00:00"
        date_to = f"{data.get('dateTo')} 23:59:59"
        assigned_to = data.get("assignedTo")
        request_type = data.get("requestType")  # Теперь это ID трекера
        country = data.get("country")

        if not all([date_from, date_to, assigned_to, request_type]):
            return jsonify({"error": "Не все параметры переданы"}), 400

        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        try:
            query = """
                SELECT DISTINCT i.id,
                       (SELECT cv2.value
                        FROM custom_values cv2
                        WHERE cv2.customized_id = i.id
                        AND cv2.custom_field_id = 22) as header
                FROM issues i
                JOIN custom_values cv ON i.id = cv.customized_id
                LEFT JOIN custom_values cv_country ON i.id = cv_country.customized_id
                    AND cv_country.custom_field_id = 24
                JOIN trackers t ON i.tracker_id = t.id
                WHERE cv.custom_field_id = 21
                AND cv.value = :assigned_to
                AND i.tracker_id = :request_type
                AND i.created_on BETWEEN :date_from AND :date_to
            """

            params = {
                "date_from": date_from,
                "date_to": date_to,
                "assigned_to": assigned_to,
                "request_type": request_type,
            }

            if country and country.strip():
                query += " AND TRIM(cv_country.value) = TRIM(:country)"
                params["country"] = country

            print(f"Final SQL query: {query}")
            print(f"Parameters: {params}")

            result = session.execute(text(query), params)
            all_results = result.fetchall()
            print(f"Number of results: {len(all_results)}")

            issues = []
            for row in all_results:
                print(f"Processing row: {row}")
                issues.append({"id": row[0], "subject": row[1]})

            return jsonify({"issues": issues})

        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            return jsonify({"error": f"Ошибка базы данных: {str(db_error)}"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@main.route("/get-total-issues-count")
@login_required
def get_total_issues_count():
    """Получение общего количества обращений с безопасной обработкой ошибок"""
    try:
        def query_total_count(session):
            result = session.execute(
                text("SELECT COUNT(id) as count FROM issues WHERE project_id=1")
            )
            return result.scalar()

        count = execute_quality_query_safe(
            query_total_count,
            "получение общего количества обращений"
        )

        if count is None:
            return jsonify({"success": True, "count": 0, "warning": "Временные проблемы с подключением"})

        return jsonify({"success": True, "count": count or 0})

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении общего количества обращений: {str(e)}")
        return jsonify({"success": False, "error": "Внутренняя ошибка сервера", "count": 0}), 500


@main.route("/get-new-issues-count")
@login_required
def get_new_issues_count():
    """Получение количества новых обращений с безопасной обработкой ошибок"""
    try:
        def query_count(session):
            result = session.execute(
                text("SELECT COUNT(id) as count FROM issues WHERE project_id=1 AND status_id=1")
            )
            return result.scalar()

        count = execute_quality_query_safe(
            query_count,
            "получение количества новых обращений"
        )

        if count is None:
            # Возвращаем последнее известное значение или 0
            return jsonify({"success": True, "count": 0, "warning": "Временные проблемы с подключением"})

        return jsonify({"success": True, "count": count or 0})

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении количества новых обращений: {str(e)}")
        return jsonify({"success": False, "error": "Внутренняя ошибка сервера", "count": 0}), 500


@main.route("/comment-notifications")
@login_required
def get_comment_notifications():
    """Получение уведомлений о комментариях с безопасной обработкой ошибок"""
    try:
        if not current_user.is_authenticated:
            return jsonify({"error": "Пользователь не авторизован"}), 401

        def query_notifications(session):
            query = """
                SELECT j.id, j.journalized_id, j.notes, j.created_on,
                       j.user_id, i.subject
                FROM journals j
                INNER JOIN issues i ON j.journalized_id = i.id
                WHERE j.journalized_type = 'Issue'
                AND i.project_id = 1
                AND j.notes IS NOT NULL
                AND TRIM(j.notes) != ''
                AND j.is_read = 0
                ORDER BY j.created_on DESC
                LIMIT 1000
            """

            result = session.execute(text(query))
            return result.mappings().all()

        notifications = execute_quality_query_safe(
            query_notifications,
            "получение уведомлений о комментариях"
        )

        if notifications is None:
            # Возвращаем пустой результат вместо ошибки
            return jsonify({
                "success": True,
                "html": render_template("_comment_notifications.html", notifications=[]),
                "count": 0,
                "warning": "Временные проблемы с подключением к базе данных"
            })

        notifications_data = [
            {
                "id": row["id"],
                "journalized_id": row["journalized_id"],
                "notes": row["notes"] if row["notes"] else "",
                "created_on": (
                    row["created_on"].strftime("%Y-%m-%d %H:%M:%S")
                    if row["created_on"]
                    else ""
                ),
                "user_id": row["user_id"],
                "subject": row["subject"] if row["subject"] else "",
            }
            for row in notifications
        ]

        logger.info(f"Получено {len(notifications_data)} уведомлений о комментариях")

        return jsonify(
            {
                "success": True,
                "html": render_template(
                    "_comment_notifications.html", notifications=notifications_data
                ),
                "count": len(notifications_data),
            }
        )

    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении уведомлений: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "html": render_template("_comment_notifications.html", notifications=[]),
            "count": 0
        }), 500


@main.route("/mark-comment-read/<int:journal_id>", methods=["POST"])
@csrf.exempt
@login_required
def mark_comment_read(journal_id):
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        session.execute(
            text("UPDATE journals SET is_read = 1 WHERE id = :id"), {"id": journal_id}
        )
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при отметке комментария как прочитанного: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@main.route("/mark-all-comments-read", methods=["POST"])
@csrf.exempt
@login_required
def mark_all_comments_read():
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        session.execute(
            text(
                "UPDATE journals SET is_read = 1 WHERE journalized_type = 'Issue' AND is_read = 0"
            )
        )
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при отметке всех комментариев как прочитанных: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if session:
            session.close()


@main.route("/get-countries")
@login_required
def get_countries():
    session = None # Инициализируем session здесь
    try:
        session = get_quality_connection()
        if session is None:
            return jsonify({"error": "Ошибка подключения к базе данных"}), 500

        # Оборачиваем SQL запрос в text()
        query = text(
            "SELECT DISTINCT value FROM custom_values WHERE custom_field_id = 24 ORDER BY value ASC"
        )
        result = session.execute(query).mappings().all() # Используем .mappings().all() для словарей


        # Формируем список стран (если значение не пустое)
        countries = [row["value"] for row in result if row["value"] is not None]
        return jsonify(countries)
    except Exception as e:
        logger.error(f"Error in get_countries: {str(e)}") # Используем logger
        return jsonify({"error": str(e)}), 500
    finally:
        if session: # Проверяем что session была присвоена перед закрытием
            session.close()


@main.route("/get-new-issues-list")
@login_required
def get_new_issues_list():
    """Получение списка новых обращений с безопасной обработкой ошибок"""
    try:
        def query_new_issues(session):
            query = """
                SELECT id, subject, description, created_on
                FROM issues
                WHERE project_id = 1
                AND tracker_id = 1
                AND status_id = 1
                ORDER BY created_on DESC
            """

            result = session.execute(text(query))
            return result.mappings().all()

        issues = execute_quality_query_safe(
            query_new_issues,
            "получение списка новых обращений"
        )

        if issues is None:
            # Возвращаем пустой результат вместо ошибки
            return jsonify({
                "success": True,
                "html": render_template("_new_issues_content.html", issues=[]),
                "count": 0,
                "warning": "Временные проблемы с подключением к базе данных"
            })

        issues_data = [
            {
                "id": row["id"],
                "subject": row["subject"],
                "description": row["description"],
                "created_on": row["created_on"],
            }
            for row in issues
        ]

        # Рендерим только содержимое, без структуры сайдбара
        html_content = render_template(
            "_new_issues_content.html", issues=issues_data
        )

        logger.info(f"Получено {len(issues_data)} новых обращений")

        return jsonify(
            {"success": True, "html": html_content, "count": len(issues_data)}
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка новых обращений: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "html": render_template("_new_issues_content.html", issues=[]),
            "count": 0
        }), 500

@main.route("/api/notifications/widget/toggle", methods=["POST"])
@login_required
def api_toggle_notification_widget():
    """API для переключения состояния виджета уведомлений"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)

        logger.info(f"Переключение виджета уведомлений для пользователя {current_user.id}: {enabled}")

        # Здесь можно сохранить настройку в базе данных или профиле пользователя
        # Пока что просто возвращаем успех

        return jsonify({
            "success": True,
            "enabled": enabled,
            "message": f"Виджет уведомлений {'включен' if enabled else 'отключен'}"
        })

    except Exception as e:
        logger.error(f"Ошибка переключения виджета уведомлений: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@main.route("/api/notifications/widget/clear", methods=["POST"])
@login_required
def api_clear_widget_notifications():
    """API эндпоинт для очистки уведомлений в виджете."""
    try:
        service = get_notification_service()
        success = service.clear_notifications_for_widget(current_user.id)
        if success:
            logger.info(f"Уведомления в виджете для пользователя {current_user.id} успешно очищены.")
            return jsonify({'success': True})
        else:
            logger.error(f"Не удалось очистить уведомления в виджете для пользователя {current_user.id} на стороне сервиса.")
            return jsonify({'success': False, 'error': 'Не удалось выполнить операцию в базе данных Redmine'}), 500
    except Exception as e:
        logger.critical(f"Критическая ошибка при очистке уведомлений в виджете для пользователя {current_user.id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Неизвестная критическая ошибка на сервере'}), 500

@main.route('/api/notifications/count', methods=['GET'])
@login_required
def get_notifications_count_api():
    try:
        count = get_total_notification_count(current_user)
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"Error in get_notifications_count_api: {str(e)}")
        return jsonify({"count": 0, "error": str(e)}), 500

class IssueTemplateHelper:
    def __init__(self):
        self.connection = None
        self.cache = {}

    def get_connection(self):
        if not self.connection:
            self.connection = get_connection(
                DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
            )
        return self.connection

    def get_cached_property_name(self, property_name, prop_key, old_value, new_value):
        cache_key = f"{property_name}:{prop_key}:{old_value}:{new_value}"
        if cache_key not in self.cache:
            self.cache[cache_key] = get_property_name(property_name, prop_key, old_value, new_value)
        return self.cache[cache_key]

@main.route("/api/issue/<int:issue_id>/attachment/<int:attachment_id>/download", methods=["GET"])
@csrf.exempt
@login_required
def download_issue_attachment(issue_id, attachment_id):
    """
    API для скачивания вложения заявки
    """
    current_app.logger.info(f"[API] GET /api/issue/{issue_id}/attachment/{attachment_id}/download - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

                # Используем существующий Redmine коннектор (он уже использует API ключ администратора)
        redmine_connector = get_redmine_connector(current_user, None)

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем заявку для проверки прав доступа
            issue = redmine_connector.redmine.issue.get(issue_id, include=['attachments'])
            current_app.logger.info(f"[API] Получена заявка {issue_id} с {len(issue.attachments)} вложениями")

            # Ищем нужное вложение
            attachment = None
            for att in issue.attachments:
                current_app.logger.info(f"[API] Проверяем вложение {att.id}: {att.filename}")
                if att.id == attachment_id:
                    attachment = att
                    break

            if not attachment:
                current_app.logger.error(f"[API] Вложение #{attachment_id} не найдено в заявке {issue_id}")
                return jsonify({
                    "error": f"Вложение #{attachment_id} не найдено",
                    "success": False
                }), 404

            current_app.logger.info(f"[API] Найдено вложение: {attachment.filename} (размер: {attachment.filesize} байт)")

            # Проверяем, что attachment найден в заявке
            current_app.logger.info(f"[API] Attachment {attachment_id} найден в заявке {issue_id}")

            # Формируем URL для прямого скачивания из Redmine
            redmine_download_url = f"{redmine_connector.redmine.url}/attachments/download/{attachment_id}"
            current_app.logger.info(f"[API] URL для скачивания: {redmine_download_url}")

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] GET /api/issue/{issue_id}/attachment/{attachment_id}/download выполнен за {execution_time:.2f}с")

            # Возвращаем JSON с URL для скачивания
            return jsonify({
                "success": True,
                "download_url": redmine_download_url,
                "filename": attachment.filename,
                "filesize": attachment.filesize
            })

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка скачивания вложения {attachment_id} для заявки {issue_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка скачивания файла: {str(redmine_error)}",
                "success": False
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в GET /api/issue/{issue_id}/attachment/{attachment_id}/download: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500
