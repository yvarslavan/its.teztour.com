"""
Helper функции для использования в шаблонах Jinja2
Убирает хардкод и обращения к базе данных из шаблонов
"""

from flask import current_app
from blog.settings import Config
from redmine import get_connection
import logging
from datetime import datetime
from flask import Flask

logger = logging.getLogger(__name__)

class TemplateHelpers:
    """Класс с helper функциями для шаблонов"""

    def __init__(self):
        self.config = Config()
        self._connection = None

    def get_mysql_connection(self):
        """Получает соединение с MySQL Redmine"""
        if not self._connection:
            try:
                self._connection = get_connection(
                    self.config.DB_REDMINE_HOST,
                    self.config.DB_REDMINE_USER_NAME,
                    self.config.DB_REDMINE_PASSWORD,
                    self.config.DB_REDMINE_NAME
                )
            except Exception as e:
                logger.error(f"Ошибка подключения к MySQL Redmine: {e}")
                return None
        return self._connection

    def get_status_name_safe(self, status_id):
        """Безопасное получение названия статуса по ID"""
        if not status_id:
            return "Не указан"

        try:
            conn = self.get_mysql_connection()
            if not conn:
                return f"Статус #{status_id}"

            cursor = conn.cursor()
            sql = """
            SELECT COALESCE(us.name, s.name) as name
            FROM issue_statuses s
            LEFT JOIN u_statuses us ON s.id = us.id
            WHERE s.id = %s
            """
            cursor.execute(sql, (status_id,))
            result = cursor.fetchone()

            if result:
                return result['name']
            else:
                return f"Статус #{status_id}"

        except Exception as e:
            logger.error(f"Ошибка получения названия статуса {status_id}: {e}")
            return f"Статус #{status_id}"

    def get_user_name_safe(self, user_id):
        """Безопасное получение имени пользователя по ID"""
        if not user_id:
            return "Не назначен"

        try:
            conn = self.get_mysql_connection()
            if not conn:
                return f"Пользователь #{user_id}"

            cursor = conn.cursor()
            sql = """
            SELECT CONCAT(firstname, ' ', lastname) as full_name
            FROM users
            WHERE id = %s
            """
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()

            if result and result['full_name']:
                return result['full_name'].strip()
            else:
                return f"Пользователь #{user_id}"

        except Exception as e:
            logger.error(f"Ошибка получения имени пользователя {user_id}: {e}")
            return f"Пользователь #{user_id}"

    def get_project_name_safe(self, project_id):
        """Безопасное получение названия проекта по ID"""
        if not project_id:
            return "Не указан"

        try:
            conn = self.get_mysql_connection()
            if not conn:
                return f"Проект #{project_id}"

            cursor = conn.cursor()
            sql = "SELECT name FROM projects WHERE id = %s"
            cursor.execute(sql, (project_id,))
            result = cursor.fetchone()

            if result:
                return result['name']
            else:
                return f"Проект #{project_id}"

        except Exception as e:
            logger.error(f"Ошибка получения названия проекта {project_id}: {e}")
            return f"Проект #{project_id}"

    def get_priority_name_safe(self, priority_id):
        """Безопасное получение названия приоритета по ID"""
        if not priority_id:
            return "Не указан"

        try:
            conn = self.get_mysql_connection()
            if not conn:
                return f"Приоритет #{priority_id}"

            cursor = conn.cursor()
            sql = """
            SELECT COALESCE(up.name, e.name) as name
            FROM enumerations e
            LEFT JOIN u_Priority up ON e.id = up.id
            WHERE e.id = %s AND e.type = 'IssuePriority'
            """
            cursor.execute(sql, (priority_id,))
            result = cursor.fetchone()

            if result:
                return result['name']
            else:
                return f"Приоритет #{priority_id}"

        except Exception as e:
            logger.error(f"Ошибка получения названия приоритета {priority_id}: {e}")
            return f"Приоритет #{priority_id}"

    def format_boolean_field(self, value, field_name):
        """Форматирование булевых полей"""
        if field_name == 'easy_helpdesk_need_reaction':
            return 'Да' if value == '1' else 'Нет'
        elif field_name == '16':
            return 'Да' if value and value != '0' else 'Нет'
        else:
            return 'Да' if value else 'Нет'

# Глобальный экземпляр для использования в приложении
template_helpers = TemplateHelpers()

def register_template_helpers(app: Flask):
    """Регистрирует helper функции в Jinja2"""

    @app.template_global()
    def get_status_name_safe(status_id):
        return template_helpers.get_status_name_safe(status_id)

    @app.template_global()
    def get_user_name_safe(user_id):
        return template_helpers.get_user_name_safe(user_id)

    @app.template_global()
    def get_project_name_safe(project_id):
        return template_helpers.get_project_name_safe(project_id)

    @app.template_global()
    def get_priority_name_safe(priority_id):
        return template_helpers.get_priority_name_safe(priority_id)

    @app.template_global()
    def format_boolean_field(value, field_name):
        return template_helpers.format_boolean_field(value, field_name)

    def datetimeformat(value, format='%d.%m.%Y %H:%M'):
        """Фильтр для форматирования datetime объектов"""
        if value is None:
            return 'Неизвестно'
        if isinstance(value, str):
            try:
                # Попытка парсинга строки в datetime
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime(format)
        return str(value)

    # Регистрация пользовательского фильтра
    app.jinja_env.filters['datetimeformat'] = datetimeformat
