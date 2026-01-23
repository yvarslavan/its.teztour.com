#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный файл для запуска Flask приложения в режиме разработки
Заменяет run_server.py и run_dev.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# ВАЖНО: Полностью отключаем прокси ДО импорта любых библиотек
# Удаляем все прокси-переменные и устанавливаем NO_PROXY=* для гарантии
for _proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                   'ALL_PROXY', 'all_proxy']:
    if _proxy_var in os.environ:
        del os.environ[_proxy_var]
# Устанавливаем NO_PROXY=* чтобы гарантированно отключить прокси для всех хостов
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'


def setup_development_environment():
    """Настройка переменных окружения для разработки"""
    # Устанавливаем режим разработки
    os.environ["FLASK_ENV"] = "development"
    os.environ["FLASK_DEBUG"] = "1"

    # Настраиваем простое логирование - используем безопасный обработчик из blog.utils.logger
    import logging

    # Проверяем, уже настроен ли логгер, чтобы избежать дублирования
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        try:
            from blog.utils.logger import configure_blog_logger
            configure_blog_logger()
        except ImportError:
            # Fallback если blog.utils.logger недоступен
            from logging.handlers import RotatingFileHandler

            os.makedirs('logs', exist_ok=True)
            file_handler = RotatingFileHandler(
                'logs/app.log',
                maxBytes=int(os.getenv('LOG_MAX_BYTES', str(10 * 1024 * 1024))),
                backupCount=int(os.getenv('LOG_BACKUP_COUNT', '5')),
                encoding='utf-8'
            )

            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    file_handler,
                    logging.StreamHandler()
                ],
                force=True
            )

    # Suppress RotatingFileHandler permission errors on Windows
    import warnings
    warnings.filterwarnings("ignore", message=".*RotatingFileHandler.*PermissionError.*", category=UserWarning)

    print("✅ Логирование настроено")

    # Загружаем конфигурацию в зависимости от окружения
    BASE_DIR = Path(__file__).resolve().parent

    # Определяем окружение (development по умолчанию для локальной разработки)
    env_mode = os.environ.get("FLASK_ENV", "development")

    # Проверяем что мы в WSL
    is_wsl = False
    try:
        with open('/proc/version', 'r') as f:
            is_wsl = 'microsoft' in f.read().lower()
    except:
        pass

    # Выбираем файл конфигурации
    if env_mode == "production":
        env_path = BASE_DIR / ".env.production"
        if not env_path.exists():
            env_path = BASE_DIR / ".env"  # Fallback на .env если production нет
    else:
        # В WSL всегда используем .env (создается setup_wsl_config.py)
        if is_wsl and (BASE_DIR / ".env").exists():
            env_path = BASE_DIR / ".env"
        else:
            env_path = BASE_DIR / ".env.development"
            if not env_path.exists():
                env_path = BASE_DIR / ".env"  # Fallback на .env если development нет

    if env_path.exists():
        load_dotenv(env_path)
        wsl_info = " [WSL detected]" if is_wsl else ""
        print(f"✅ Загружены переменные окружения из {env_path.name} (режим: {env_mode}){wsl_info}")
    else:
        print("⚠️ Файл конфигурации не найден. Создайте .env.development или .env.production")


def main():
    """Основная функция запуска"""
    # Настраиваем окружение разработки
    setup_development_environment()

    # Импортируем после настройки окружения
    from blog import create_app

    # Создаем приложение
    app = create_app()

    # Красивый вывод информации о запуске
    print("=" * 60)
    print("🚀 FLASK DEVELOPMENT SERVER")
    print("=" * 60)
    print(f"📁 Проект: {Path(__file__).resolve().parent}")
    print(f"🔧 Debug режим: {app.debug}")
    print(f"🔧 Окружение: {os.environ.get('FLASK_ENV', 'не определено')}")
    print(f"🌐 Сервер будет доступен по адресам:")
    print("   ➡️  http://localhost:5000")
    print("   ➡️  http://127.0.0.1:5000")
    print("   ➡️  http://0.0.0.0:5000 (внешний доступ)")
    print("📍 Главные страницы:")
    print("   ➡️  http://localhost:5000/tasks/my-tasks")
    print("   ➡️  http://localhost:5000/users/login")
    print("=" * 60)

    # Запускаем сервер с оптимальными настройками для разработки
    try:
        app.run(
            debug=True,  # DEBUG режим
            host="0.0.0.0",  # Доступ извне (для тестирования на других устройствах)
            port=int(
                os.environ.get("FLASK_RUN_PORT", 5000)
            ),  # Порт из переменных или 5000
            use_reloader=True,  # Автоперезагрузка при изменениях
            use_debugger=True,  # Встроенный отладчик
            threaded=True,  # Многопоточность
            load_dotenv=False,  # Мы уже загрузили переменные
        )
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
