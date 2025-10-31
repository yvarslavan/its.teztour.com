import os
import tempfile
from datetime import timedelta, datetime
from configparser import ConfigParser
import logging
import functools
import time
from builtins import Exception
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import pytz
from redminelib import Redmine
from redminelib.exceptions import (
    BaseRedmineError,
    ResourceNotFoundError,
    AuthError,
    ForbiddenError,
)
import pymysql
import pymysql.cursors
from flask import flash, current_app
from blog.models import User, Notifications, NotificationsAddNotes
from blog import db
import uuid

# ИСПРАВЛЕНИЕ: Убираем импорт notification_service отсюда, чтобы избежать циклического импорта
# from blog.notification_service import notification_service, NotificationData, NotificationType, WebPushException
from typing import List, Dict, Set, Optional, Any


# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Создаем объект логгера
logger = logging.getLogger(__name__)

os.environ["NLS_LANG"] = "Russian.AL32UTF8"

# Импорт безопасной конфигурации
try:
    # Прямое чтение переменных окружения
    db_redmine_host = os.getenv('MYSQL_HOST')
    db_redmine_name = os.getenv('MYSQL_DATABASE')
    db_redmine_user_name = os.getenv('MYSQL_USER')
    db_redmine_password = os.getenv('MYSQL_PASSWORD')
    
    # Проверяем наличие обязательных переменных
    if not all([db_redmine_host, db_redmine_name, db_redmine_user_name, db_redmine_password]):
        missing = [k for k, v in [
            ('MYSQL_HOST', db_redmine_host),
            ('MYSQL_DATABASE', db_redmine_name),
            ('MYSQL_USER', db_redmine_user_name),
            ('MYSQL_PASSWORD', db_redmine_password)
        ] if not v]
        logger.warning(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing)}")
        raise ImportError("Неполная конфигурация")
    
    logger.info("✅ Используется безопасная конфигурация из переменных окружения")

    # Получаем путь к текущему каталогу
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_absolute_path = os.getenv('DB_PATH', 'blog/db/blog.db')
    ERROR_MESSAGE = "An error occurred:"

    # Глобальные переменные для URL и API ключа администратора Redmine
    REDMINE_URL = os.getenv('REDMINE_URL')
    REDMINE_ADMIN_API_KEY = os.getenv('REDMINE_API_KEY')
    ANONYMOUS_USER_ID_CONFIG = int(os.getenv('REDMINE_ANONYMOUS_USER_ID', '4'))

except ImportError:
    logger.warning("⚠️ Используется устаревшая конфигурация config.ini")
    import os

    # Используем переменные окружения напрямую
    db_redmine_host = os.getenv('MYSQL_HOST')
    db_redmine_name = os.getenv('MYSQL_DATABASE')
    db_redmine_user_name = os.getenv('MYSQL_USER')
    db_redmine_password = os.getenv('MYSQL_PASSWORD')

    # Получаем путь к текущему каталогу
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Получаем относительный путь к базе данных из переменных окружения
    db_relative_path = os.getenv('DB_PATH', 'blog/db/blog.db')
    # Формируем абсолютный путь к базе данных
    db_absolute_path = os.path.join(current_dir, db_relative_path)
    ERROR_MESSAGE = "An error occurred:"

    # Глобальные переменные для URL и API ключа администратора Redmine
    REDMINE_URL = os.getenv('REDMINE_URL')
    REDMINE_ADMIN_API_KEY = os.getenv('REDMINE_API_KEY')
    # ANONYMOUS_USER_ID также уже определен глобально в routes.py, но может понадобиться здесь
    ANONYMOUS_USER_ID_CONFIG = int(os.getenv('REDMINE_ANONYMOUS_USER_ID', '4'))


def get_connection(host, user_name, password, name, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            connection = pymysql.connect(
                host=host,
                user=user_name,
                password=password,
                db=name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
            logger.info("Соединение с базой данных установлено")
            return connection
        except pymysql.Error as e:
            logger.error(f"Ошибка при установлении соединения с базой данных: {e}")
            attempts += 1
            if attempts < max_attempts:
                logger.warning(
                    f"Повторная попытка подключения через 3 секунды (попытка {attempts + 1} из {max_attempts})..."
                )
                time.sleep(3)
        except Exception as _:  # pylint: disable=broad-except
            logging.error(
                "Неизвестная ошибка при подключении к базе данных", exc_info=True
            )
            break  # или можете выбрать продолжить попытки, если считаете это целесообразным
    logger.error(
        f"Не удалось установить соединение с базой данных после {max_attempts} попыток"
    )
    return None


def convert_datetime_msk_format(input_datetime, redmine_timezone_str="Europe/Moscow"):
    output_format = "%d.%m.%Y %H:%M"

    # Устанавливаем часовой пояс сервера Redmine
    redmine_timezone = pytz.timezone(redmine_timezone_str)
    input_datetime = input_datetime.astimezone(redmine_timezone) + timedelta(
        hours=3
    )  # добавляем 3 часа

    output_datetime = input_datetime.strftime(output_format)
    return output_datetime


def get_user_full_name_from_id(connection, property_value):
    sql = "SELECT CONCAT(IFNULL(lastname, ''), ' ', IFNULL(firstname, '')) AS full_name FROM users WHERE id=%s"
    cursor = None
    full_name = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, (property_value,))
        for row in cursor:
            full_name = row["full_name"]
            return full_name  # Возвращаем полное имя пользователя после первой итерации
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
    finally:
        if cursor is not None:
            cursor.close()
    return (
        full_name  # Возвращаем None в случае ошибки или отсутствия результата запроса
    )


def get_project_name_from_id(connection, project_id):
    sql = "SELECT IFNULL(name,'') as name FROM projects WHERE id=%s"
    cursor = None
    project_name = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, (project_id,))
        for row in cursor:
            project_name = row["name"]
            return project_name
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
    finally:
        if cursor is not None:
            cursor.close()
    return project_name


def get_status_name_from_id(connection, status_id):
    sql = "SELECT IFNULL(name,'') as name FROM u_statuses WHERE id=%s"
    cursor = None
    status_name = None  # Инициализация по умолчанию
    try:
        cursor = connection.cursor()
        cursor.execute(sql, (status_id,))
        for row in cursor:
            status_name = row["name"]
            return status_name
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
    finally:
        if cursor is not None:
            cursor.close()
    return status_name


def get_priority_name_from_id(connection, priority_id):
    sql = "SELECT IFNULL(name,'') as name FROM u_Priority WHERE id=%s"
    cursor = None
    priority_name = None  # Инициализация по умолчанию
    try:
        cursor = connection.cursor()
        cursor.execute(sql, (priority_id,))
        for row in cursor:
            priority_name = row["name"]
            return priority_name
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
    finally:
        if cursor is not None:
            cursor.close()
    return priority_name


def get_property_name(property_name, prop_key, old_value, value):
    connection = get_connection(
        db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name
    )
    result = None  # Инициализируем result
    if connection:
        with connection:
            if prop_key == "project_id":
                project_name_from = get_project_name_from_id(connection, old_value)
                project_name_to = get_project_name_from_id(connection, value)
                result = (
                    "Параметр&nbsp;<b>Проект</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + (project_name_from or "None")
                    + "</b>&nbsp;на&nbsp;<b>"
                    + (project_name_to or "None")
                    + "</b>"
                )

            elif prop_key == "assigned_to_id":
                assigned_name_from = None
                assigned_name_to = None
                if old_value is None:
                    assigned_name_to = get_user_full_name_from_id(connection, value)
                else:
                    assigned_name_from = get_user_full_name_from_id(
                        connection, old_value
                    )
                    assigned_name_to = get_user_full_name_from_id(connection, value)
                result = (
                    "Параметр&nbsp;<b>Назначена</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + (assigned_name_from or "None")
                    + "</b>&nbsp;на&nbsp;<b>"
                    + (assigned_name_to or "None")
                    + "</b>"
                )

            elif prop_key == "status_id":
                status_name_from = get_status_name_from_id(connection, old_value)
                status_name_to = get_status_name_from_id(connection, value)
                result = (
                    "Параметр&nbsp;<b>Статус</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + str(status_name_from)
                    + "</b>&nbsp;на&nbsp;<b>"
                    + str(status_name_to)
                    + "</b>"
                )

            elif prop_key == "priority_id":
                priority_name_from = get_priority_name_from_id(connection, old_value)
                priority_name_to = get_priority_name_from_id(connection, value)
                result = (
                    "Параметр&nbsp;<b>Приоритет</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + str(priority_name_from)
                    + "</b>&nbsp;на&nbsp;<b>"
                    + str(priority_name_to)
                    + "</b>"
                )

            elif prop_key == "subject":
                result = (
                    "Параметр&nbsp;<b>Тема</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + str(old_value)
                    + "</b>&nbsp;на&nbsp;<b>"
                    + str(value)
                    + "</b>"
                )

            elif prop_key == "easy_helpdesk_need_reaction":
                old_reaction_text = "Да" if old_value == "1" else "Нет"
                new_reaction_text = "Да" if value == "1" else "Нет"
                result = (
                    "Параметр&nbsp;<b>Нужна&nbsp;реакция?</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + old_reaction_text
                    + "</b>&nbsp;на&nbsp;<b>"
                    + new_reaction_text
                    + "</b>"
                )

            elif prop_key == "done_ratio":
                result = (
                    "Параметр&nbsp;<b>Готовность</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                    + str(old_value)
                    + "%</b>&nbsp;на&nbsp;<b>"
                    + str(value)
                    + "%</b>"
                )

            elif prop_key == "16":  # Кастомное поле "Что нового"
                if old_value and not value:
                    # Удаление значения: было что-то, стало пустое (None/null)
                    old_text = "Да" if str(old_value) != "0" else "Нет"
                    result = (
                        "Значение&nbsp;<b>"
                        + old_text
                        + "</b>&nbsp;параметра&nbsp;<b>Что&nbsp;нового</b>&nbsp;удалено"
                    )
                elif not old_value and value:
                    # Добавление значения: было пустое (None/null), стало что-то
                    new_text = "Да" if str(value) != "0" else "Нет"
                    result = (
                        "Параметр&nbsp;<b>Что&nbsp;нового</b>&nbsp;изменился&nbsp;на&nbsp;<b>"
                        + new_text
                        + "</b>"
                    )
                else:
                    # Обычное изменение значения
                    old_text = "Да" if old_value and str(old_value) != "0" else "Нет"
                    new_text = "Да" if value and str(value) != "0" else "Нет"
                    result = (
                        "Параметр&nbsp;<b>Что&nbsp;нового</b>&nbsp;изменился&nbsp;c&nbsp;<b>"
                        + old_text
                        + "</b>&nbsp;на&nbsp;<b>"
                        + new_text
                        + "</b>"
                    )

            elif property_name == "attachment":
                result = "Файл&nbsp;<b>" + str(value) + "</b>&nbsp;добавлен"

            elif property_name == "relation" and prop_key == "relates":
                result = (
                    "Задача&nbsp;связана&nbsp;с&nbsp;задачей&nbsp;<b>#"
                    + str(value)
                    + "</b>"
                )

            elif (
                prop_key == "subtask"
                and property_name == "relation"
                and value is not None
            ):
                result = "Добавлена&nbsp;подзадача&nbsp;<b>#" + str(value) + "</b>"

            else:
                result = None

    return result


class RedmineConnector:
    def __init__(self, url, username=None, password=None, api_key=None):
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error(f"Некорректный URL для подключения к Redmine: {url}")
                raise ValueError("Некорректный URL для подключения к Redmine.")

            logger.info(f"Инициализация RedmineConnector с URL: {url}")
            logger.info(
                f"Параметры: username={username}, password={'***' if password else None}, api_key={'***' if api_key else None}"
            )

            # ИСПРАВЛЕНИЕ: Отключаем проверку SSL и прокси для избежания ошибок подключения
            import requests
            # Жестко очищаем прокси из окружения (на случай если requests всё же подхватит)
            for _k in [
                'HTTP_PROXY','HTTPS_PROXY','NO_PROXY','ALL_PROXY',
                'http_proxy','https_proxy','no_proxy','all_proxy'
            ]:
                if os.environ.get(_k) is not None:
                    try:
                        del os.environ[_k]
                    except Exception:
                        pass

            session = requests.Session()
            session.verify = False
            # Полностью игнорируем прокси из env (http_proxy/https_proxy)
            session.trust_env = False
            # Отключаем использование прокси
            session.proxies.clear()
            # Используем пустые строки вместо None, чтобы удовлетворить типизатор
            session.proxies.update({'http': '', 'https': ''})
            # Устанавливаем таймауты для избежания зависания запросов
            # Таймауты будут передаваться в каждый запрос

            if username and password:
                logger.info(
                    f"Создание подключения к Redmine с именем пользователя: {username}"
                )
                self.redmine = Redmine(
                    url,
                    username=username,
                    password=password,
                    requests={"session": session, "timeout": 10},
                )
                logger.info(
                    "Инициализировано подключение к Redmine с использованием имени пользователя и пароля."
                )
            elif api_key:
                logger.info("Создание подключения к Redmine с API ключом")
                self.redmine = Redmine(
                    url,
                    key=api_key,
                    requests={"session": session, "timeout": 10},
                )
                logger.info(
                    "Инициализировано подключение к Redmine с использованием API ключа."
                )
            else:
                logger.error(
                    "Не предоставлены учетные данные для подключения к Redmine"
                )
                raise ValueError(
                    "Или (username, password) или api_key должны быть определены."
                )

            logger.info("RedmineConnector успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка при инициализации RedmineConnector: {e}")
            import traceback

            logger.error(f"Трассировка: {traceback.format_exc()}")
            raise

    def is_user_authenticated(self):
        try:
            logger.info("Проверка аутентификации пользователя в Redmine...")
            current_user = self.redmine.user.get("current")
            logger.info(
                f"Аутентификация успешна. Пользователь ID: {current_user.id}, Email: {getattr(current_user, 'mail', 'N/A')}"
            )
            return True
        except AuthError as auth_error:
            logger.error(f"Ошибка аутентификации (AuthError): {auth_error}")
            return False
        except ForbiddenError as forbidden_error:
            logger.error(f"Доступ запрещен (ForbiddenError): {forbidden_error}")
            return False
        except ResourceNotFoundError as not_found_error:
            logger.error(f"Ресурс не найден (ResourceNotFoundError): {not_found_error}")
            return False
        except BaseRedmineError as base_error:
            logger.error(f"Общая ошибка Redmine (BaseRedmineError): {base_error}")
            return False
        except Exception as general_error:
            logger.error(
                f"Неожиданная ошибка при проверке аутентификации: {general_error}"
            )
            import traceback

            logger.error(f"Трассировка: {traceback.format_exc()}")
            return False

    def get_current_user(self, user_id):
        try:
            user = self.redmine.user.get(user_id)
            return True, user  # Возвращаем True и пользователя, если операция успешна
        except BaseRedmineError as e:
            return (
                False,
                f"Ошибка при получении пользователя: {e}",
            )  # Возвращаем False и сообщение об ошибке в случае исключения

    def get_issue(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id)
            return True, issue
        except BaseRedmineError as e:
            return False, f"Ошибка при получении информации о заявке: {e}"

    def get_issue_status(self, issue_id):
        try:
            # Получаем объект заявки по её идентификатору
            issue = self.redmine.issue.get(issue_id)
            # Получаем текущий статус заявки
            current_status = issue.status.name
            return True, current_status
        except BaseRedmineError as e:
            return False, f"Ошибка при получении статуса заявки: {e}"

    def create_issue(self, subject, description, project_id, **kwargs):
        author_id = kwargs.get("author_id")
        file_paths = kwargs.get("file_path", [])
        easy_email_to = kwargs.get("easy_email_to")

        issue_data = {
            "project_id": project_id,
            "subject": subject,
            "description": description,
        }

        if author_id is not None:
            issue_data["author_id"] = author_id
            issue_data["easy_email_to"] = easy_email_to

        if file_paths:
            for file_path in file_paths:
                with open(file_path, "rb") as file:
                    filename = os.path.basename(file_path)
                    attachment = self.redmine.upload(file, filename=filename)
                if "uploads" not in issue_data:
                    issue_data["uploads"] = []
                issue_data["uploads"].append(
                    {"token": attachment["token"], "filename": filename}
                )
        return self.redmine.issue.create(**issue_data)

    def update_issue(self, issue_id, **kwargs):
        issue = self.redmine.issue.get(issue_id)
        for key, value in kwargs.items():
            setattr(issue, key, value)
        issue.save()
        return issue

    def update_issue_status_closed_on_open(self, issue_id, new_open_status_id):
        try:
            # Получаем объект заявки по её идентификатору
            issue = self.redmine.issue.get(issue_id)
            # Обновляем статус заявки
            if issue.status.id == 5:  # Если статус Закрыта переоткрываем заявку
                issue.status_id = new_open_status_id
                # Сохраняем изменения
                issue.save()
            return True, "Статус заявки успешно обновлен на Открыта"
        except pymysql.Error as e:
            logging.error("Ошибка при обновлении статуса заявки:: %s", str(e))
            return False, f"Ошибка при обновлении статуса заявки: {e}"

    def get_issue_history(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id, include="journals")
            # Возвращаем историю в обратном порядке (новые комментарии вверху)
            return list(reversed(issue.journals))
        except ResourceNotFoundError:
            logging.error(
                "Ошибка выполнения запроса к базе данных TEZ ERP: Заявка не найдена."
            )
            flash(f"Заявка с ID {issue_id} не существует или была удалена.", "error")
            return []  # Возвращаем пустой список истории
        except ForbiddenError:
            logging.error("Запрошенный ресурс запрещен:")
            # flash(f"Доступ к заявке с ID {issue_id} запрещен.", "error")
            return None  # Возвращаем пустой список истории

    def add_comment(self, issue_id, notes, user_id=None):
        try:
            # Логируем параметры
            print(f"[add_comment] Добавление комментария к задаче {issue_id}")
            print(f"[add_comment] user_id: {user_id}")
            print(f"[add_comment] notes: {notes[:100]}...")

            self.redmine.issue.update(issue_id, notes=notes)
            print(f"[add_comment] Комментарий добавлен через Redmine API")
        except BaseRedmineError as e:
            print(f"[add_comment] Ошибка Redmine API: {e}")
            return False, f"Ошибка при добавлении комментария в Redmine: {e}"

        if user_id is not None:
            try:
                print(f"[add_comment] Обновляем user_id в БД на {user_id}")
                conn = get_connection(
                    db_redmine_host,
                    db_redmine_user_name,
                    db_redmine_password,
                    db_redmine_name,
                )
                success, message = update_user_id(conn, user_id, issue_id)
                if not success:
                    print(f"[add_comment] Ошибка обновления user_id: {message}")
                    return False, message
                print(f"[add_comment] user_id успешно обновлен: {message}")
            except pymysql.Error as e:  # Перехватываем исключения, связанные с pymysql
                print(f"[add_comment] Ошибка БД: {e}")
                return False, f"Ошибка работы с базой данных: {e}"

        return True, "Комментарий успешно добавлен!"

    def get_issues_by_easy_email_to(self, easy_email_to_value):
        """
        Функция для получения задач из Redmine по полю easy_email_to.
        """
        filtered_issues = self.redmine.issue.filter(
            easy_email_to=easy_email_to_value,
            include=["id", "created_on", "subject", "status"],
        )
        return filtered_issues

    def get_issue_attachments(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id)
            attachments = issue.attachments
            attachment_list = []
            if attachments:
                for attachment in attachments:
                    attachment_list.append(
                        {
                            "filename": attachment.filename,
                            "url": attachment.content_url,
                            "author": attachment.author.name,
                            "created_on": attachment.created_on,
                        }
                    )
            return attachment_list
        except ResourceNotFoundError as e:
            logger.error("Error retrieving attachments for Issue #%s: %s", issue_id, e)
            return []
        except Exception as e:  # pylint: disable=broad-except
            logger.error("An unexpected error occurred: %s", e, exc_info=True)
            return []


def update_user_id(connection, redmine_user_id, redmine_issue_id):
    """Обновляем user_id для последнего добавленного комментария к задаче"""
    # Обновляем последний добавленный комментарий к задаче
    user_id_update = """UPDATE redmine.journals SET user_id = %s WHERE journalized_id = %s
                        AND journalized_type = 'Issue' AND notes IS NOT NULL AND notes != ''
                        ORDER BY created_on DESC LIMIT 1;"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(user_id_update, (redmine_user_id, redmine_issue_id))
            connection.commit()
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
        return False, f"Ошибка при обновлении user_id: {e}"
    return True, "user_id успешно обновлен!"


def check_user_active_redmine(connection, email_address):
    """Проверка по email пользователя, является ли пользователь активным пользователем Redmine?"""

    query = """ SELECT u.id as user_id
            FROM email_addresses ea
            INNER JOIN users u ON ea.user_id = u.id
            WHERE ea.address = %s AND u.status = 1 """
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, email_address)
        for row in cursor:
            return row["user_id"]
        return 4  # Если не является возвращаем user_id Аноним = 4
    except pymysql.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
        return None  # Возвращаем значение в случае исключения
    finally:
        if cursor is not None:
            cursor.close()


def get_issues_redmine_author_id(connection, author_id, easy_email_to):
    """Выборка заявок из Redmine по автору или email пользователя

    ИСПРАВЛЕНИЕ: Теперь корректно фильтруем заявки, принадлежащие пользователю.
    Заявка считается принадлежащей пользователю, если он является автором (author_id)
    ИЛИ указан в поле easy_email_to (для заявок, созданных от имени пользователя).
    """

    query = """
    SELECT i.id AS issue_id, i.updated_on AS updated_on, i.subject AS subject, us.name AS status_name, i.status_id AS status_id
    FROM issues i
    INNER JOIN u_statuses us ON i.status_id = us.id
    WHERE i.author_id = %s OR i.easy_email_to = %s
    ORDER BY i.updated_on DESC
    """

    issues_data = []

    try:
        with connection.cursor() as cursor:
            # ИСПРАВЛЕНИЕ: Используем точное сравнение для easy_email_to вместо LIKE
            # Это гарантирует, что будут выбраны только заявки, где пользователь явно указан
            cursor.execute(query, (author_id, easy_email_to))
            rows = cursor.fetchall()

            for row in rows:
                issues_data.append(
                    {
                        "id": row["issue_id"],
                        "updated_on": str(row["updated_on"]),
                        "subject": row["subject"],
                        "status_name": row["status_name"],
                        "status_id": row["status_id"],
                    }
                )

    except pymysql.MySQLError as e:
        print(f"{ERROR_MESSAGE} {e}")
        return None

    return issues_data


def get_notifications(user_id):
    """Выборка уведомлений об изменении статуса заявки"""
    # Получаем notifications
    notifications_data = Notifications.query.filter_by(user_id=user_id).all()
    return notifications_data


def get_notifications_add_notes(user_id):
    """Выборка уведомлений о добавлении комментариев"""
    # Получаем notifications
    notifications_add_notes_data = NotificationsAddNotes.query.filter_by(
        user_id=user_id
    ).all()
    return notifications_add_notes_data


def get_count_notifications(user_id):
    """Количество уведомлений об изменении статуса заявки"""
    # Получаем notifications
    notifications_data = Notifications.query.filter_by(user_id=user_id).all()
    notifications_count = len(notifications_data)
    return notifications_count


def get_count_notifications_add_notes(user_id):
    """Количество уведомлений о добавлении комментария в заявку"""
    # Получаем notifications
    notifications_add_notes_data = NotificationsAddNotes.query.filter_by(
        user_id=user_id
    ).all()
    notifications_add_notes_count = len(notifications_add_notes_data)
    return notifications_add_notes_count


def check_notifications(user_email, current_user_id):
    logger_main = current_app.logger
    run_id = uuid.uuid4()
    start_time_check = time.time()
    logger_main.info(
        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: НАЧАЛО проверки уведомлений."
    )

    connection_db = None
    cursor = None
    newly_processed_count = 0
    # Возвращаем словарь с деталями, включая ошибки
    processed_details = {
        "status_changes": 0,
        "added_notes": 0,
        "total_processed": 0,
        "errors": [],
    }

    try:
        logger_main.debug(
            f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка подключения к Redmine DB: host={db_redmine_host}, db={db_redmine_name}"
        )
        connect_start_time = time.time()
        connection_db = get_connection(
            db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name
        )
        connect_end_time = time.time()
        if connection_db is None:
            logger_main.error(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: НЕ УДАЛОСЬ подключиться к Redmine DB. Время: {connect_end_time - connect_start_time:.2f} сек."
            )
            processed_details["errors"].append("Redmine DB connection failed")
            # Не возвращаем 0, а обновляем детали и позволяем finally блоку отработать
            # return processed_details # Это прервет выполнение, лучше дать finally отработать
        else:
            logger_main.info(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Успешное подключение к Redmine DB. Время: {connect_end_time - connect_start_time:.2f} сек."
            )

            cursor_start_time = time.time()
            cursor = get_database_cursor(
                connection_db
            )  # get_database_cursor должен использовать current_app.logger или глобальный logger
            cursor_end_time = time.time()
            if cursor is None:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: НЕ УДАЛОСЬ получить курсор для Redmine DB. Время: {cursor_end_time - cursor_start_time:.2f} сек."
                )
                processed_details["errors"].append("Redmine DB cursor failed")
            else:
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Курсор Redmine DB получен. Время: {cursor_end_time - cursor_start_time:.2f} сек."
                )

                email_part = (
                    user_email.split("@")[0] if "@" in user_email else user_email
                )

                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Начало обработки status_changes."
                )
                process_status_start_time = time.time()
                # Передаем user_email как easy_email_to
                s_count, s_ids, s_errors = process_status_changes(
                    connection_db, cursor, email_part, current_user_id, user_email
                )
                process_status_end_time = time.time()
                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершена обработка status_changes. Найдено: {s_count}. Время: {process_status_end_time - process_status_start_time:.2f} сек."
                )
                processed_details["status_changes"] = s_count
                if s_errors:
                    processed_details["errors"].extend(s_errors)

                if s_count > 0:
                    newly_processed_count += s_count
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка удаления {len(s_ids)} обработанных status_changes из Redmine DB ID: {s_ids}"
                    )
                    delete_start_time = time.time()
                    delete_notifications(connection_db, s_ids)
                    delete_end_time = time.time()
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершено удаление status_changes. Время: {delete_end_time - delete_start_time:.2f} сек."
                    )

                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Начало обработки added_notes."
                )
                process_notes_start_time = time.time()
                n_count, n_ids, n_errors = process_added_notes(
                    connection_db, cursor, email_part, current_user_id, user_email
                )
                process_notes_end_time = time.time()
                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершена обработка added_notes. Найдено: {n_count}. Время: {process_notes_end_time - process_notes_start_time:.2f} сек."
                )
                processed_details["added_notes"] = n_count
                if n_errors:
                    processed_details["errors"].extend(n_errors)

                if n_count > 0:
                    newly_processed_count += n_count
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка удаления {len(n_ids)} обработанных added_notes из Redmine DB ID: {n_ids}"
                    )
                    delete_start_time = time.time()
                    delete_notifications_notes(connection_db, n_ids)
                    delete_end_time = time.time()
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершено удаление added_notes. Время: {delete_end_time - delete_start_time:.2f} сек."
                    )

        processed_details["total_processed"] = newly_processed_count

    except Exception as e:
        logger_main.error(
            f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: ГЛОБАЛЬНАЯ ОШИБКА. {e}",
            exc_info=True,
        )
        processed_details["errors"].append(
            f"Global error in check_notifications: {str(e)}"
        )
    finally:
        if cursor:
            try:
                cursor.close()
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Курсор Redmine DB закрыт."
                )
            except Exception as e_cursor:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Ошибка при закрытии курсора Redmine DB: {e_cursor}",
                    exc_info=True,
                )
        if connection_db:
            try:
                connection_db.close()
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Соединение Redmine DB закрыто."
                )
            except Exception as e_conn:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Ошибка при закрытии соединения Redmine DB: {e_conn}",
                    exc_info=True,
                )

        end_time_check = time.time()
        logger_main.info(
            f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: ЗАВЕРШЕНИЕ проверки уведомлений. Всего обработано: {newly_processed_count}. Детали: {processed_details}. Время: {end_time_check - start_time_check:.2f} сек."
        )
        return processed_details


def get_database_cursor(connection):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger
    try:
        return connection.cursor()
    except pymysql.Error as e:
        log.error("MYSQL_CURSOR: Ошибка получения курсора: %s", e, exc_info=True)
        return None
    except Exception as e_gen:  # Общее исключение
        log.error(
            "MYSQL_CURSOR: Непредвиденная ошибка получения курсора: %s",
            e_gen,
            exc_info=True,
        )
        return None


def execute_query(cursor, query, params=None):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger

    run_id = uuid.uuid4()
    func_name = "EXECUTE_QUERY"

    query_to_log = query.strip()[:250].replace("\\n", " ") + (
        "..." if len(query.strip()) > 250 else ""
    )
    log.debug(f"{func_name}_RUN_ID={run_id}: SQL='{query_to_log}', PARAMS={params}")

    start_time = time.time()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        end_time = time.time()
        log.info(
            f"{func_name}_RUN_ID={run_id}: Успешно. Найдено строк: {len(results) if results is not None else 'N/A'}. Время: {end_time - start_time:.3f} сек."
        )
        return results
    except pymysql.Error as e:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: ОШИБКА pymysql. {e}. SQL='{query_to_log}', PARAMS={params}. Время: {end_time - start_time:.3f} сек.",
            exc_info=True,
        )
        return None
    except Exception as e_generic:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: НЕПРЕДВИДЕННАЯ ОШИБКА. {e_generic}. SQL='{query_to_log}', PARAMS={params}. Время: {end_time - start_time:.3f} сек.",
            exc_info=True,
        )
        return None


def process_status_changes(
    connection, cursor, email_part, current_user_id, easy_email_to
):
    log = (
        current_app.logger
    )  # Переименовал logger на log для избежания конфликта с модулем logging
    run_id = uuid.uuid4()
    func_name = "PROCESS_STATUS_CHANGES"
    start_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: НАЧАЛО обработки."
    )

    query_status_change = """
        SELECT id, IssueID, NewStatus, OldStatus, DateCreated, Author, OldSubj, Body, RowDateCreated
        FROM u_its_update_status
        WHERE LOWER(Author) = LOWER(%s) # Возвращаем easy_email_to (полный email)
        ORDER BY RowDateCreated DESC LIMIT 50
    """
    log.debug(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQL Query to Redmine u_its_update_status for Author='{easy_email_to}'"
    )

    query_start_time = time.time()
    rows_status_change = execute_query(
        cursor, query_status_change, (easy_email_to,)
    )  # Возвращаем easy_email_to
    query_end_time = time.time()

    if rows_status_change is None:
        log.error(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка SQL-запроса к u_its_update_status. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return (
            0,
            [],
            [f"SQL query failed for u_its_update_status (Author: {easy_email_to})"],
        )

    found_count = len(rows_status_change)
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Найдено {found_count} записей в u_its_update_status. Время запроса: {query_end_time - query_start_time:.2f} сек."
    )

    processed_in_this_run = 0
    processed_ids_in_this_run = []
    errors_in_this_run = []

    user = User.query.get(current_user_id)
    if not user:
        log.warning(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Пользователь не найден в SQLite, PUSH не будут отправляться."
        )

    if rows_status_change:
        for row_data in rows_status_change:
            source_id = row_data["id"]
            issue_id = row_data["IssueID"]
            loop_start_time = time.time()
            log_row_data = {
                k: (str(v)[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
                for k, v in row_data.items()
            }
            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Обработка MySQL SourceID={source_id}, IssueID={issue_id}, Data: {log_row_data}"
            )

            try:
                with db.session.begin_nested():
                    existing_notification = Notifications.query.filter_by(
                        user_id=current_user_id,
                        issue_id=issue_id,
                        old_status=row_data["OldStatus"],
                        new_status=row_data["NewStatus"],
                        date_created=row_data["RowDateCreated"],
                    ).first()

                    if not existing_notification:
                        # Преобразование RowDateCreated в datetime, если это строка
                        date_created_dt = row_data["RowDateCreated"]
                        if isinstance(date_created_dt, str):
                            try:
                                date_created_dt = datetime.strptime(
                                    date_created_dt, "%Y-%m-%d %H:%M:%S"
                                )  # Формат MySQL
                            except ValueError:
                                try:
                                    date_created_dt = datetime.fromisoformat(
                                        date_created_dt
                                    )
                                except ValueError:
                                    log.error(
                                        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Не удалось преобразовать RowDateCreated='{row_data['RowDateCreated']}' в datetime для SourceID={source_id}"
                                    )
                                    date_created_dt = (
                                        datetime.now()
                                    )  # Фоллбэк или пропуск

                        new_notification_status = Notifications(
                            user_id=current_user_id,
                            issue_id=issue_id,
                            old_status=row_data["OldStatus"],
                            new_status=row_data["NewStatus"],
                            old_subj=row_data.get("OldSubj"),
                            date_created=date_created_dt,  # Используем преобразованную дату
                        )
                        db.session.add(new_notification_status)
                        db.session.flush()  # Flush чтобы получить new_notification_status.id для логов и потенциального использования

                        log.info(
                            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: ДОБАВЛЕНО уведомление о статусе. SourceID={source_id}, SQLiteID={new_notification_status.id}, IssueID={issue_id}."
                        )
                        processed_in_this_run += 1
                        processed_ids_in_this_run.append(source_id)

                        # ОТПРАВКА PUSH-УВЕДОМЛЕНИЯ
                        if (
                            user
                        ):  # Убедимся что пользователь есть (загружен ранее в функции)
                            try:
                                # Используем данные из new_notification_status (SQLite)
                                current_issue_id = new_notification_status.issue_id
                                new_status_id = new_notification_status.new_status
                                old_status_id = (
                                    new_notification_status.old_status
                                )  # на случай если понадобится

                                # Получаем имена статусов из Redmine DB, используя ID из SQLite
                                status_name_to = get_status_name_from_id(
                                    connection, new_status_id
                                )
                                status_name_from = get_status_name_from_id(
                                    connection, old_status_id
                                )

                                # Тему задачи берем из row_data (из Redmine u_its_update_status), т.к. ее нет в Notifications
                                subject = row_data.get("OldSubj", "Без темы")

                                title = f"Изменен статус задачи #{current_issue_id}"
                                # Формируем сообщение согласно требованию: "статус заявки номер X изменен на Y"
                                # Добавляем тему задачи для контекста, если это полезно
                                message = f"Статус задачи #{current_issue_id} ({subject}) изменен на '{status_name_to or new_status_id}'."

                                # Если нужно строго следовать "статус заявки номер X изменен на Y" без темы:
                                # message = f"Статус задачи #{current_issue_id} изменен на '{status_name_to or new_status_id}'."

                                # ИСПРАВЛЕНИЕ: Локальный импорт для избежания циклического импорта
                                from blog.notification_service import (
                                    NotificationData,
                                    NotificationType,
                                    WebPushException,
                                )

                                notification_payload_for_push = NotificationData(
                                    user_id=current_user_id,
                                    issue_id=current_issue_id,  # Используем current_issue_id
                                    notification_type=NotificationType.STATUS_CHANGE,
                                    title=title,
                                    message=message,
                                    data={
                                        "issue_id": current_issue_id,
                                        "old_status_id": old_status_id,
                                        "new_status_id": new_status_id,
                                        "old_status_name": status_name_from,
                                        "new_status_name": status_name_to,
                                        "subject": subject,
                                        "url": f"/my-issues/{current_issue_id}",  # ИЗМЕНЕНО ЗДЕСЬ
                                    },
                                    created_at=new_notification_status.date_created,
                                )
                                log.info(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Попытка PUSH для SQLiteID={new_notification_status.id}, IssueID={current_issue_id}. Payload: {notification_payload_for_push.to_dict()}"
                                )
                                # ИСПРАВЛЕНИЕ: Локальный импорт для избежания циклического импорта
                                from blog.notification_service import (
                                    notification_service,
                                )

                                push_service_instance = (
                                    notification_service.push_service
                                )
                                push_service_instance.send_push_notification(
                                    notification_payload_for_push
                                )
                                log.info(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: PUSH для SQLiteID={new_notification_status.id} ВЫЗВАН."
                                )

                            except AttributeError as e_attr:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка атрибута при доступе к push_service для SQLiteID={new_notification_status.id}. {e_attr}",
                                    exc_info=True,
                                )
                                errors_in_this_run.append(
                                    f"Push service attribute error for SourceID={source_id}: {str(e_attr)}"
                                )
                            except WebPushException as e_wp:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА WebPushException для SQLiteID={new_notification_status.id}. {e_wp}",
                                    exc_info=True,
                                )
                                errors_in_this_run.append(
                                    f"WebPushException for SourceID={source_id}: {str(e_wp)}"
                                )
                            except Exception as e_push:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА PUSH для SQLiteID={new_notification_status.id}. {e_push}",
                                    exc_info=True,
                                )
                                errors_in_this_run.append(
                                    f"Push failed for SourceID={source_id}: {str(e_push)}"
                                )
                        else:
                            log.warning(
                                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Пользователь не найден, PUSH не отправлен для SQLiteID={new_notification_status.id}."
                            )

            except Exception as e_row:
                log.error(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА обработки MySQL SourceID={source_id}, IssueID={issue_id}. {e_row}",
                    exc_info=True,
                )
                errors_in_this_run.append(
                    f"Processing MySQL status row SourceID={source_id} failed: {str(e_row)}"
                )

            loop_end_time = time.time()
            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Завершение обработки MySQL SourceID={source_id}. Время: {loop_end_time - loop_start_time:.2f} сек."
            )

        if processed_in_this_run > 0:
            try:
                db.session.commit()
                log.info(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: Финальный коммит {processed_in_this_run} новых уведомлений о статусах."
                )
            except Exception as e_final_commit:
                log.error(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: ОШИБКА финального коммита. {e_final_commit}",
                    exc_info=True,
                )
                errors_in_this_run.append(
                    f"Final commit for status changes failed: {str(e_final_commit)}"
                )
                db.session.rollback()

    end_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: ЗАВЕРШЕНИЕ обработки. Обработано: {processed_in_this_run}. ID для MySQL удаления: {processed_ids_in_this_run}. Ошибки: {len(errors_in_this_run)}. Время: {end_time_func - start_time_func:.2f} сек."
    )
    return processed_in_this_run, processed_ids_in_this_run, errors_in_this_run


def process_added_notes(connection, cursor, email_part, current_user_id, easy_email_to):
    log = current_app.logger
    run_id = uuid.uuid4()
    func_name = "PROCESS_ADDED_NOTES"
    start_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: НАЧАЛО обработки."
    )

    query_added_notes = """
        SELECT id, issue_id, date_created, Notes, Author, RowDateCreated
        FROM u_its_add_notes
        WHERE LOWER(Author) = LOWER(%s) # Возвращаем easy_email_to (полный email)
        ORDER BY RowDateCreated DESC LIMIT 50
    """
    log.debug(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQL Query to Redmine u_its_add_notes for Author='{easy_email_to}'"
    )

    query_start_time = time.time()
    rows_added_notes = execute_query(
        cursor, query_added_notes, (easy_email_to,)
    )  # Возвращаем easy_email_to
    query_end_time = time.time()

    if rows_added_notes is None:
        log.error(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка SQL-запроса к u_its_add_notes. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return (
            0,
            [],
            [f"SQL query failed for u_its_add_notes (Author: {easy_email_to})"],
        )

    found_count = len(rows_added_notes)
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Найдено {found_count} записей в u_its_add_notes. Время запроса: {query_end_time - query_start_time:.2f} сек."
    )

    processed_in_this_run = 0
    processed_ids_in_this_run = []
    errors_in_this_run_notes = []

    user = User.query.get(current_user_id)
    if not user:
        log.warning(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Пользователь не найден в SQLite, PUSH (комментарии) не будут отправляться."
        )

    if rows_added_notes:
        for row_add_notes in rows_added_notes:
            source_id_notes = row_add_notes["id"]
            issue_id_notes = row_add_notes["issue_id"]
            loop_start_time = time.time()
            log_row_data = {
                "Author": row_add_notes.get("Author"),
                "RowDateCreated": row_add_notes.get("RowDateCreated"),
                "Notes_len": len(row_add_notes.get("Notes", "")),
            }
            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Обработка MySQL SourceID={source_id_notes}, IssueID={issue_id_notes}, Data: {log_row_data}"
            )

            try:
                with db.session.begin_nested():
                    existing_note = NotificationsAddNotes.query.filter_by(
                        user_id=current_user_id,
                        issue_id=issue_id_notes,
                        author=row_add_notes["Author"],
                        notes=row_add_notes["Notes"],
                        date_created=row_add_notes["date_created"],
                    ).first()

                    if not existing_note:
                        # Преобразование date_created из строки u_its_add_notes в datetime
                        date_created_str = row_add_notes["date_created"]
                        date_created_dt = None
                        if date_created_str:
                            if isinstance(
                                date_created_str, datetime
                            ):  # Если уже datetime (маловероятно из DictCursor, но проверим)
                                date_created_dt = date_created_str
                            else:
                                try:
                                    # MySQL обычно возвращает datetime, но если это строка, парсим
                                    # Попробуем несколько распространенных форматов или ISO
                                    # Логи показывают 'YYYY-MM-DD HH:MM:SS'
                                    date_created_dt = datetime.strptime(
                                        date_created_str, "%Y-%m-%d %H:%M:%S"
                                    )
                                except ValueError:
                                    try:
                                        date_created_dt = datetime.fromisoformat(
                                            date_created_str
                                        )
                                    except ValueError:
                                        log.error(
                                            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Не удалось преобразовать date_created='{date_created_str}' в datetime для SourceID={source_id_notes}"
                                        )
                                        # Можно установить текущее время или пропустить запись, в зависимости от бизнес-логики
                                        # В данном случае, если дата невалидна, лучше пропустить или залогировать и обработать ошибку
                                        # пока оставляем None, что может привести к ошибке БД если поле NOT NULL без default
                                        # Модель NotificationsAddNotes.date_created = db.Column(db.DateTime), так что None может быть проблемой
                                        # Если поле date_created обязательно, то здесь нужно либо кидать ошибку, либо использовать фоллбэк
                                        # errors_in_this_run_notes.append(f"Invalid date_format for comment SourceID={source_id_notes}")
                                        # continue # Пропустить эту запись
                                        date_created_dt = (
                                            datetime.now()
                                        )  # Временный фоллбек, чтобы избежать None для DateTime поля
                        else:
                            log.warning(
                                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: date_created is None for SourceID={source_id_notes}. Используем текущее время."
                            )
                            date_created_dt = (
                                datetime.now()
                            )  # Фоллбэк, если дата отсутствует

                        new_notification_add_notes = NotificationsAddNotes(
                            user_id=current_user_id,
                            issue_id=issue_id_notes,
                            author=row_add_notes["Author"],
                            notes=row_add_notes["Notes"],
                            date_created=date_created_dt,  # Используем преобразованную или текущую дату
                            source_id=source_id_notes,
                        )
                        db.session.add(new_notification_add_notes)
                        db.session.flush()  # Чтобы получить ID до коммита, если нужно

                        log.info(
                            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: ДОБАВЛЕНО уведомление о комментарии. SourceID={source_id_notes}, SQLiteID={new_notification_add_notes.id}, IssueID={issue_id_notes}."
                        )
                        processed_in_this_run += 1
                        processed_ids_in_this_run.append(source_id_notes)

                        # ОТПРАВКА PUSH-УВЕДОМЛЕНИЯ О НОВОМ КОММЕНТАРИИ
                        if (
                            user
                        ):  # Убедимся что пользователь есть (загружен ранее в функции)
                            try:
                                title = f"Новый комментарий к задаче #{issue_id_notes}"
                                comment_preview = row_add_notes["Notes"]
                                if len(comment_preview) > 100:
                                    comment_preview = comment_preview[:97] + "..."

                                message = f'К задаче #{issue_id_notes} добавлен новый комментарий: "{comment_preview}".'

                                # ИСПРАВЛЕНИЕ: Локальный импорт для избежания циклического импорта
                                from blog.notification_service import (
                                    NotificationData,
                                    NotificationType,
                                    WebPushException,
                                )

                                notification_payload_for_push = NotificationData(
                                    user_id=current_user_id,
                                    issue_id=issue_id_notes,
                                    notification_type=NotificationType.COMMENT_ADDED,
                                    title=title,
                                    message=message,
                                    data={
                                        "issue_id": issue_id_notes,
                                        "comment_body_preview": comment_preview,
                                        "author_comment": row_add_notes["Author"],
                                        "url": f"/my-issues/{issue_id_notes}",
                                        "comment_added_at": date_created_dt.isoformat(),
                                    },
                                    created_at=new_notification_add_notes.date_created,
                                )
                                log.info(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Попытка PUSH для SQLiteID={new_notification_add_notes.id} (комментарий). Payload: {notification_payload_for_push.to_dict()}"
                                )
                                # ИСПРАВЛЕНИЕ: Локальный импорт для избежания циклического импорта
                                from blog.notification_service import (
                                    notification_service,
                                )

                                push_service_instance = (
                                    notification_service.push_service
                                )
                                push_service_instance.send_push_notification(
                                    notification_payload_for_push
                                )
                                log.info(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: PUSH для SQLiteID={new_notification_add_notes.id} (комментарий) ВЫЗВАН."
                                )

                            except AttributeError as e_attr:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка атрибута при доступе к push_service для SQLiteID={new_notification_add_notes.id} (комментарий). {e_attr}",
                                    exc_info=True,
                                )
                                errors_in_this_run_notes.append(
                                    f"Push service attribute error for SourceID={source_id_notes} (comment): {str(e_attr)}"
                                )
                            except WebPushException as e_wp:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА WebPushException для SQLiteID={new_notification_add_notes.id} (комментарий). {e_wp}",
                                    exc_info=True,
                                )
                                errors_in_this_run_notes.append(
                                    f"WebPushException for SourceID={source_id_notes} (comment): {str(e_wp)}"
                                )
                            except Exception as e_push:
                                log.error(
                                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА PUSH для SQLiteID={new_notification_add_notes.id} (комментарий). {e_push}",
                                    exc_info=True,
                                )
                                errors_in_this_run_notes.append(
                                    f"Push failed for SourceID={source_id_notes} (comment): {str(e_push)}"
                                )
                        else:
                            log.warning(
                                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Пользователь не найден, PUSH не отправлен для SQLiteID={new_notification_add_notes.id} (комментарий)."
                            )

            except Exception as e_row_notes:
                log.error(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: ОШИБКА обработки MySQL SourceID={source_id_notes}, IssueID={issue_id_notes} (комментарий). {e_row_notes}",
                    exc_info=True,
                )
                errors_in_this_run_notes.append(
                    f"Processing MySQL comment row SourceID={source_id_notes} failed: {str(e_row_notes)}"
                )

            loop_end_time = time.time()
            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Завершение обработки MySQL SourceID={source_id_notes} (комментарий). Время: {loop_end_time - loop_start_time:.2f} сек."
            )

        if processed_in_this_run > 0:
            try:
                db.session.commit()
                log.info(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: Финальный коммит {processed_in_this_run} новых уведомлений о комментариях."
                )
            except Exception as e_final_commit:
                log.error(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQLite: ОШИБКА финального коммита (комментарии). {e_final_commit}",
                    exc_info=True,
                )
                errors_in_this_run_notes.append(
                    f"Final commit for added notes failed: {str(e_final_commit)}"
                )
                db.session.rollback()

    end_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: ЗАВЕРШЕНИЕ обработки (комментарии). Обработано: {processed_in_this_run}. ID для MySQL удаления: {processed_ids_in_this_run}. Ошибки: {len(errors_in_this_run_notes)}. Время: {end_time_func - start_time_func:.2f} сек."
    )
    return processed_in_this_run, processed_ids_in_this_run, errors_in_this_run_notes


def delete_notifications(connection, ids_to_delete):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger
    run_id = uuid.uuid4()
    func_name = "DELETE_NOTIFICATIONS_STATUS"
    start_time = time.time()

    if not ids_to_delete:
        log.info(f"{func_name}_RUN_ID={run_id}: Список ID для удаления пуст.")
        return

    log.info(
        f"{func_name}_RUN_ID={run_id}: НАЧАЛО удаления {len(ids_to_delete)} записей из u_its_update_status. IDs: {ids_to_delete}"
    )
    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(ids_to_delete))
        query = f"DELETE FROM u_its_update_status WHERE id IN ({placeholders})"
        log.debug(
            f"{func_name}_RUN_ID={run_id}: SQL='{query}', IDs={tuple(ids_to_delete)}"
        )

        cursor.execute(query, tuple(ids_to_delete))
        connection.commit()
        deleted_count = cursor.rowcount
        end_time = time.time()
        log.info(
            f"{func_name}_RUN_ID={run_id}: Успешно удалено {deleted_count} записей. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек."
        )
    except pymysql.Error as e:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: ОШИБКА pymysql. {e}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
    except Exception as e_generic:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: НЕПРЕДВИДЕННАЯ ОШИБКА. {e_generic}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()


def delete_notifications_notes(connection, ids_to_delete):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger
    run_id = uuid.uuid4()
    func_name = "DELETE_NOTIFICATIONS_NOTES"
    start_time = time.time()

    if not ids_to_delete:
        log.info(f"{func_name}_RUN_ID={run_id}: Список ID для удаления пуст.")
        return

    log.info(
        f"{func_name}_RUN_ID={run_id}: НАЧАЛО удаления {len(ids_to_delete)} записей из u_its_add_notes. IDs: {ids_to_delete}"
    )
    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(ids_to_delete))
        query = f"DELETE FROM u_its_add_notes WHERE id IN ({placeholders})"
        log.debug(
            f"{func_name}_RUN_ID={run_id}: SQL='{query}', IDs={tuple(ids_to_delete)}"
        )

        cursor.execute(query, tuple(ids_to_delete))
        connection.commit()
        deleted_count = cursor.rowcount
        end_time = time.time()
        log.info(
            f"{func_name}_RUN_ID={run_id}: Успешно удалено {deleted_count} записей. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек."
        )
    except pymysql.Error as e:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: ОШИБКА pymysql. {e}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
    except Exception as e_generic:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: НЕПРЕДВИДЕННАЯ ОШИБКА. {e_generic}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()


def save_and_get_filepath(upload_files_data):
    file_paths = []
    if upload_files_data:
        for uploaded_file in upload_files_data:
            # Создаем временный каталог
            temp_dir = tempfile.mkdtemp()
            # Получаем имя файла
            filename = secure_filename(uploaded_file.filename)
            # Формируем путь для сохранения файла во временной папке
            temp_file_path = os.path.join(temp_dir, filename)
            # Сохраняем файл на диск
            uploaded_file.save(temp_file_path)
            # Добавляем путь к сохраненному файлу в список
            file_paths.append(temp_file_path)
    return file_paths


def generate_email_signature(user):
    """
    email HTML подпись пользователя

    Аргументы:
        user (dict): Включают full_name, position, department, phone, and email

    Возвращает:
        str: HTML код email подписи
    """
    email_signature = f"""
    <div class="email-signature-frame float-right" style="border: none;">
        <p style="font-family: Tahoma, Verdana, Arial, sans-serif; font-size: 13px; color: #25252;">С уважением,<br>
        <b>{user['full_name']}</b></p>
        <p style="font-family: Tahoma, Verdana, Arial, sans-serif; font-size: 12px; color: #25252;">{user['position']}<br>
        {user['department']}</p>
        <div style="border-top: 1px solid #252525;"></div><br> <!-- Подчеркивание -->
        <a href="http://www.tez-tour.com/" target="_blank"><img src="http://s.tez-tour.com/article/50001388/teztour_mail_signature_logo_3129.gif" width="150" height="40" border="0"></a><br>
        Тел: внутр. {user['phone']}<br>
        <a href="mailto:{user['email']}">{user['email']}</a><br>
        <a href="http://www.tez-tour.com">www.tez-tour.com </a><br>
    </div>
    """
    return email_signature


def get_redmine_admin_instance():
    """
    Создает и возвращает экземпляр Redmine API клиента,
    аутентифицированный с использованием административного API ключа.
    """
    try:
        # Создаем сессию без прокси для избежания ошибок подключения
        import requests

        session = requests.Session()
        session.verify = False
        # Полностью игнорируем прокси из env (http_proxy/https_proxy)
        session.trust_env = False
        session.proxies.clear()
        # Таймауты будут передаваться в каждый запрос

        return Redmine(
            REDMINE_URL, key=REDMINE_ADMIN_API_KEY, requests={"session": session}
        )
    except Exception as e:
        logger.error(f"Ошибка при создании экземпляра Redmine API: {e}")
        return None


def fetch_redmine_raw_updates(redmine_instance, last_run_timestamp: datetime):
    """
    Получает "сырые" обновления из Redmine API с момента last_run_timestamp.

    Запрашивает задачи, обновленные с last_run_timestamp, и для каждой из них
    запрашивает записи журнала, созданные после last_run_timestamp.

    Args:
        redmine_instance: Активный экземпляр Redmine API клиента.
        last_run_timestamp: datetime объект, указывающий время последнего успешного запуска.

    Returns:
        Список словарей, где каждый словарь представляет "сырое событие"
        (например, новый комментарий или изменение статуса).
        Структура событий:
        {
            'type': 'comment' | 'status_change' | ...,
            'issue_id': int,
            'journal_id': int, (ID записи журнала)
            'user_id': int, (ID пользователя Redmine, совершившего действие)
            'created_on': datetime, (время создания записи журнала)
            'notes': str, (текст комментария, если есть)
            'details': list (детали изменений атрибутов)
            'issue_author_id': int,
            'issue_assigned_to_id': int (может отсутствовать)
        }
        Возвращает пустой список в случае ошибки или отсутствия обновлений.
    """
    if not redmine_instance:
        logger.error("Экземпляр Redmine не предоставлен для fetch_redmine_raw_updates.")
        return []

    raw_events = []
    try:
        # Форматируем временную метку для API Redmine (ISO 8601)
        # Redmine ожидает UTC, убедимся, что last_run_timestamp в UTC или конвертируем
        if last_run_timestamp.tzinfo is None:
            # Если таймзона не указана, предполагаем, что это UTC, но лучше явно указывать
            # import pytz # Потребуется pytz
            # last_run_timestamp = pytz.utc.localize(last_run_timestamp)
            # Для простоты пока оставим как есть, но это ВАЖНЫЙ момент для корректной работы с разными часовыми поясами
            # redminelib обычно ожидает строки в формате ISO
            logger.warning(
                "last_run_timestamp не имеет информации о часовом поясе. Предполагается UTC."
            )

        # Redmine API ожидает время в UTC. Если last_run_timestamp локальное, его нужно конвертировать в UTC.
        # Для простоты примера, предположим, что last_run_timestamp уже в UTC или redminelib корректно его обработает.
        # Убедимся, что передаем строку в ISO формате, redminelib >= 2.3.0 должен принимать datetime объекты напрямую.
        # Если версия старее, может потребоваться last_run_timestamp.isoformat()

        logger.info(
            f"Запрос задач, обновленных после: {last_run_timestamp.isoformat()}"
        )

        # Используем f-строку для корректной передачи datetime в redminelib,
        # если он не справляется с datetime объектом напрямую для фильтрации.
        # 일반적으로 redminelib 은 datetime 객체를 올바르게 처리해야 합니다.
        updated_issues = redmine_instance.issue.filter(
            updated_on=f">{last_run_timestamp.isoformat()}",  # Передача строки может быть надежнее
            status_id="*",  # все статусы
            sort="updated_on:asc",
        )

        processed_journal_ids = set()

        for issue in updated_issues:
            logger.debug(
                f"Обработка обновленной задачи ID: {issue.id}, обновлена: {issue.updated_on}"
            )
            try:
                # issue.journals загружает все журналы. Мы должны фильтровать их по дате.
                for (
                    journal_entry
                ) in (
                    issue.journals
                ):  # Переименовал journal в journal_entry во избежание конфликта имен, если есть модуль journal
                    journal_created_on = journal_entry.created_on

                    if journal_entry.id in processed_journal_ids:
                        continue

                    # Сравнение дат: journal_created_on (от redminelib, обычно UTC) и last_run_timestamp (предполагаем UTC)
                    if journal_created_on > last_run_timestamp:
                        processed_journal_ids.add(journal_entry.id)
                        event_data = {
                            "issue_id": issue.id,
                            "journal_id": journal_entry.id,
                            "user_id": (
                                journal_entry.user.id
                                if hasattr(journal_entry, "user") and journal_entry.user
                                else ANONYMOUS_USER_ID_CONFIG
                            ),
                            "created_on": journal_created_on,
                            "notes": getattr(journal_entry, "notes", ""),
                            "details": getattr(journal_entry, "details", []),
                            "issue_author_id": (
                                issue.author.id
                                if hasattr(issue, "author") and issue.author
                                else ANONYMOUS_USER_ID_CONFIG
                            ),
                            "issue_assigned_to_id": (
                                issue.assigned_to.id
                                if hasattr(issue, "assigned_to") and issue.assigned_to
                                else None
                            ),
                            "project_id": (
                                issue.project.id
                                if hasattr(issue, "project") and issue.project
                                else None
                            ),
                            "tracker_id": (
                                issue.tracker.id
                                if hasattr(issue, "tracker") and issue.tracker
                                else None
                            ),
                            "status_id": (
                                issue.status.id
                                if hasattr(issue, "status") and issue.status
                                else None
                            ),
                            "subject": getattr(issue, "subject", ""),
                        }
                        raw_events.append(event_data)
                        logger.debug(
                            f"  Добавлено событие из журнала ID: {journal_entry.id} для задачи {issue.id}"
                        )

            except ResourceNotFoundError:
                logger.warning(
                    f"Задача {issue.id} не найдена при попытке получить журналы (возможно, удалена). Пропускаем."
                )
                continue
            except Exception as e_journal:
                logger.error(
                    f"Ошибка при обработке журналов для задачи {issue.id}: {e_journal}"
                )
                continue

        logger.info(f"Найдено {len(raw_events)} сырых событий Redmine.")
        return raw_events

    except AuthError:
        logger.error("Ошибка аутентификации при запросе к Redmine API.")
        return []
    except ForbiddenError:
        logger.error(
            "Доступ запрещен при запросе к Redmine API (проверьте права API ключа)."
        )
        return []
    # Убрал ConnectionError, так как BaseRedmineError должен его покрывать или redminelib кидает свои типы
    except BaseRedmineError as e_base:
        logger.error(f"Общая ошибка Redmine API (redminelib): {e_base}")
        return []
    except Exception as e:
        logger.error(
            f"Неожиданная ошибка в fetch_redmine_raw_updates: {e}", exc_info=True
        )
        return []


def monitor_performance(operation_name):
    """Декоратор для мониторинга производительности функций"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed = end_time - start_time

                if elapsed > 1.0:  # Логируем только медленные операции
                    logger.warning(f"PERFORMANCE: {operation_name} took {elapsed:.2f}s")
                else:
                    logger.info(f"PERFORMANCE: {operation_name} took {elapsed:.3f}s")

                return result
            except Exception as e:
                end_time = time.time()
                logger.error(
                    f"PERFORMANCE ERROR: {operation_name} failed after {end_time - start_time:.2f}s: {e}"
                )
                raise

        return wrapper

    return decorator


# Применение к функциям
@monitor_performance("get_multiple_user_names")
def get_multiple_user_names(connection, user_ids):
    """
    Пакетная загрузка имен пользователей по списку ID

    Args:
        connection: Соединение с БД MySQL
        user_ids: Список ID пользователей

    Returns:
        dict: Словарь {user_id: full_name}
    """
    if not user_ids or not connection:
        return {}

    # Удаляем дубликаты и None значения
    clean_ids = list(set(filter(None, user_ids)))
    if not clean_ids:
        return {}

    # Создаем плейсхолдеры для параметризованного запроса
    placeholders = ",".join(["%s"] * len(clean_ids))
    sql = f"""
        SELECT id, CONCAT(IFNULL(lastname, ''), ' ', IFNULL(firstname, '')) AS full_name
        FROM users
        WHERE id IN ({placeholders})
    """

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["full_name"].strip()
        logger.info(
            f"Загружено {len(result)} имен пользователей из {len(clean_ids)} запрошенных"
        )
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке имен пользователей: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_project_names(connection, project_ids):
    """
    Пакетная загрузка названий проектов по списку ID

    Args:
        connection: Соединение с БД MySQL
        project_ids: Список ID проектов

    Returns:
        dict: Словарь {project_id: name}
    """
    if not project_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, project_ids)))
    if not clean_ids:
        return {}

    placeholders = ",".join(["%s"] * len(clean_ids))
    sql = (
        f"SELECT id, IFNULL(name,'') as name FROM projects WHERE id IN ({placeholders})"
    )

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        logger.info(
            f"Загружено {len(result)} названий проектов из {len(clean_ids)} запрошенных"
        )
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий проектов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_status_names(connection, status_ids):
    """
    Пакетная загрузка названий статусов по списку ID

    Args:
        connection: Соединение с БД MySQL
        status_ids: Список ID статусов

    Returns:
        dict: Словарь {status_id: name}
    """
    if not status_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, status_ids)))
    if not clean_ids:
        return {}

    placeholders = ",".join(["%s"] * len(clean_ids))
    sql = f"SELECT id, IFNULL(name,'') as name FROM u_statuses WHERE id IN ({placeholders})"

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        logger.info(
            f"Загружено {len(result)} названий статусов из {len(clean_ids)} запрошенных"
        )
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий статусов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_priority_names(connection, priority_ids):
    """
    Пакетная загрузка названий приоритетов по списку ID

    Args:
        connection: Соединение с БД MySQL
        priority_ids: Список ID приоритетов

    Returns:
        dict: Словарь {priority_id: name}
    """
    if not priority_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, priority_ids)))
    if not clean_ids:
        return {}

    placeholders = ",".join(["%s"] * len(clean_ids))
    sql = f"SELECT id, IFNULL(name,'') as name FROM u_Priority WHERE id IN ({placeholders})"

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        logger.info(
            f"Загружено {len(result)} названий приоритетов из {len(clean_ids)} запрошенных"
        )
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий приоритетов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()


def generate_optimized_property_names(connection, issue_history):
    """
    Оптимизированная генерация описаний изменений для истории заявки.
    Использует пакетную загрузку вместо множественных запросов к БД.

    Args:
        connection: Соединение с БД MySQL
        issue_history: История изменений заявки

    Returns:
        dict: Словарь с предгенерированными описаниями изменений
        Ключ: "{property}:{name}:{old_value}:{new_value}"
        Значение: HTML-описание изменения
    """
    if not issue_history or not connection:
        return {}

    # Собираем все уникальные ID для пакетной загрузки
    user_ids = set()
    project_ids = set()
    status_ids = set()
    priority_ids = set()

    # Проходим по всей истории и собираем ID
    for journal_entry in issue_history:
        if hasattr(journal_entry, "details"):
            for detail in journal_entry.details:
                prop_name = detail.get("name", "")
                old_value = detail.get("old_value")
                new_value = detail.get("new_value")

                if prop_name == "assigned_to_id":
                    if old_value:
                        user_ids.add(int(old_value))
                    if new_value:
                        user_ids.add(int(new_value))
                elif prop_name == "project_id":
                    if old_value:
                        project_ids.add(int(old_value))
                    if new_value:
                        project_ids.add(int(new_value))
                elif prop_name == "status_id":
                    if old_value:
                        status_ids.add(int(old_value))
                    if new_value:
                        status_ids.add(int(new_value))
                elif prop_name == "priority_id":
                    if old_value:
                        priority_ids.add(int(old_value))
                    if new_value:
                        priority_ids.add(int(new_value))

    # Пакетная загрузка всех данных одним запросом к БД
    logger.info(
        f"Начинаем пакетную загрузку: users={len(user_ids)}, projects={len(project_ids)}, statuses={len(status_ids)}, priorities={len(priority_ids)}"
    )

    user_names = get_multiple_user_names(connection, list(user_ids))
    project_names = get_multiple_project_names(connection, list(project_ids))
    status_names = get_multiple_status_names(connection, list(status_ids))
    priority_names = get_multiple_priority_names(connection, list(priority_ids))

    # Генерируем описания изменений
    property_descriptions = {}

    for journal_entry in issue_history:
        if hasattr(journal_entry, "details"):
            for detail in journal_entry.details:
                property_name = detail.get("property", "attr")
                prop_key = detail.get("name", "")
                old_value = detail.get("old_value")
                new_value = detail.get("new_value")

                # Создаем уникальный ключ для кеширования
                cache_key = f"{property_name}:{prop_key}:{old_value}:{new_value}"

                if cache_key in property_descriptions:
                    continue  # Уже обработано

                # Генерируем описание на основе предзагруженных данных
                result = None

                if prop_key == "project_id":
                    project_from = project_names.get(
                        int(old_value) if old_value else None, "None"
                    )
                    project_to = project_names.get(
                        int(new_value) if new_value else None, "None"
                    )
                    result = f"Параметр&nbsp;<b>Проект</b>&nbsp;изменился&nbsp;c&nbsp;<b>{project_from}</b>&nbsp;на&nbsp;<b>{project_to}</b>"

                elif prop_key == "assigned_to_id":
                    assigned_from = user_names.get(
                        int(old_value) if old_value else None, "None"
                    )
                    assigned_to = user_names.get(
                        int(new_value) if new_value else None, "None"
                    )
                    result = f"Параметр&nbsp;<b>Назначена</b>&nbsp;изменился&nbsp;c&nbsp;<b>{assigned_from}</b>&nbsp;на&nbsp;<b>{assigned_to}</b>"

                elif prop_key == "status_id":
                    status_from = status_names.get(
                        int(old_value) if old_value else None, "Неизвестно"
                    )
                    status_to = status_names.get(
                        int(new_value) if new_value else None, "Неизвестно"
                    )
                    result = f"Параметр&nbsp;<b>Статус</b>&nbsp;изменился&nbsp;c&nbsp;<b>{status_from}</b>&nbsp;на&nbsp;<b>{status_to}</b>"

                elif prop_key == "priority_id":
                    priority_from = priority_names.get(
                        int(old_value) if old_value else None, "Неизвестно"
                    )
                    priority_to = priority_names.get(
                        int(new_value) if new_value else None, "Неизвестно"
                    )
                    result = f"Параметр&nbsp;<b>Приоритет</b>&nbsp;изменился&nbsp;c&nbsp;<b>{priority_from}</b>&nbsp;на&nbsp;<b>{priority_to}</b>"

                elif prop_key == "subject":
                    result = f"Параметр&nbsp;<b>Тема</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_value}</b>&nbsp;на&nbsp;<b>{new_value}</b>"

                elif prop_key == "easy_helpdesk_need_reaction":
                    old_reaction = "Да" if old_value == "1" else "Нет"
                    new_reaction = "Да" if new_value == "1" else "Нет"
                    result = f"Параметр&nbsp;<b>Нужна&nbsp;реакция?</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_reaction}</b>&nbsp;на&nbsp;<b>{new_reaction}</b>"

                elif prop_key == "done_ratio":
                    result = f"Параметр&nbsp;<b>Готовность</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_value}%</b>&nbsp;на&nbsp;<b>{new_value}%</b>"

                elif prop_key == "16":  # Кастомное поле "Что нового"
                    if old_value and not new_value:
                        old_text = "Да" if str(old_value) != "0" else "Нет"
                        result = f"Значение&nbsp;<b>{old_text}</b>&nbsp;параметра&nbsp;<b>Что&nbsp;нового</b>&nbsp;удалено"
                    elif not old_value and new_value:
                        new_text = "Да" if str(new_value) != "0" else "Нет"
                        result = f"Параметр&nbsp;<b>Что&nbsp;нового</b>&nbsp;изменился&nbsp;на&nbsp;<b>{new_text}</b>"
                    else:
                        old_text = (
                            "Да" if old_value and str(old_value) != "0" else "Нет"
                        )
                        new_text = (
                            "Да" if new_value and str(new_value) != "0" else "Нет"
                        )
                        result = f"Параметр&nbsp;<b>Что&nbsp;нового</b>&nbsp;изменился&nbsp;c&nbsp;<b>{old_text}</b>&nbsp;на&nbsp;<b>{new_text}</b>"

                elif property_name == "attachment":
                    result = f"Файл&nbsp;<b>{new_value}</b>&nbsp;добавлен"

                elif property_name == "relation" and prop_key == "relates":
                    result = f"Задача&nbsp;связана&nbsp;с&nbsp;задачей&nbsp;<b>#{new_value}</b>"

                elif (
                    prop_key == "subtask" and property_name == "relation" and new_value
                ):
                    result = f"Добавлена&nbsp;подзадача&nbsp;<b>#{new_value}</b>"

                # Сохраняем результат в кеш
                if result:
                    property_descriptions[cache_key] = result

    logger.info(f"Сгенерировано {len(property_descriptions)} описаний изменений")
    return property_descriptions




def determine_activity_type(property_name, prop_key, old_value, value, notes):
    """
    Определение типа активности на основе данных из journals

    Returns:
        tuple: (activity_type, activity_icon, activity_text)
    """
    # Если есть комментарий (notes)
    if notes and notes.strip():
        return ("comment", "💬", "Добавлен комментарий")

    # Если это изменение атрибута
    if property_name == "attr":
        if prop_key == "status_id":
            return ("status", "🔄", "Изменен статус")
        elif prop_key == "priority_id":
            return ("priority", "⚡", "Изменен приоритет")
        elif prop_key == "assigned_to_id":
            return ("assigned", "👤", "Изменен исполнитель")
        elif prop_key == "description":
            return ("description", "📝", "Обновлено описание")
        elif prop_key == "subject":
            return ("subject", "📝", "Изменена тема")
        elif prop_key == "done_ratio":
            return ("progress", "📊", "Изменена готовность")

    # Если это добавление файла
    if property_name == "attachment":
        return ("attachment", "📎", "Добавлен файл")

    # Если это связь с другой задачей
    if property_name == "relation":
        if prop_key == "relates":
            return ("relation", "🔗", "Связана с задачей")
        elif prop_key == "subtask":
            return ("subtask", "📋", "Добавлена подзадача")

    # По умолчанию - общее обновление
    return ("update", "🔄", "Обновлена заявка")
