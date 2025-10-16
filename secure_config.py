"""
Безопасная конфигурация приложения с использованием переменных окружения
Заменяет небезопасный config.ini
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class SecureConfig:
    """Безопасный класс конфигурации"""

    def __init__(self):
        self.load_from_env()

    def load_from_env(self):
        """Загрузка конфигурации из переменных окружения"""

        # Oracle Database Configuration
        self.oracle_host = os.getenv('ORACLE_HOST', 'localhost')
        self.oracle_port = os.getenv('ORACLE_PORT', '1521')
        self.oracle_service_name = os.getenv('ORACLE_SERVICE_NAME', '')
        self.oracle_user = os.getenv('ORACLE_USER', '')
        self.oracle_password = os.getenv('ORACLE_PASSWORD', '')

        # MySQL Database Configuration
        self.mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        self.mysql_database = os.getenv('MYSQL_DATABASE', '')
        self.mysql_user = os.getenv('MYSQL_USER', '')
        self.mysql_password = os.getenv('MYSQL_PASSWORD', '')

        # Redmine Configuration
        self.redmine_url = os.getenv('REDMINE_URL', '')
        self.redmine_api_key = os.getenv('REDMINE_API_KEY', '')
        self.redmine_login_admin = os.getenv('REDMINE_LOGIN_ADMIN', '')
        self.redmine_password_admin = os.getenv('REDMINE_PASSWORD_ADMIN', '')
        self.redmine_anonymous_user_id = os.getenv('REDMINE_ANONYMOUS_USER_ID', '4')

        # Quality MySQL Configuration
        self.mysql_quality_host = os.getenv('MYSQL_QUALITY_HOST', 'localhost')
        self.mysql_quality_database = os.getenv('MYSQL_QUALITY_DATABASE', '')
        self.mysql_quality_user = os.getenv('MYSQL_QUALITY_USER', '')
        self.mysql_quality_password = os.getenv('MYSQL_QUALITY_PASSWORD', '')

        # Quality Redmine Configuration
        self.redmine_quality_url = os.getenv('REDMINE_QUALITY_URL', '')
        self.redmine_quality_api_key = os.getenv('REDMINE_QUALITY_API_KEY', '')
        self.redmine_quality_login_admin = os.getenv('REDMINE_QUALITY_LOGIN_ADMIN', '')
        self.redmine_quality_password_admin = os.getenv('REDMINE_QUALITY_PASSWORD_ADMIN', '')
        self.redmine_quality_anonymous_user_id = os.getenv('REDMINE_QUALITY_ANONYMOUS_USER_ID', '4')

        # Database Path
        self.db_path = os.getenv('DB_PATH', 'blog/db/blog.db')

        # XMPP Configuration
        self.xmpp_jabberid = os.getenv('XMPP_JABBERID', '')
        self.xmpp_sender_password = os.getenv('XMPP_SENDER_PASSWORD', '')

        # Recovery Password URL
        self.recovery_password_url = os.getenv('RECOVERY_PASSWORD_URL', '')

        # File Paths
        self.erp_file_path = os.getenv('ERP_FILE_PATH', '')

        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_path = os.getenv('LOG_PATH', 'logs/app.log')

        # Email Configuration
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')

        # GitHub Configuration
        self.github_token = os.getenv('GITHUB_TOKEN', '')

        # Flask Configuration
        self.flask_env = os.getenv('FLASK_ENV', 'development')
        self.secret_key = os.getenv('SECRET_KEY', os.urandom(32).hex())

    def get_oracle_config(self) -> dict:
        """Получить конфигурацию Oracle"""
        return {
            'host': self.oracle_host,
            'port': self.oracle_port,
            'service_name': self.oracle_service_name,
            'user_name': self.oracle_user,
            'password': self.oracle_password
        }

    def get_mysql_config(self) -> dict:
        """Получить конфигурацию MySQL"""
        return {
            'host': self.mysql_host,
            'database': self.mysql_database,
            'user': self.mysql_user,
            'password': self.mysql_password
        }

    def get_redmine_config(self) -> dict:
        """Получить конфигурацию Redmine"""
        return {
            'url': self.redmine_url,
            'api_key': self.redmine_api_key,
            'login_admin': self.redmine_login_admin,
            'password_admin': self.redmine_password_admin,
            'anonymous_user_id': self.redmine_anonymous_user_id
        }

    def get_mysql_quality_config(self) -> dict:
        """Получить конфигурацию MySQL Quality"""
        return {
            'host': self.mysql_quality_host,
            'database': self.mysql_quality_database,
            'user': self.mysql_quality_user,
            'password': self.mysql_quality_password
        }

    def validate_required_vars(self) -> list:
        """Проверить наличие обязательных переменных окружения"""
        required_vars = [
            'ORACLE_HOST', 'ORACLE_SERVICE_NAME', 'ORACLE_USER', 'ORACLE_PASSWORD',
            'MYSQL_HOST', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD',
            'REDMINE_URL', 'REDMINE_API_KEY'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        return missing_vars

# Глобальный экземпляр конфигурации
config = SecureConfig()

def get_config() -> SecureConfig:
    """Получить экземпляр конфигурации"""
    return config

if __name__ == "__main__":
    # Проверка конфигурации
    missing = config.validate_required_vars()
    if missing:
        print(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
        print("Пожалуйста, установите их в .env файле или переменных окружения")
    else:
        print("Конфигурация загружена успешно")
