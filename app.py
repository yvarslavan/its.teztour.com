#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный файл для запуска Flask приложения в режиме разработки
Заменяет run_server.py и run_dev.py
"""

import os
import sys
from pathlib import Path
from env_loader import load_environment

env_path, env_loaded, is_wsl = load_environment(Path(__file__).resolve().parent)
# ВАЖНО: Полностью отключаем прокси ДО импорта любых библиотек
# Удаляем все прокси-переменные и устанавливаем NO_PROXY=* для гарантии
for _proxy_var in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
]:
    if _proxy_var in os.environ:
        del os.environ[_proxy_var]
# Устанавливаем NO_PROXY=* чтобы гарантированно отключить прокси для всех хостов
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"


def configure_console_output():
    """Пытается включить UTF-8 вывод в консоли, если это поддерживается."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(message: str):
    """Печать без падения на UnicodeEncodeError в старых кодировках консоли."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        fallback = str(message).encode(encoding, errors="replace").decode(
            encoding, errors="replace"
        )
        print(fallback)


def setup_development_environment():
    """Настройка переменных окружения.

    По умолчанию запускаем development, но не перезаписываем
    явно заданный FLASK_ENV (например, в production service).
    """
    env_mode = os.environ.get("FLASK_ENV", "development").strip().lower()

    # В development включаем debug по умолчанию.
    # В production/staging не перезаписываем режим принудительно.
    if env_mode in {"production", "staging"}:
        os.environ.setdefault("FLASK_DEBUG", "0")
    else:
        os.environ.setdefault("FLASK_ENV", "development")
        os.environ.setdefault("FLASK_DEBUG", "1")

    # Настраиваем логирование через централизованный модуль blog.utils.logger
    try:
        from blog.utils.logger import configure_blog_logger

        configure_blog_logger()
    except ImportError as e:
        # Fallback только если blog.utils.logger недоступен
        import logging
        from logging.handlers import RotatingFileHandler

        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[file_handler, logging.StreamHandler()],
            force=True,
        )

    safe_print("✅ Логирование настроено")

    # Загружаем конфигурацию в зависимости от окружения
    BASE_DIR = Path(__file__).resolve().parent
    env_mode = os.environ.get("FLASK_ENV", "development")

    env_path, env_loaded, is_wsl = load_environment(BASE_DIR, env_mode)
    if env_loaded:
        wsl_info = " [WSL detected]" if is_wsl else ""
        safe_print(
            f"✅ Загружены переменные окружения из {env_path.name} (режим: {env_mode}){wsl_info}"
        )
    else:
        if env_path.exists():
            safe_print(
                f"ℹ️ Переменные окружения уже загружены ранее из {env_path.name}"
            )
        else:
            safe_print(f"⚠️ Файл конфигурации не найден: {env_path}")


def main():
    """Основная функция запуска"""
    configure_console_output()

    # Настраиваем окружение разработки
    setup_development_environment()

    # Импортируем после настройки окружения
    from blog import create_app

    # Создаем приложение
    app = create_app()

    # Красивый вывод информации о запуске
    safe_print("=" * 60)
    safe_print("🚀 FLASK DEVELOPMENT SERVER")
    safe_print("=" * 60)
    safe_print(f"📁 Проект: {Path(__file__).resolve().parent}")
    safe_print(f"🔧 Debug режим: {app.debug}")
    safe_print(f"🔧 Окружение: {os.environ.get('FLASK_ENV', 'не определено')}")
    safe_print("🌐 Сервер будет доступен по адресам:")
    safe_print("   ➡️  http://localhost:5000")
    safe_print("   ➡️  http://127.0.0.1:5000")
    safe_print("   ➡️  http://0.0.0.0:5000 (внешний доступ)")
    safe_print("📍 Главные страницы:")
    safe_print("   ➡️  http://localhost:5000/tasks/my-tasks")
    safe_print("   ➡️  http://localhost:5000/users/login")
    safe_print("=" * 60)

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
        safe_print("\n🛑 Сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        safe_print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
