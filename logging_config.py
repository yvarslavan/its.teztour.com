"""
Конфигурация системы ротации логов с оптимальными параметрами
Размер файла: 10MB, хранение 7 архивов
"""
import logging
import logging.handlers
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настройка ротации логов с оптимальными параметрами"""

    # Создаем директорию для логов, если она не существует
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Основной файл лога
    log_file = os.path.join(log_dir, 'app.log')

    # Настройка ротации: 10MB на файл, 7 архивов
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=7,
        encoding='utf-8'
    )

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Отдельный логгер для ошибок
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=7,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(error_handler)

    return logger, error_logger

def archive_current_log():
    """Архивация текущего файла лога"""
    import shutil
    from datetime import datetime

    current_log = 'app_err.log'
    if os.path.exists(current_log):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f'app_err_log_archived_{timestamp}.log'
        shutil.move(current_log, archive_name)
        print(f"Лог файл архивирован как: {archive_name}")
        return archive_name
    return None

if __name__ == "__main__":
    # Тестирование настройки логов
    logger, error_logger = setup_logging()
    logger.info("Система ротации логов настроена")
    error_logger.error("Тест записи ошибки")
    print("Логирование настроено успешно")
