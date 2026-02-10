#!/usr/bin/env python3
"""
WSGI точка входа для продакшена
Используется веб-серверами (Apache, Nginx + uWSGI/Gunicorn)
"""

import os
from pathlib import Path
from env_loader import load_environment
import logging
from logging.handlers import RotatingFileHandler

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

_log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_str, logging.INFO)

file_handler = RotatingFileHandler(
    os.path.join(log_dir, "flask_debug.log"),
    maxBytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
    backupCount=int(os.getenv("LOG_BACKUP_COUNT", "5")),
    encoding="utf-8",
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)

# Настройка логгера Flask
flask_logger = logging.getLogger("werkzeug")
flask_logger.setLevel(_log_level)
for handler in flask_logger.handlers[:]:
    flask_logger.removeHandler(handler)
flask_logger.addHandler(file_handler)

# Настройка корневого логгера (current_app.logger использует его хендлеры)
app_logger = logging.getLogger()
app_logger.setLevel(_log_level)
for handler in app_logger.handlers[:]:
    app_logger.removeHandler(handler)
app_logger.addHandler(file_handler)


def setup_production_environment():
    """Настройка переменных окружения для продакшена"""
    BASE_DIR = Path(__file__).resolve().parent

    # Определяем окружение (автоматически по ОС)
    env = "production" if os.name != "nt" else "development"
    os.environ.setdefault("FLASK_ENV", env)

    env_path, env_loaded, _ = load_environment(BASE_DIR, env)

    if env_loaded:
        print(f"📦 Загружены настройки из {env_path}")
    else:
        print(f"⚠️  Файл {env_path} не найден, используются переменные системы")

    # Переопределяем настройки для production
    if env == "production":
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_DEBUG"] = "False"
        os.environ["WTF_CSRF_ENABLED"] = "True"
        print("✅ Установлены настройки для продакшена")

    # Создаем необходимые директории
    db_dir = BASE_DIR / "blog" / "db"
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
if environment == "production":
    # Настройки безопасности для продакшена
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_DOMAIN=".tez-tour.com",
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
    )
    print("🔒 Применены настройки безопасности для продакшена")

# Информация о конфигурации для отладки
if app.debug or environment == "development":
    print(f"🔧 DEBUG режим: {app.debug}")
    print(f"🔧 TEMPLATES_AUTO_RELOAD: {app.config.get('TEMPLATES_AUTO_RELOAD')}")

if __name__ == "__main__":
    # Этот блок выполняется только при прямом запуске wsgi.py
    # Не рекомендуется для продакшена, используйте app.py для разработки
    print("⚠️  Прямой запуск wsgi.py не рекомендуется!")
    print("   Для разработки используйте: python app.py")
    print("   Для продакшена используйте WSGI сервер (gunicorn, uWSGI)")

    app.run(
        debug=(environment == "development"),
        host="0.0.0.0",
        port=5000,
        use_reloader=False,
        threaded=True,
    )
