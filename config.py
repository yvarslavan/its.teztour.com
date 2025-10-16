import configparser
import os

def get_config():
    """
    Получить конфигурацию из безопасного источника.
    Приоритет: переменные окружения > config.ini (устаревший)
    """
    try:
        # Пытаемся использовать безопасную конфигурацию
        from secure_config import get_config as get_secure_config
        secure_config = get_secure_config()

        # Проверяем, что все обязательные переменные установлены
        missing = secure_config.validate_required_vars()
        if not missing:
            print("✅ Используется безопасная конфигурация из переменных окружения")
            return secure_config
        else:
            print(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing)}")
            print("🔄 Используется config.ini как резервный вариант")

    except ImportError:
        print("⚠️ Модуль secure_config не найден, используется config.ini")

    # Резервный вариант: старая конфигурация
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    config.read(config_path)
    print("⚠️ ИСПОЛЬЗУЕТСЯ УСТАРЕВШАЯ КОНФИГУРАЦИЯ config.ini")
    print("🔧 Рекомендуется перейти на переменные окружения (см. secure_config.py)")

    return config

def get_config_value(section, key, fallback=None):
    """
    Универсальный метод получения конфигурации
    Совместим со старым кодом и новой безопасной конфигурацией
    """
    config = get_config()

    # Если это безопасная конфигурация
    if hasattr(config, 'get_oracle_config'):
        # Маппинг секций и ключей для безопасной конфигурации
        section_mapping = {
            'oracle': {
                'host': config.oracle_host,
                'port': config.oracle_port,
                'service_name': config.oracle_service_name,
                'user_name': config.oracle_user,
                'password': config.oracle_password
            },
            'mysql': {
                'host': config.mysql_host,
                'database': config.mysql_database,
                'user': config.mysql_user,
                'password': config.mysql_password
            },
            'mysql_quality': {
                'host': config.mysql_quality_host,
                'database': config.mysql_quality_database,
                'user': config.mysql_quality_user,
                'password': config.mysql_quality_password
            },
            'redmine': {
                'url': config.redmine_url,
                'api_key': config.redmine_api_key,
                'login_admin': config.redmine_login_admin,
                'password_admin': config.redmine_password_admin,
                'anonymous_user_id': config.redmine_anonymous_user_id
            },
            'database': {
                'db_path': config.db_path
            },
            'xmpp': {
                'jabberid': config.xmpp_jabberid,
                'sender_password': config.xmpp_sender_password
            },
            'RecoveryPassword': {
                'url': config.recovery_password_url
            },
            'FilePaths': {
                'erp_file_path': config.erp_file_path
            },
            'sender_email': {
                'sender_email': config.sender_email,
                'sender_password': config.sender_password
            }
        }

        if section in section_mapping and key in section_mapping[section]:
            value = section_mapping[section][key]
            if value is not None:
                return value

    # Для старой конфигурации или если ключ не найден
    if hasattr(config, 'get'):
        return config.get(section, key, fallback=fallback)
    elif fallback is not None:
        return fallback
    else:
        raise KeyError(f"Ключ '{key}' не найден в секции '{section}'")

def get_legacy(section, key, fallback=None):
    """
    Функция для обратной совместимости
    Вызывает новый метод get_config_value
    """
    return get_config_value(section, key, fallback)

# Создаем псевдоним для обратной совместимости
get = get_legacy
