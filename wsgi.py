#!/usr/bin/env python3
"""
WSGI точка входа для продакшена
Используется веб-серверами (Apache, Nginx + uWSGI/Gunicorn)
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging



logging.basicConfig(
    filename='logs/flask_debug.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# Настройка логгера Flask
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
for handler in flask_logger.handlers:
    flask_logger.removeHandler(handler)
file_handler = logging.FileHandler('logs/flask_debug.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
flask_logger.addHandler(file_handler)

# Настройка логгера приложения (current_app.logger)
app_logger = logging.getLogger()
app_logger.setLevel(logging.INFO)
app_logger.addHandler(file_handler)
def setup_production_environment():
    """Настройка переменных окружения для продакшена"""
    BASE_DIR = Path(__file__).resolve().parent

    # Определяем окружение (автоматически по ОС)
    env = 'production' if os.name != 'nt' else 'development'
    os.environ.setdefault('FLASK_ENV', env)

    # Выбираем файл конфигурации
    if env == 'production':
        env_file = BASE_DIR / '.env.production'
    else:
        env_file = BASE_DIR / '.env.development'

    # Загружаем переменные окружения
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📦 Загружены настройки из {env_file}")
    else:
        print(f"⚠️  Файл {env_file} не найден, используются переменные системы")
        # Устанавливаем базовые переменные для продакшена
        if env == 'production':
            os.environ.setdefault('FLASK_ENV', 'production')
            os.environ.setdefault('FLASK_DEBUG', 'False')
            os.environ.setdefault('WTF_CSRF_ENABLED', 'True')
            print("✅ Установлены базовые настройки для продакшена")

    # Создаем необходимые директории
    db_dir = BASE_DIR / 'blog' / 'db'
    db_dir.mkdir(parents=True, exist_ok=True)

    print(f"🌍 Окружение: {env}")
    return env

# Настраиваем окружение при импорте модуля
environment = setup_production_environment()

# Импортируем и создаем приложение
from blog import create_app

app = create_app()

for handler in app.logger.handlers[:]:
    app.logger.removeHandler(handler)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Дополнительные настройки только для продакшена
if environment == 'production':
    # Настройки безопасности для продакшена
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_DOMAIN='.tez-tour.com',
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax'
    )
    print("🔒 Применены настройки безопасности для продакшена")

# Информация о конфигурации для отладки
if app.debug or environment == 'development':
    print(f"🔧 DEBUG режим: {app.debug}")
    print(f"🔧 TEMPLATES_AUTO_RELOAD: {app.config.get('TEMPLATES_AUTO_RELOAD')}")

if __name__ == "__main__":
    # Этот блок выполняется только при прямом запуске wsgi.py
    # Не рекомендуется для продакшена, используйте app.py для разработки
    print("⚠️  Прямой запуск wsgi.py не рекомендуется!")
    print("   Для разработки используйте: python app.py")
    print("   Для продакшена используйте WSGI сервер (gunicorn, uWSGI)")

    app.run(
        debug=(environment == 'development'),
        host='0.0.0.0',
        port=5000,
        use_reloader=False,
        threaded=True
    )
