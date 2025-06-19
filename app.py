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

def setup_development_environment():
    """Настройка переменных окружения для разработки"""
    # Устанавливаем режим разработки
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'

    # Загружаем переменные из .flaskenv (если есть)
    BASE_DIR = Path(__file__).resolve().parent
    flaskenv_path = BASE_DIR / '.flaskenv'

    if flaskenv_path.exists():
        load_dotenv(flaskenv_path)
        print(f"✅ Загружены настройки из {flaskenv_path}")

    # Загружаем dev конфигурацию
    env_dev_path = BASE_DIR / '.env.development'
    if env_dev_path.exists():
        load_dotenv(env_dev_path)
        print(f"✅ Загружены настройки разработки из {env_dev_path}")

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
            debug=True,              # DEBUG режим
            host='0.0.0.0',          # Доступ извне (для тестирования на других устройствах)
            port=int(os.environ.get('FLASK_RUN_PORT', 5000)),  # Порт из переменных или 5000
            use_reloader=True,       # Автоперезагрузка при изменениях
            use_debugger=True,       # Встроенный отладчик
            threaded=True,           # Многопоточность
            load_dotenv=False        # Мы уже загрузили переменные
        )
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
