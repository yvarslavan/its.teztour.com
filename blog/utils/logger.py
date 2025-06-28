import logging
import sys
import os
from logging.handlers import RotatingFileHandler
# Поддержка разных имён пакета: python_json_logger (fork) и python-json-logger (оригинал)
try:
    from python_json_logger.json import JsonFormatter  # наш предпочтительный форк
except ModuleNotFoundError:
    # fallback на официальный пакет python-json-logger, который устанавливается как 'pythonjsonlogger'
    from pythonjsonlogger import jsonlogger as _jsonlogger  # type: ignore
    JsonFormatter = _jsonlogger.JsonFormatter
from config import get

def configure_blog_logger():
    """Конфигурирует логгер для всего пакета 'blog'."""
    log_level_str = get("logging", "level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    blog_package_logger = logging.getLogger('blog')
    blog_package_logger.setLevel(log_level)

    # Предотвращаем повторное добавление обработчиков, если они уже есть
    if not blog_package_logger.handlers:
        formatter = JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(process)d %(module)s %(funcName)s %(lineno)d %(message)s'
        )

        # Файловый обработчик с ротацией (с улучшенной обработкой ошибок)
        try:
            log_file_path = get("logging", "path", "/var/log/flask_helpdesk/app.log")
            log_dir = os.path.dirname(log_file_path)

            os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=1024 * 1024 * 5,  # 5 MBP
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            blog_package_logger.addHandler(file_handler)
        except Exception as e:
            logging.basicConfig()
            logging.getLogger().critical(f"Failed to configure file logger: {e}")

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        blog_package_logger.addHandler(console_handler)
