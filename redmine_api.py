"""
Redmine API Module
Handles Redmine API integration, authentication, and operations.
"""

import logging
import traceback
import requests
from urllib.parse import urlparse
from redminelib import Redmine
from redminelib.exceptions import (
    BaseRedmineError,
    ResourceNotFoundError,
    AuthError,
    ForbiddenError,
)

# Создаем объект логгера
logger = logging.getLogger(__name__)


class RedmineConnector:
    """Класс для работы с Redmine API"""

    def __init__(self, url, username=None, password=None, api_key=None):
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error("Некорректный URL для подключения к Redmine: %s", url)
                raise ValueError("Некорректный URL для подключения к Redmine.")

            logger.info("Инициализация RedmineConnector с URL: %s", url)
            logger.info(
                "Параметры: username=%s, password=%s, api_key=%s",
                username, '***' if password else None, '***' if api_key else None
            )

            # Создаем сессию без прокси (NO_PROXY=* установлен глобально в app.py)
            session = requests.Session()
            session.verify = False
            session.trust_env = False
            # Устанавливаем таймауты для избежания зависания запросов
            # Таймауты будут передаваться в каждый запрос

            if username and password:
                logger.info(
                    "Создание подключения к Redmine с именем пользователя: %s", username
                )
                self.redmine = Redmine(
                    url,
                    username=username,
                    password=password,
                    requests={"session": session, "timeout": 10, "verify": False},
                )
                logger.info(
                    "Инициализировано подключение к Redmine с использованием имени пользователя и пароля."
                )
            elif api_key:
                logger.info("Создание подключения к Redmine с API ключом")
                self.redmine = Redmine(
                    url,
                    key=api_key,
                    requests={"session": session, "timeout": 10, "verify": False},
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
            logger.error("Ошибка при инициализации RedmineConnector: %s", e)
            import traceback

            logger.error("Трассировка: %s", traceback.format_exc())
            raise

    def is_user_authenticated(self):
        try:
            logger.info("Проверка аутентификации пользователя в Redmine...")
            current_user = self.redmine.user.get("current")
            logger.info(
                "Аутентификация успешна. Пользователь ID: %s, Email: %s",
                current_user.id, getattr(current_user, 'mail', 'N/A')
            )
            return True
        except AuthError as auth_error:
            logger.error("Ошибка аутентификации (AuthError): %s", auth_error)
            return False
        except ForbiddenError as forbidden_error:
            logger.error("Доступ запрещен (ForbiddenError): %s", forbidden_error)
            return False
        except ResourceNotFoundError as not_found_error:
            logger.error("Ресурс не найден (ResourceNotFoundError): %s", not_found_error)
            return False
        except BaseRedmineError as base_error:
            logger.error("Общая ошибка Redmine (BaseRedmineError): %s", base_error)
            return False
        except (ValueError, TypeError, OSError, RuntimeError) as general_error:
            logger.error(
                "Неожиданная ошибка при проверке аутентификации: %s", general_error
            )
            import traceback

            logger.error("Трассировка: %s", traceback.format_exc())
            return False

    def get_current_user(self, user_id):
        try:
            user = self.redmine.user.get(user_id)
            return True, user  # Возвращаем True и пользователя, если операция успешна
        except BaseRedmineError as e:
            return (
                False,
                f"Ошибка при получении пользователя: {e}",
            )
        except Exception as e:
            return (
                False,
                f"Неожиданная ошибка при получении пользователя: {e}",
            )

    def get_issue(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id, include="journals")
            return True, issue
        except BaseRedmineError as e:
            return False, f"Ошибка при получении заявки: {e}"
        except Exception as e:
            return False, f"Неожиданная ошибка при получении заявки: {e}"

    def get_issue_history(self, issue_id):
        try:
            issue = self.redmine.issue.get(issue_id, include="journals")
            # Возвращаем историю в обратном порядке (новые комментарии вверху)
            return list(reversed(issue.journals))
        except ResourceNotFoundError:
            logging.error(
                "Ошибка выполнения запроса к базе данных TEZ ERP: Заявка не найдена."
            )
            return None  # Возвращаем пустой список истории

    def add_comment(self, issue_id, notes, user_id=None):
        try:
            # Логируем параметры
            print(f"[add_comment] Добавление комментария к задаче {issue_id}")
            print(f"[add_comment] user_id: {user_id}")
            print(f"[add_comment] notes: {notes[:100]}...")

            self.redmine.issue.update(issue_id, notes=notes)
            print("[add_comment] Комментарий добавлен через Redmine API")
        except BaseRedmineError as e:
            print(f"[add_comment] Ошибка Redmine API: {e}")
            return False, f"Ошибка при добавлении комментария в Redmine: {e}"

        if user_id is not None:
            try:
                print(f"[add_comment] Обновляем user_id в БД на {user_id}")
                from redmine_db import get_connection, db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, db_redmine_port
                conn = get_connection(
                    db_redmine_host,
                    db_redmine_user_name,
                    db_redmine_password,
                    db_redmine_name,
                    db_redmine_port,
                )
                if conn:
                    try:
                        cursor = conn.cursor()
                        update_user_id(conn, cursor, user_id, issue_id)
                        conn.commit()
                        print(f"[add_comment] user_id успешно обновлен в БД")
                    except Exception as db_error:
                        conn.rollback()
                        print(f"[add_comment] Ошибка при обновлении user_id в БД: {db_error}")
                        return False, f"Ошибка при обновлении user_id в БД: {db_error}"
                    finally:
                        if cursor:
                            cursor.close()
                        conn.close()
                else:
                    print(f"[add_comment] Не удалось подключиться к БД для обновления user_id")
                    return False, "Не удалось подключиться к БД для обновления user_id"
            except Exception as e:
                print(f"[add_comment] Исключение при обновлении user_id: {e}")
                return False, f"Исключение при обновлении user_id: {e}"

        return True, "Комментарий успешно добавлен"

    def get_users(self):
        try:
            users = self.redmine.user.all(limit=1000)
            return True, users
        except BaseRedmineError as e:
            return False, f"Ошибка при получении пользователей: {e}"
        except Exception as e:
            return False, f"Неожиданная ошибка при получении пользователей: {e}"

    def get_projects(self):
        try:
            projects = self.redmine.project.all(limit=1000)
            return True, projects
        except BaseRedmineError as e:
            return False, f"Ошибка при получении проектов: {e}"
        except Exception as e:
            return False, f"Неожиданная ошибка при получении проектов: {e}"


def update_user_id(connection, cursor, redmine_user_id, redmine_issue_id):
    """Обновляем user_id для последнего добавленного комментария к задаче"""
    # Обновляем последний добавленный комментарий к задаче
    user_id_update = """UPDATE redmine.journals SET user_id = %s WHERE journalized_id = %s
                        AND journalized_type = 'Issue' AND notes IS NOT NULL AND notes != ''
                        ORDER BY created_on DESC LIMIT 1;"""
    try:
        cursor.execute(user_id_update, (redmine_user_id, redmine_issue_id))
        logger.info("user_id успешно обновлен для комментария к задаче %s", redmine_issue_id)
    except Exception as e:
        logger.error("Ошибка при обновлении user_id: %s", e)
        raise
