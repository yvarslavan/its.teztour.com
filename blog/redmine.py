import pymysql
import pymysql.cursors
import logging
from configparser import ConfigParser
import os
from typing import Optional, Any, Tuple

# Настройка логгера
logger = logging.getLogger(__name__)

# Чтение конфигурации один раз при загрузке модуля из переменных окружения
try:
    DB_REDMINE_HOST = os.getenv('MYSQL_HOST')
    DB_REDMINE_USER = os.getenv('MYSQL_USER')
    DB_REDMINE_PASSWORD = os.getenv('MYSQL_PASSWORD')
    DB_REDMINE_DB = os.getenv('MYSQL_DATABASE')
    
    if not all([DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB]):
        raise ValueError("Неполная конфигурация MySQL")
    
    logger.info("Конфигурация для Redmine DB успешно загружена из переменных окружения.")
except Exception as e:
    logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось прочитать конфигурацию БД Redmine из переменных окружения: {e}")
    DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB = None, None, None, None

def get_connection() -> Optional[pymysql.Connection]:
    """Устанавливает и возвращает соединение с базой данных MySQL."""
    host, user, password, db = DB_REDMINE_HOST, DB_REDMINE_USER, DB_REDMINE_PASSWORD, DB_REDMINE_DB
    if host is None or user is None or password is None or db is None:
        logger.error("Невозможно установить соединение: параметры конфигурации Redmine DB неполные.")
        return None
    try:
        return pymysql.connect(
            host=host, user=user, password=password, database=db,
            cursorclass=pymysql.cursors.DictCursor, connect_timeout=10
        )
    except pymysql.MySQLError as e:
        logger.error(f"Ошибка подключения к MySQL: {e}", exc_info=True)
        return None

def execute_query(query: str, params: Optional[Any] = None, fetch: Optional[str] = None, commit: bool = False) -> Tuple[bool, Any]:
    """
    Выполняет SQL-запрос с явным управлением ресурсами.
    Возвращает кортеж (success: bool, result: any).
    """
    connection = get_connection()
    if not connection:
        return False, "Не удалось установить соединение с базой данных."

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)

        if fetch == 'one':
            result: Any = cursor.fetchone()
        elif fetch == 'all':
            result = list(cursor.fetchall())
        else:
            result = cursor.rowcount

        if commit:
            connection.commit()
        return True, result
    except pymysql.MySQLError as e:
        if connection and commit:
            connection.rollback()
        logger.error(f"Ошибка SQL: {e}\nЗапрос: {query}\nПараметры: {params or 'N/A'}", exc_info=True)
        return False, str(e)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_recent_activity(user_id: Optional[int] = None, user_email: str = None, limit: int = 50) -> list:
    """
    Получение последней активности по заявкам пользователя
    Показывает только активные заявки (исключает закрытые статусы где is_closed = 1)
    Использует ту же логику, что и основная таблица заявок

    Args:
        user_id: ID пользователя в Redmine (может быть None)
        user_email: Email пользователя
        limit: Максимальное количество записей активности

    Returns:
        list: Список записей активности или пустой список в случае ошибки
    """
    try:
        logger.info(f"[get_recent_activity] Получение активности для user_id={user_id}, email={user_email}, limit={limit}")

        if not user_email:
            logger.warning("[get_recent_activity] Email пользователя не указан")
            return []

        logger.info(f"[get_recent_activity] 🔍 ДЕТАЛЬНАЯ ОТЛАДКА:")
        logger.info(f"[get_recent_activity] - user_id: {user_id} (тип: {type(user_id)})")
        logger.info(f"[get_recent_activity] - user_email: '{user_email}'")
        logger.info(f"[get_recent_activity] - user_id != 4: {user_id != 4}")
        logger.info(f"[get_recent_activity] - user_id and user_id != 4: {user_id and user_id != 4}")

        # Получаем подключение к MySQL
        connection = get_connection()
        if not connection:
            logger.error("[get_recent_activity] Не удалось подключиться к MySQL")
            return []

        try:
            cursor = connection.cursor()
            activity_data = []

            # Используем ту же логику, что и в get_issues_redmine_author_id
            if user_id and user_id != 4:
                # Для пользователей с аккаунтом в Redmine: ищем по author_id ИЛИ easy_email_to
                # Исключаем закрытые статусы (is_closed = 1)
                issues_query = """
                    SELECT DISTINCT i.id, i.subject, i.updated_on, s.name as status_name
                    FROM issues i
                    LEFT JOIN u_statuses s ON i.status_id = s.id
                    LEFT JOIN issue_statuses ist ON i.status_id = ist.id
                    WHERE (i.author_id = %s OR i.easy_email_to = %s)
                    AND (ist.is_closed = 0 OR ist.is_closed IS NULL)
                    AND i.updated_on >= DATE_SUB(NOW(), INTERVAL 10 DAY)
                    ORDER BY i.updated_on DESC
                """
                logger.info(f"[get_recent_activity] 🔍 SQL для пользователя С аккаунтом Redmine:")
                logger.info(f"[get_recent_activity] - user_id: {user_id}")
                logger.info(f"[get_recent_activity] - user_email: '{user_email}'")
                logger.info(f"[get_recent_activity] - SQL: {issues_query}")
                cursor.execute(issues_query, (user_id, user_email))
            else:
                # Для пользователей без аккаунта в Redmine: ищем только по easy_email_to
                # Используем ту же логику, что и в get_issues_by_email
                # Исключаем закрытые статусы (is_closed = 1)
                alt_email = user_email.replace("@tez-tour.com", "@msk.tez-tour.com")
                issues_query = """
                    SELECT DISTINCT i.id, i.subject, i.updated_on, s.name as status_name
                    FROM issues i
                    LEFT JOIN u_statuses s ON i.status_id = s.id
                    LEFT JOIN issue_statuses ist ON i.status_id = ist.id
                    WHERE (i.easy_email_to = %s OR i.easy_email_to = %s)
                    AND (ist.is_closed = 0 OR ist.is_closed IS NULL)
                    AND i.updated_on >= DATE_SUB(NOW(), INTERVAL 10 DAY)
                    ORDER BY i.updated_on DESC
                """
                logger.info(f"[get_recent_activity] 🔍 SQL для пользователя БЕЗ аккаунта Redmine:")
                logger.info(f"[get_recent_activity] - user_email: '{user_email}'")
                logger.info(f"[get_recent_activity] - alt_email: '{alt_email}'")
                logger.info(f"[get_recent_activity] - SQL: {issues_query}")
                cursor.execute(issues_query, (user_email, alt_email))

            issues = cursor.fetchall()

            logger.info(f"[get_recent_activity] Найдено {len(issues)} заявок для пользователя")
            if issues:
                logger.info(f"[get_recent_activity] 🔍 ПРИМЕРЫ НАЙДЕННЫХ ЗАЯВОК:")
                for i, issue in enumerate(issues[:5]):  # Показываем первые 5
                    logger.info(f"[get_recent_activity] - Заявка {i+1}: ID={issue['id']}, subject='{issue['subject'][:50]}...', updated_on={issue['updated_on']}")
            else:
                logger.warning(f"[get_recent_activity] Заявки не найдены для user_id={user_id}, email={user_email}")

            for issue in issues:
                activity_data.append({
                    'issue_id': issue['id'],
                    'subject': issue['subject'],
                    'updated_on': issue['updated_on'],
                    'status_name': issue['status_name'],
                    'activity_type': 'update',
                    'activity_text': 'Заявка обновлена'
                })

            # Получаем комментарии к заявкам пользователя
            if issues:
                issue_ids = [str(issue['id']) for issue in issues]
                placeholders = ','.join(['%s'] * len(issue_ids))

                comments_query = f"""
                    SELECT
                        j.journalized_id as issue_id,
                        j.notes as Body,
                        CONCAT(u.firstname, ' ', u.lastname) as Author,
                        j.created_on as created_at,
                        i.subject
                    FROM journals j
                    JOIN issues i ON i.id = j.journalized_id
                    LEFT JOIN users u ON u.id = j.user_id
                    WHERE j.journalized_id IN ({placeholders})
                    AND j.journalized_type = 'Issue'
                    AND j.notes IS NOT NULL
                    AND j.notes != ''
                    AND j.created_on >= DATE_SUB(NOW(), INTERVAL 10 DAY)
                    ORDER BY j.created_on DESC
                """

                cursor.execute(comments_query, issue_ids)
                comments = cursor.fetchall()

                logger.info(f"[get_recent_activity] Найдено {len(comments)} комментариев")

                for comment in comments:
                    activity_data.append({
                        'issue_id': comment['issue_id'],
                        'subject': comment['subject'],
                        'updated_on': comment['created_at'],
                        'status_name': 'Комментарий',
                        'activity_type': 'comment',
                        'activity_text': f'Добавлен комментарий от {comment["Author"]}'
                    })

            # Сортируем по дате обновления
            activity_data.sort(key=lambda x: x['updated_on'], reverse=True)

            logger.info(f"[get_recent_activity] Возвращаем {len(activity_data)} записей активности")
            if activity_data:
                logger.info(f"[get_recent_activity] Примеры возвращаемых данных: {activity_data[:2]}")
            else:
                logger.warning(f"[get_recent_activity] ВНИМАНИЕ: Возвращаем пустой список!")
            return activity_data

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        logger.error(f"[get_recent_activity] Ошибка при получении активности: {e}", exc_info=True)
        return []
