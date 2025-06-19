import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from config import get

def configure_blog_logger():
    """Конфигурирует логгер для всего пакета 'blog'."""
    blog_package_logger = logging.getLogger('blog')
    blog_package_logger.setLevel(logging.DEBUG)

    # Предотвращаем повторное добавление обработчиков, если они уже есть
    if not blog_package_logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Файловый обработчик с ротацией (с улучшенной обработкой ошибок)
        try:
            log_file_path = get("logging", "path", "app.log")
            # Добавляем PID к имени лога для избежания конфликтов
            pid = os.getpid()
            log_file_name = f"app_{pid}.log"
            log_dir = os.path.dirname(log_file_path)
            log_file_path_with_pid = os.path.join(log_dir, log_file_name)

            file_handler = RotatingFileHandler(
                log_file_path_with_pid,
                maxBytes=1024 * 1024 * 5,  # 5 MB
                backupCount=3,
                encoding='utf-8',
                delay=True  # Откладывает создание файла до первой записи
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            blog_package_logger.addHandler(file_handler)
        except Exception as e:
            print(f"CRITICAL: Failed to configure file logger: {e}", file=sys.stderr)
            # Продолжаем работу только с консольным логированием

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        blog_package_logger.addHandler(console_handler)
