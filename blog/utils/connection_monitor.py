from config import get_config
from erp_oracle import connect_oracle
from redmine import get_connection
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

config = get_config()

# Добавим проверку и логирование значений конфигурации
required_keys = ['db_host', 'db_port', 'db_service_name', 'db_user_name', 'db_password',
                'db_redmine_host', 'db_redmine_user_name', 'db_redmine_password', 'db_redmine_name']

for key in required_keys:
    if key not in config:
        logger.error(f"Missing configuration key: {key}")
    else:
        logger.debug(f"Config {key} is present")

# Получаем значения из секций конфигурации
db_host = config.get('oracle', 'host')
db_port = config.get('oracle', 'port')
db_service_name = config.get('oracle', 'service_name')
db_user_name = config.get('oracle', 'user_name')
db_password = config.get('oracle', 'password')

db_redmine_host = config.get('mysql', 'host')
db_redmine_user_name = config.get('mysql', 'user')
db_redmine_password = config.get('mysql', 'password')
db_redmine_name = config.get('mysql', 'database')

# Проверяем соединение с MySQL


def check_database_connections():
    try:
        # Проверяем соединение с Oracle
        oracle_connection = connect_oracle(
            db_host, db_port, db_service_name, db_user_name, db_password
        )

        if oracle_connection:
            logger.debug("Oracle connection successful")
        else:
            logger.error("Oracle connection failed")

        mysql_connection = get_connection(
            db_redmine_host,
            db_redmine_user_name,
            db_redmine_password,
            db_redmine_name
        )

        if mysql_connection:
            logger.debug("MySQL connection successful")
        else:
            logger.error("MySQL connection failed")

        result = bool(oracle_connection and mysql_connection)
        logger.info(f"Connection check result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in check_database_connections: {str(e)}")
        return False
    finally:
        if 'oracle_connection' in locals() and oracle_connection:
            oracle_connection.close()
        if 'mysql_connection' in locals() and mysql_connection:
            mysql_connection.close()

# Функция проверки доступности таблицы
def check_table_exists(session, table_name):
    """Проверяет существование таблицы в схеме"""
    try:
        result = session.execute(text(f"SELECT 1 FROM {table_name} WHERE ROWNUM = 1"))
        return True
    except Exception:
        return False
