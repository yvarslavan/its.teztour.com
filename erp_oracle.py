from configparser import ConfigParser
import os
import logging
from flask import flash
import oracledb

os.environ["NLS_LANG"] = "Russian.AL32UTF8"

# Импорт безопасной конфигурации
try:
    from secure_config import get_config
    secure_config = get_config()

    # Проверяем наличие обязательных переменных
    missing = secure_config.validate_required_vars()
    if not missing:
        logging.info("✅ Используется безопасная конфигурация из переменных окружения")

        # Получаем конфигурацию из безопасного источника
        db_host = secure_config.oracle_host
        db_port = secure_config.oracle_port
        db_service_name = secure_config.oracle_service_name
        db_user_name = secure_config.oracle_user
        db_password = secure_config.oracle_password

    else:
        logging.warning(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing)}")
        raise ImportError("Неполная конфигурация")

except ImportError:
    logging.warning("⚠️ Используется устаревшая конфигурация config.ini")
    import os

    # Используем переменные окружения напрямую
    db_host = os.getenv('ORACLE_HOST')
    db_port = os.getenv('ORACLE_PORT')
    db_service_name = os.getenv('ORACLE_SERVICE_NAME')
    db_user_name = os.getenv('ORACLE_USER')
    db_password = os.getenv('ORACLE_PASSWORD')

# Логирование для диагностики - проверяем значения конфигурации
logger = logging.getLogger(__name__)
logger.info(f"[ORACLE CONFIG] db_host={db_host}")
logger.info(f"[ORACLE CONFIG] os.getenv('ORACLE_HOST')={os.getenv('ORACLE_HOST')}")
logger.info(f"[ORACLE CONFIG] Using secure_config: {locals().get('secure_config', 'None')}")


def connect_oracle(
    oracle_host, oracle_port, oracle_service_name, oracle_user_name, oracle_password
):
    logger = logging.getLogger(__name__)
    logger.info(f"[ORACLE DEBUG] Connecting to Oracle: {oracle_host}:{oracle_port}/{oracle_service_name}")

    # Проверяем, является ли устройство мобильным (для увеличения таймаута)
    try:
        from flask import request
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipad', 'ios'])
        if is_mobile:
            logger.info(f"[ORACLE DEBUG] Mobile device detected: {user_agent[:50]}...")
    except:
        is_mobile = False

    try:
        # Добавляем таймаут подключения (по умолчанию 10 секунд для мобильных устройств)
        # Таймаут Oracle (в секундах). Для мобильных устройств рекомендуется 10-15 сек.
        tcp_timeout = int(os.getenv("ORACLE_TCP_TIMEOUT", "10"))
        # Для мобильных устройств увеличиваем таймаут еще больше
        if is_mobile and tcp_timeout < 15:
            tcp_timeout = 15
            logger.info(f"[ORACLE DEBUG] Increased timeout for mobile device to: {tcp_timeout} seconds")
        logger.info(f"[ORACLE DEBUG] TCP timeout set to: {tcp_timeout} seconds")
        oracle_connection = oracledb.connect(
            user=oracle_user_name,
            password=oracle_password,
            host=oracle_host,
            port=oracle_port,
            service_name=oracle_service_name,
            tcp_connect_timeout=tcp_timeout  # Таймаут TCP подключения в секундах
        )
        logger.info("[ORACLE DEBUG] Oracle connection established successfully")
        return oracle_connection
    except oracledb.DatabaseError as e:
        logger.error(f"[ORACLE DEBUG] DatabaseError during connection: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[ORACLE DEBUG] Unexpected error during Oracle connection: {str(e)}")
        return None


def close_oracle_connection(connection):
    if connection is not None:
        try:
            connection.close()
            print("Oracle connection closed successfully")
        except oracledb.DatabaseError as e:
            logging.error("Ошибка выполнения закрытия соединения: %s", str(e))
    else:
        logging.warning("Попытка закрыть несуществующее соединение")


def verify_credentials(connection, login_erp_user, password_erp_user):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS result
                            FROM erp.v_user WHERE AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник'
                            AND NAME = :login_erp_user AND PASSWORD = :password_erp_user""",
                {
                    "login_erp_user": str(login_erp_user),
                    "password_erp_user": str(password_erp_user)
                }
            )
            return bool(cursor.fetchone()[0] == 1)
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
        return False


def get_user_erp_data(connection, login_erp_user, password_erp_user):
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT
                        NVL(vu.PASSWORD,'') as password,
                        UPPER(NVL(vu.FULL_NAME, '')) as full_name,
                        NVL(vu.EMAIL, '') as email,
                        NVL(vu.OFFICE, '') as office,
                        NVL(vu.DEPARTMENT_NAME, '') as department_name,
                        NVL(vu.POST_NAME, '') as position,
                        NVL(vu.PHONE_EXT, '') as phone_ext,
                        NVL(vu.VPN, '') as vpn,
                        NVL(tu.vpn_end_date, '') as vpn_end_date
                FROM erp.v_user vu, erp.t_user tu
                WHERE vu.USER_ID=tu.USER_ID AND (vu.AUTH_PERIOD_TYPE IS NOT NULL
                      AND vu.AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник')
                      AND vu.NAME = :erp_login  AND vu.PASSWORD = :erp_password""",
            {"erp_login": str(login_erp_user), "erp_password": str(password_erp_user)},
        )
        result = cursor.fetchone()
        if result:
            return result
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
    return None


def get_user_erp_password(connection, user_username):
    if connection is None:
        logging.error("Отсутствует соединение с базой данных TEZ ERP")
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT PASSWORD
                FROM erp.v_user
                WHERE AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник'
                AND NAME = :login_erp_user
                """,
                {"login_erp_user": str(user_username)},
            )
            result = cursor.fetchone()
            return result[0] if result else None  # Возвращаем строку, а не кортеж
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
        return None  # Лучше возвращать None в случае ошибки
