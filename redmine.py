import os
import tempfile
from datetime import timedelta, datetime
from configparser import ConfigParser
import re
import logging
import sqlite3
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
    ImpersonateError,
)
import pymysql
import pymysql.cursors
from flask_login import current_user
from flask import flash
import xmpp
from blog.models import Notifications, NotificationsAddNotes


# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Создаем объект логгера
logger = logging.getLogger(__name__)

os.environ["NLS_LANG"] = "Russian.AL32UTF8"

config = ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config.read(config_path)
db_redmine_host = config.get("mysql", "host")
db_redmine_name = config.get("mysql", "database")
db_redmine_user_name = config.get("mysql", "user")
db_redmine_password = config.get("mysql", "password")

# Получаем путь к текущему каталогу
current_dir = os.path.dirname(os.path.abspath(__file__))
# Получаем относительный путь к базе данных из конфигурации
db_relative_path = config.get("database", "db_path")
# Формируем абсолютный путь к базе данных
db_absolute_path = os.path.join(current_dir, db_relative_path)
ERROR_MESSAGE = "An error occurred:"

# Глобальные переменные для URL и API ключа администратора Redmine
REDMINE_URL = config.get("redmine", "url")
REDMINE_ADMIN_API_KEY = config.get("redmine", "api_key")
# ANONYMOUS_USER_ID также уже определен глобально в routes.py, но может понадобиться здесь
ANONYMOUS_USER_ID_CONFIG = int(config.get("redmine", "anonymous_user_id", fallback="0"))

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
            print("Соединение с базой данных установлено")
            return connection
        except pymysql.Error as e:
            print(f"Ошибка при установлении соединения с базой данных: {e}")
            attempts += 1
            if attempts < max_attempts:
                print(
                    f"Повторная попытка подключения через 3 секунды (попытка {attempts + 1} из {max_attempts})..."
                )
                time.sleep(3)
        except Exception as _:  # pylint: disable=broad-except
            logging.error(
                "Неизвестная ошибка при подключении к базе данных", exc_info=True
            )
            break  # или можете выбрать продолжить попытки, если считаете это целесообразным
    print(
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
    result = None # Инициализируем result
    with connection:
        if prop_key == "project_id":
            project_name_from = get_project_name_from_id(connection, old_value)
            project_name_to = get_project_name_from_id(connection, value)
            result = "Параметр&nbsp;<b>Проект</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + (project_name_from or 'None') + "</b>&nbsp;на&nbsp;<b>" + (project_name_to or 'None') + "</b>"

        elif prop_key == "assigned_to_id":
            assigned_name_from = None
            assigned_name_to = None
            if old_value is None:
                assigned_name_to = get_user_full_name_from_id(connection, value)
            else:
                assigned_name_from = get_user_full_name_from_id(connection, old_value)
                assigned_name_to = get_user_full_name_from_id(connection, value)
            result = "Параметр&nbsp;<b>Назначена</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + (assigned_name_from or 'None') + "</b>&nbsp;на&nbsp;<b>" + (assigned_name_to or 'None') + "</b>"

        elif prop_key == "status_id":
            status_name_from = get_status_name_from_id(connection, old_value)
            status_name_to = get_status_name_from_id(connection, value)
            result = "Параметр&nbsp;<b>Статус</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + str(status_name_from) + "</b>&nbsp;на&nbsp;<b>" + str(status_name_to) + "</b>"

        elif prop_key == "priority_id":
            priority_name_from = get_priority_name_from_id(connection, old_value)
            priority_name_to = get_priority_name_from_id(connection, value)
            result = "Параметр&nbsp;<b>Приоритет</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + str(priority_name_from) + "</b>&nbsp;на&nbsp;<b>" + str(priority_name_to) + "</b>"

        elif prop_key == "subject":
            result = (
                "Параметр&nbsp;<b>Тема</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + str(old_value) + "</b>&nbsp;на&nbsp;<b>" + str(value) + "</b>"
            )

        elif prop_key == "easy_helpdesk_need_reaction":
            old_reaction_text = 'Да' if old_value == '1' else 'Нет'
            new_reaction_text = 'Да' if value == '1' else 'Нет'
            result = "Параметр&nbsp;<b>Нужна&nbsp;реакция?</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + old_reaction_text + "</b>&nbsp;на&nbsp;<b>" + new_reaction_text + "</b>"

        elif prop_key == "done_ratio":
            result = "Параметр&nbsp;<b>Готовность</b>&nbsp;изменился&nbsp;c&nbsp;<b>" + str(old_value) + "%</b>&nbsp;на&nbsp;<b>" + str(value) + "%</b>"

        elif property_name == "attachment":
            result = "Файл&nbsp;<b>" + str(value) + "</b>&nbsp;добавлен"

        elif property_name == "relation" and prop_key == "relates":
            result = "Задача&nbsp;связана&nbsp;с&nbsp;задачей&nbsp;<b>#" + str(value) + "</b>"

        elif (
            prop_key == "subtask" and property_name == "relation" and value is not None
        ):
            result = "Добавлена&nbsp;подзадача&nbsp;<b>#" + str(value) + "</b>"

        else:
            result = None

    return result


class RedmineConnector:
    def __init__(self, url, username=None, password=None, api_key=None):
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Некорректный URL для подключения к Redmine.")
        if username and password:
            self.redmine = Redmine(url, username=username, password=password)
            logger.info("Инициализировано подключение к Redmine с использованием имени пользователя и пароля.")
        elif api_key:
            self.redmine = Redmine(url, key=api_key)
            logger.info("Инициализировано подключение к Redmine с использованием API ключа.")
        else:
            raise ValueError("Или (username, password) или api_key должны быть определены.")

    def is_user_authenticated(self):
        try:
            self.redmine.user.get("current")
            return True
        except AuthError:
            return False
        except BaseRedmineError as e:
            logging.error("Ошибка при проверке аутентификации: %s", e)
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
        except pymysql.Error() as e:
            logging.error("Ошибка при обновлении статуса заявки:: %s", str(e))
            return False, f"Ошибка при обновлении статуса заявки: {e}"

    def get_issue_history(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id, include="journals")
            return issue.journals
        except ResourceNotFoundError:
            logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: Заявка не найдена.")
            flash(f"Заявка с ID {issue_id} не существует или была удалена.", "error")
            return []  # Возвращаем пустой список истории
        except ForbiddenError:
            logging.error("Запрошенный ресурс запрещен:")
            # flash(f"Доступ к заявке с ID {issue_id} запрещен.", "error")
            return None  # Возвращаем пустой список истории

    def add_comment(self, issue_id, notes, user_id=None):
        try:
            self.redmine.issue.update(issue_id, notes=notes)
        except BaseRedmineError as e:
            return False, f"Ошибка при добавлении комментария в Redmine: {e}"

        if user_id is not None:
            try:
                conn = get_connection(
                    db_redmine_host,
                    db_redmine_user_name,
                    db_redmine_password,
                    db_redmine_name,
                )
                success, message = update_user_id(conn, user_id, issue_id)
                if not success:
                    return False, message
            except pymysql.Error as e:  # Перехватываем исключения, связанные с pymysql
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
            logger.error(
                "An unexpected error occurred: %s", e, exc_info=True
            )
            return []


def update_user_id(connection, redmine_user_id, redmine_issue_id):
    """Обновляем user_id с Admin Redmine = 1 на Anonymous = 4"""
    user_id_update = """UPDATE redmine.journals SET user_id = %s WHERE journalized_id = %s
                        AND journalized_type = 'Issue' AND user_id = 1;"""
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
    except pymysql.Error() as e:
        print(f"{ERROR_MESSAGE} {e}")
        return None  # Возвращаем значение в случае исключения
    finally:
        if cursor is not None:
            cursor.close()


def get_issues_redmine_author_id(connection, author_id, easy_email_to):
    """Выборка заявок из Redmine по автору или email пользователя"""

    query = """
    SELECT i.id AS issue_id, i.updated_on AS updated_on, i.subject AS subject, us.name AS status_name
    FROM issues i
    INNER JOIN u_statuses us ON i.status_id = us.id
    WHERE i.author_id = %s OR i.easy_email_to LIKE %s
    ORDER BY i.updated_on DESC
    """

    issues_data = []

    try:
        with connection.cursor() as cursor:
            # Для безопасности и гибкости использую параметризованные запросы
            cursor.execute(query, (author_id, f"%{easy_email_to}%"))
            rows = cursor.fetchall()

            for row in rows:
                issues_data.append(
                    {
                        "id": row["issue_id"],
                        "updated_on": str(row["updated_on"]),
                        "subject": row["subject"],
                        "status_name": row["status_name"],
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
    """
    Проверка и загрузка новых уведомлений из Redmine DB (u_its_update_status, u_its_add_notes)
    и сохранение их в локальную SQLite DB (notifications, notifications_add_notes).
    Возвращает количество вновь обработанных уведомлений.
    """
    logger.info(f"[CHECK_NOTIFICATIONS] Начало проверки уведомлений для user_id: {current_user_id}, email: {user_email}")
    connection_db = None
    cursor = None
    newly_processed_count = 0

    try:
        # 1. Получаем соединение с базой данных Redmine
        logger.debug(f"[CHECK_NOTIFICATIONS] Попытка подключения к Redmine DB: host={db_redmine_host}, db={db_redmine_name}")
        connection_db = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)
        if connection_db is None:
            logger.error(f"[CHECK_NOTIFICATIONS] Не удалось подключиться к Redmine DB для user_id: {current_user_id}")
            return 0 # Возвращаем 0, так как False может интерпретироваться как ошибка глубже

        logger.info(f"[CHECK_NOTIFICATIONS] Успешное подключение к Redmine DB для user_id: {current_user_id}")

        # 2. Получаем курсор
        cursor = get_database_cursor(connection_db)
        if cursor is None:
            logger.error(f"[CHECK_NOTIFICATIONS] Не удалось получить курсор для Redmine DB для user_id: {current_user_id}")
            return 0

        # 3. Подготовка параметров
        email_part = user_email.split('@')[0] if '@' in user_email else user_email
        easy_email_to = user_email # Используется для удаления
        # count_vacuum_im_notifications сейчас не используется, передаем 0
        # (старая логика для XMPP закомментирована в process_*)

        # 4. Обработка изменений статусов
        logger.debug(f"[CHECK_NOTIFICATIONS] Вызов process_status_changes для user_id: {current_user_id}, email_part: {email_part}")
        processed_status_count = process_status_changes(
            connection_db, cursor, email_part, current_user_id, 0, easy_email_to
        )
        if processed_status_count > 0:
            logger.info(f"[CHECK_NOTIFICATIONS] Обработано {processed_status_count} уведомлений об изменении статуса для user_id: {current_user_id}")
            newly_processed_count += processed_status_count
            # Удаляем обработанные уведомления о статусах из Redmine DB
            logger.debug(f"[CHECK_NOTIFICATIONS] Попытка удаления обработанных status_changes из Redmine DB для easy_email_to: {easy_email_to}")
            delete_notifications(connection_db, easy_email_to)
            logger.info(f"[CHECK_NOTIFICATIONS] Удалены обработанные status_changes из Redmine DB для easy_email_to: {easy_email_to}")

        # 5. Обработка добавленных комментариев
        logger.debug(f"[CHECK_NOTIFICATIONS] Вызов process_added_notes для user_id: {current_user_id}, email_part: {email_part}")
        processed_notes_count = process_added_notes(
            connection_db, cursor, email_part, current_user_id, 0, easy_email_to
        )
        if processed_notes_count > 0:
            logger.info(f"[CHECK_NOTIFICATIONS] Обработано {processed_notes_count} уведомлений о новых комментариях для user_id: {current_user_id}")
            newly_processed_count += processed_notes_count
            # Удаляем обработанные уведомления о комментариях из Redmine DB
            logger.debug(f"[CHECK_NOTIFICATIONS] Попытка удаления обработанных added_notes из Redmine DB для easy_email_to: {easy_email_to}")
            delete_notifications_notes(connection_db, easy_email_to)
            logger.info(f"[CHECK_NOTIFICATIONS] Удалены обработанные added_notes из Redmine DB для easy_email_to: {easy_email_to}")

        logger.info(f"[CHECK_NOTIFICATIONS] Завершение проверки. Всего обработано новых уведомлений: {newly_processed_count} для user_id: {current_user_id}")
        return newly_processed_count

    except Exception as e:
        logger.error(f"[CHECK_NOTIFICATIONS] Глобальная ошибка при проверке уведомлений для user_id: {current_user_id}, email: {user_email}. Ошибка: {e}", exc_info=True)
        return 0 # Возвращаем 0 в случае ошибки
    finally:
        if cursor:
            try:
                cursor.close()
                logger.debug(f"[CHECK_NOTIFICATIONS] Курсор Redmine DB закрыт для user_id: {current_user_id}")
            except Exception as e_cursor:
                logger.error(f"[CHECK_NOTIFICATIONS] Ошибка при закрытии курсора Redmine DB для user_id: {current_user_id}: {e_cursor}", exc_info=True)
        if connection_db:
            try:
                connection_db.close()
                logger.debug(f"[CHECK_NOTIFICATIONS] Соединение Redmine DB закрыто для user_id: {current_user_id}")
            except Exception as e_conn:
                logger.error(f"[CHECK_NOTIFICATIONS] Ошибка при закрытии соединения Redmine DB для user_id: {current_user_id}: {e_conn}", exc_info=True)


def get_database_cursor(connection):
    try:
        return connection.cursor()
    except pymysql.Error:
        logging.exception(
            "Error getting database cursor"
        )  # Это автоматически логирует информацию об исключении
        return None


def execute_query(cursor, query, param):
    print(f"[DB_QUERY] Выполнение запроса: {query} с параметром: {param}")
    try:
        cursor.execute(query, param)
        results = cursor.fetchall()
        print(f"[DB_QUERY] Запрос выполнен успешно, получено строк: {len(results) if results else 0}")
        return results
    except pymysql.Error as e:
        print(f"[DB_QUERY] Ошибка выполнения запроса: {e}")
        logger.error("[DB_QUERY] Error executing query:", exc_info=True)
        return None


def process_status_changes(
    connection,
    cursor,
    email_part,
    current_user_id,
    count_vacuum_im_notifications,
    easy_email_to,
):
    query_status_change = """SELECT IssueID, OldStatus, NewStatus, OldSubj, Body, RowDateCreated
                             FROM u_its_update_status
                             WHERE SUBSTRING_INDEX(Author, '@', 1) = %s ORDER BY RowDateCreated DESC LIMIT 50"""
    print(f"[PROCESS_STATUS] Запрос для получения статусов: {query_status_change % email_part}")
    rows_status_change = execute_query(cursor, query_status_change, email_part)
    if rows_status_change:
        print(f"[PROCESS_STATUS] Получено {len(rows_status_change)} строк статусов. Первая строка (частично): IssueID={rows_status_change[0]['IssueID']}, OldSubj='{rows_status_change[0]['OldSubj'][:100] if rows_status_change[0]['OldSubj'] else ''}'...")
    else:
        print(f"[PROCESS_STATUS] Получено 0 строк статусов.")

    if rows_status_change is not None and len(rows_status_change) > 0:
        print(f"[PROCESS_STATUS] Найдено {len(rows_status_change)} новых статусов для обработки.")
        for i, row in enumerate(rows_status_change):
            print(f"[PROCESS_STATUS] Обработка статуса {i+1}/{len(rows_status_change)}: IssueID={row['IssueID']}, OldStatus='{row['OldStatus']}', NewStatus='{row['NewStatus']}'")
            notification_data_to_add = {
                "user_id": current_user_id,
                "issue_id": row["IssueID"],
                "old_status": row["OldStatus"],
                "new_status": row["NewStatus"],
                "old_subj": row["OldSubj"],
                "date_created": row["RowDateCreated"],
            }
            add_notification_to_database(notification_data_to_add)

            # Добавляем эту строку для отправки уведомления в Vacuum-IM
            # send_vacuum_im_notification(
            #     count_vacuum_im_notifications,
            #     row["IssueID"],
            #     row["OldStatus"],
            #     row["NewStatus"],
            #     easy_email_to,
            # )
    return len(rows_status_change) if rows_status_change else 0


def process_added_notes(
    connection,
    cursor,
    email_part,
    current_user_id,
    count_vacuum_im_notifications,
    easy_email_to,
):
    query_add_notes = """SELECT issue_id, Author, notes, date_created
                         FROM u_its_add_notes
                         WHERE SUBSTRING_INDEX(Author, '@', 1) = %s
                         ORDER BY date_created DESC LIMIT 50"""
    print(f"[PROCESS_NOTES] Запрос для получения комментариев: {query_add_notes % email_part}")
    rows_add_notes = execute_query(cursor, query_add_notes, email_part)
    if rows_add_notes:
        print(f"[PROCESS_NOTES] Получено {len(rows_add_notes)} строк комментариев. Первая строка (частично): IssueID={rows_add_notes[0]['issue_id']}, Author='{rows_add_notes[0]['Author']}', Notes='{rows_add_notes[0]['notes'][:100] if rows_add_notes[0]['notes'] else ''}'...")
    else:
        print(f"[PROCESS_NOTES] Получено 0 строк комментариев.")

    if rows_add_notes:
        print(f"[PROCESS_NOTES] Найдено {len(rows_add_notes)} новых комментариев для обработки.")
        for i, row in enumerate(rows_add_notes):
            print(f"[PROCESS_NOTES] Обработка комментария {i+1}/{len(rows_add_notes)}: IssueID={row['issue_id']}, Author='{row['Author']}'")
            notification_data_to_add = {
                "user_id": current_user_id,
                "issue_id": row["issue_id"],
                "Author": row["Author"],
                "notes": row["notes"],
                "date_created": row["date_created"],
            }
            print(f"[PROCESS_NOTES] Данные для добавления в SQLite: {notification_data_to_add}")
            add_notification_notes_to_database(notification_data_to_add)
            # Удаляем вызов, связанный с Vacuum-IM
            # send_vacuum_im_notification_add_note(
            #     count_vacuum_im_notifications,
            #     row["issue_id"],
            #     easy_email_to,
            #     row["notes"],
            # )
    return len(rows_add_notes) if rows_add_notes else 0


def connect_to_database(database_file):
    """Соединение с базой данных SQLite."""
    try:
        connection = sqlite3.connect(database_file)
        print("Соединение с базой данных успешно установлено.")
        return connection
    except sqlite3.Error as e:
        print("Ошибка при соединении с базой данных:", e)
        return None


def execute_sql_query(connection, query, params=None, row_factory=None):
    """Выполнение SQL-запроса к базе данных."""
    try:
        cursor = connection.cursor()
        if row_factory:
            cursor.row_factory = row_factory
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print("Ошибка при выполнении SQL-запроса:", e)
        return None


def notification_count(database_path, user_id):
    try:
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        # SQL-запрос для подсчета количества уведомлений с использованием параметризации
        sql_query = "SELECT COUNT(*) FROM notifications WHERE user_id = ?"
        cursor.execute(sql_query, (user_id,))
        count = cursor.fetchone()[0]  # Получаем результат запроса
        connection.close()
        return count  # Возвращаем количество уведомлений
    except sqlite3.Error as e:
        print(f"{ERROR_MESSAGE} {e}")
        return None


def add_notification_notes_to_database(notification_notes_data):
    try:
        user_id = notification_notes_data.get("user_id")
        issue_id = notification_notes_data.get("issue_id")
        author = notification_notes_data.get("Author")
        notes = notification_notes_data.get("notes")
        date_created = notification_notes_data.get("date_created")
        print(f"[ADD_NOTE_DB] Попытка добавления уведомления в SQLite: user_id={user_id}, issue_id={issue_id}, author={author}, notes_len={len(notes) if notes else 0}, date_created={date_created}")

        # Подключаемся к базе данных SQLite
        connection = sqlite3.connect(db_absolute_path)
        cursor = connection.cursor()
        # SQL-запрос для добавления записи в таблицу Notifications
        sql_query = """INSERT INTO notifications_add_notes (user_id, issue_id, author, notes, date_created)
                       VALUES (?, ?, ?, ?, ?)"""
        cursor.execute(
            sql_query,
            (user_id, issue_id, author, notes, date_created),
        )
        connection.commit()
        print(f"[ADD_NOTE_DB] Уведомление успешно добавлено и закоммичено в SQLite.")
        connection.close()
        logger.info("Notification added to the database successfully.")
    except sqlite3.Error as e:
        print(f"[ADD_NOTE_DB] Ошибка sqlite3 при добавлении уведомления: {e}")
        logger.error("[ADD_NOTE_DB] %s %s", ERROR_MESSAGE, e, exc_info=True)
    except Exception as e:
        print(f"[ADD_NOTE_DB] НЕПРЕДВИДЕННАЯ Ошибка при добавлении уведомления: {e}")
        logger.error("[ADD_NOTE_DB] Непредвиденная ошибка: %s", e, exc_info=True)


def add_notification_to_database(notification_data):
    try:
        user_id = notification_data.get("user_id")
        issue_id = notification_data.get("issue_id")
        old_status = notification_data.get("old_status")
        new_status = notification_data.get("new_status")
        old_subj = notification_data.get("old_subj")
        date_created = notification_data.get("date_created")

        # Подключаемся к базе данных SQLite
        connection = sqlite3.connect(db_absolute_path)
        cursor = connection.cursor()
        # SQL-запрос для добавления записи в таблицу Notifications
        sql_query = """INSERT INTO notifications (user_id, issue_id, old_status, new_status, old_subj, date_created)
                       VALUES (?, ?, ?, ?, ?, ?)"""
        cursor.execute(
            sql_query,
            (user_id, issue_id, old_status, new_status, old_subj, date_created),
        )
        connection.commit()
        connection.close()
        logger.info("Notification added to the database successfully.")
    except sqlite3.Error as e:
        logger.error("%s %s", ERROR_MESSAGE, e)


def delete_notifications_notes(connection, easy_email_to):
    """Удаляем уведомления о добавлении комментариев после их обработки"""
    split_easy_email_to = easy_email_to.split("@")[0]
    cursor = connection.cursor()
    query = """DELETE FROM u_its_add_notes WHERE SUBSTRING_INDEX(Author, '@', 1) = %s"""
    cursor.execute(
        query,
        split_easy_email_to,
    )
    connection.commit()
    cursor.close()


def delete_notifications(connection, easy_email_to):
    """Удаляем уведомления о изменении статуса после их обработки"""
    split_easy_email_to = easy_email_to.split("@")[0]
    cursor = connection.cursor()
    query = (
        """DELETE FROM u_its_update_status WHERE SUBSTRING_INDEX(Author, '@', 1) = %s"""
    )
    cursor.execute(
        query,
        split_easy_email_to,
    )
    connection.commit()
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
        return Redmine(REDMINE_URL, key=REDMINE_ADMIN_API_KEY)
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
            logger.warning("last_run_timestamp не имеет информации о часовом поясе. Предполагается UTC.")


        # Redmine API ожидает время в UTC. Если last_run_timestamp локальное, его нужно конвертировать в UTC.
        # Для простоты примера, предположим, что last_run_timestamp уже в UTC или redminelib корректно его обработает.
        # Убедимся, что передаем строку в ISO формате, redminelib >= 2.3.0 должен принимать datetime объекты напрямую.
        # Если версия старее, может потребоваться last_run_timestamp.isoformat()

        logger.info(f"Запрос задач, обновленных после: {last_run_timestamp.isoformat()}")

        # Используем f-строку для корректной передачи datetime в redminelib,
        # если он не справляется с datetime объектом напрямую для фильтрации.
        # 일반적으로 redminelib 은 datetime 객체를 올바르게 처리해야 합니다.
        updated_issues = redmine_instance.issue.filter(
            updated_on=f">{last_run_timestamp.isoformat()}", # Передача строки может быть надежнее
            status_id='*', # все статусы
            sort='updated_on:asc'
        )

        processed_journal_ids = set()

        for issue in updated_issues:
            logger.debug(f"Обработка обновленной задачи ID: {issue.id}, обновлена: {issue.updated_on}")
            try:
                # issue.journals загружает все журналы. Мы должны фильтровать их по дате.
                for journal_entry in issue.journals: # Переименовал journal в journal_entry во избежание конфликта имен, если есть модуль journal
                    journal_created_on = journal_entry.created_on

                    if journal_entry.id in processed_journal_ids:
                        continue

                    # Сравнение дат: journal_created_on (от redminelib, обычно UTC) и last_run_timestamp (предполагаем UTC)
                    if journal_created_on > last_run_timestamp:
                        processed_journal_ids.add(journal_entry.id)
                        event_data = {
                            'issue_id': issue.id,
                            'journal_id': journal_entry.id,
                            'user_id': journal_entry.user.id if hasattr(journal_entry, 'user') and journal_entry.user else ANONYMOUS_USER_ID_CONFIG,
                            'created_on': journal_created_on,
                            'notes': getattr(journal_entry, 'notes', ''),
                            'details': getattr(journal_entry, 'details', []),
                            'issue_author_id': issue.author.id if hasattr(issue, 'author') and issue.author else ANONYMOUS_USER_ID_CONFIG,
                            'issue_assigned_to_id': issue.assigned_to.id if hasattr(issue, 'assigned_to') and issue.assigned_to else None,
                            'project_id': issue.project.id if hasattr(issue, 'project') and issue.project else None,
                            'tracker_id': issue.tracker.id if hasattr(issue, 'tracker') and issue.tracker else None,
                            'status_id': issue.status.id if hasattr(issue, 'status') and issue.status else None,
                            'subject': getattr(issue, 'subject', '')
                        }
                        raw_events.append(event_data)
                        logger.debug(f"  Добавлено событие из журнала ID: {journal_entry.id} для задачи {issue.id}")

            except ResourceNotFoundError:
                logger.warning(f"Задача {issue.id} не найдена при попытке получить журналы (возможно, удалена). Пропускаем.")
                continue
            except Exception as e_journal:
                logger.error(f"Ошибка при обработке журналов для задачи {issue.id}: {e_journal}")
                continue

        logger.info(f"Найдено {len(raw_events)} сырых событий Redmine.")
        return raw_events

    except AuthError:
        logger.error("Ошибка аутентификации при запросе к Redmine API.")
        return []
    except ForbiddenError:
        logger.error("Доступ запрещен при запросе к Redmine API (проверьте права API ключа).")
        return []
    # Убрал ConnectionError, так как BaseRedmineError должен его покрывать или redminelib кидает свои типы
    except BaseRedmineError as e_base:
        logger.error(f"Общая ошибка Redmine API (redminelib): {e_base}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка в fetch_redmine_raw_updates: {e}", exc_info=True)
        return []
