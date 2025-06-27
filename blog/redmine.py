import pymysql
import pymysql.cursors
import logging
from configparser import ConfigParser
import os
from typing import Optional, Any, Tuple

# Настройка логгера
logger = logging.getLogger(__name__)

# Чтение конфигурации один раз при загрузке модуля
config = ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')
if not os.path.exists(config_path):
    config_path = os.path.join(os.getcwd(), "config.ini")

try:
    config.read(config_path)
    DB_REDMINE_HOST = config.get("mysql", "host")
    DB_REDMINE_USER = config.get("mysql", "user")
    DB_REDMINE_PASSWORD = config.get("mysql", "password")
    DB_REDMINE_DB = config.get("mysql", "database")
    logger.info("Конфигурация для Redmine DB успешно загружена.")
except Exception as e:
    logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось прочитать конфигурацию БД Redmine из {config_path}: {e}")
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
