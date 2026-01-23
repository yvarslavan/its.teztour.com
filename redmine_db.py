"""
Redmine Database Connection Module
Handles database connections, pooling, and query execution.
"""

import os
import time
import logging
import pymysql
import pymysql.cursors
from dbutils.pooled_db import PooledDB

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Создаем объект логгера
logger = logging.getLogger(__name__)

# Глобальный пул соединений MySQL
_connection_pools = {}
_pool_lock = __import__('threading').Lock()


def _get_pool_key(host, port, name, user_name):
    """Генерирует уникальный ключ для пула соединений"""
    return f"{host}:{port}/{name}/{user_name}"


def _get_or_create_pool(host, user_name, password, name, port):
    """Получает существующий пул или создаёт новый"""
    pool_key = _get_pool_key(host, port, name, user_name)

    with _pool_lock:
        if pool_key not in _connection_pools:
            connect_timeout = int(os.getenv('MYSQL_CONNECT_TIMEOUT', '3'))
            pool_size = int(os.getenv('MYSQL_POOL_SIZE', '5'))
            max_connections = int(os.getenv('MYSQL_MAX_CONNECTIONS', '10'))

            try:
                _connection_pools[pool_key] = PooledDB(
                    creator=pymysql,
                    maxconnections=max_connections,
                    mincached=2,
                    maxcached=pool_size,
                    blocking=True,
                    maxusage=None,
                    setsession=[],
                    ping=1,  # Проверять соединение перед использованием
                    host=host,
                    port=int(port),
                    user=user_name,
                    password=password,
                    db=name,
                    charset="utf8mb4",
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=connect_timeout,
                )
                logger.info("✅ Создан пул соединений для %s:%s/%s (размер: %s, макс: %s)", host, port, name, pool_size, max_connections)
            except (pymysql.Error, ValueError, OSError) as e:
                logger.error("❌ Ошибка создания пула соединений: %s", e)
                return None

        return _connection_pools[pool_key]


def get_connection(host, user_name, password, name, port=3306, max_attempts=None, retry_delay=None):
    """
    Подключение к MySQL через пул соединений.

    Args:
        host: Хост базы данных
        user_name: Имя пользователя
        password: Пароль
        name: Имя базы данных
        port: Порт (по умолчанию 3306)
        max_attempts: Максимальное количество попыток
        retry_delay: Задержка между попытками

    Returns:
        connection: Объект соединения или None в случае ошибки
    """
    if max_attempts is None:
        max_attempts = int(os.getenv('MYSQL_MAX_ATTEMPTS', '3'))
    if retry_delay is None:
        retry_delay = float(os.getenv('MYSQL_RETRY_DELAY', '1.0'))

    # Преобразуем порт в строку для совместимости
    if isinstance(port, int):
        port = str(port)
    else:
        # Если порт передан как строка (например, из переменных окружения)
        try:
            port = str(int(port))
        except ValueError:
            logger.error("Неверный формат порта: %s", port)
            return None

    # Пробуем использовать пул соединений
    use_pool = os.getenv('MYSQL_USE_POOL', '1') == '1'

    if use_pool:
        pool = _get_or_create_pool(host, user_name, password, name, port)
        if pool:
            try:
                connection = pool.connection()
                logger.debug("Получено соединение из пула для %s:%s/%s", host, port, name)
                return connection
            except (pymysql.Error, ValueError, OSError) as e:
                logger.warning("Ошибка получения соединения из пула: %s, пробуем прямое подключение", e)

    # Fallback: прямое подключение (старая логика)
    connect_timeout = int(os.getenv('MYSQL_CONNECT_TIMEOUT', '3'))
    attempts = 0
    while attempts < max_attempts:
        try:
            connection = pymysql.connect(
                host=host,
                port=int(port),
                user=user_name,
                password=password,
                db=name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=connect_timeout,
            )
            logger.info("Соединение с базой данных %s:%s/%s установлено (прямое)", host, port, name)
            return connection
        except pymysql.Error as e:
            logger.error("Ошибка при установлении соединения с базой данных: %s", e)
            attempts += 1
            if attempts < max_attempts:
                logger.warning(
                    "Повторная попытка подключения через %.1f сек (попытка %s/%s)...",
                    retry_delay, attempts + 1, max_attempts
                )
                time.sleep(retry_delay)
        except Exception as _:  # pylint: disable=broad-except
            logging.error(
                "Неизвестная ошибка при подключении к базе данных", exc_info=True
            )
            break
    logger.error(
        "Не удалось установить соединение с базой данных после %s попыток", max_attempts
    )
    return None


def execute_query(cursor, query, params=None):
    """
    Выполняет SQL-запрос и возвращает результат.

    Args:
        cursor: Объект курсора
        query: SQL-запрос
        params: Параметры запроса (опционально)

    Returns:
        list: Результат запроса или None в случае ошибки
    """
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except pymysql.Error as e:
        logger.error("Ошибка выполнения SQL-запроса: %s", e)
        return None


def execute_update(cursor, query, params=None):
    """
    Выполняет SQL-запрос на обновление/вставку/удаление.

    Args:
        cursor: Объект курсора
        query: SQL-запрос
        params: Параметры запроса (опционально)

    Returns:
        int: Количество затронутых строк или None в случае ошибки
    """
    try:
        cursor.execute(query, params or ())
        return cursor.rowcount
    except pymysql.Error as e:
        logger.error("Ошибка выполнения SQL-запроса: %s", e)
        return None


# Конфигурация базы данных из переменных окружения
try:
    # Проверяем наличие обязательных переменных
    db_redmine_host = os.getenv('MYSQL_HOST')
    db_redmine_port = int(os.getenv('MYSQL_PORT', '3306'))
    db_redmine_name = os.getenv('MYSQL_DATABASE')
    db_redmine_user_name = os.getenv('MYSQL_USER')
    db_redmine_password = os.getenv('MYSQL_PASSWORD')

    if not all([db_redmine_host, db_redmine_name, db_redmine_user_name, db_redmine_password]):
        missing = [k for k, v in [
            ('MYSQL_HOST', db_redmine_host),
            ('MYSQL_DATABASE', db_redmine_name),
            ('MYSQL_USER', db_redmine_user_name),
            ('MYSQL_PASSWORD', db_redmine_password)
        ] if not v]
        logger.warning("⚠️ Отсутствуют переменные окружения: %s", ', '.join(missing))
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

    # Используем переменные окружения напрямую
    db_redmine_host = os.getenv('MYSQL_HOST')
    db_redmine_port = int(os.getenv('MYSQL_PORT', '3306'))
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
    ANONYMOUS_USER_ID_CONFIG = int(os.getenv('REDMINE_ANONYMOUS_USER_ID', '4'))
