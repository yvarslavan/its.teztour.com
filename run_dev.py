#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Файл для запуска Flask приложения в режиме разработки
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from blog import create_app

# Устанавливаем режим разработки
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Загружаем переменные окружения из .flaskenv
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.flaskenv'
if env_path.exists():
    load_dotenv(env_path)

# Импортируем и создаем приложение

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 FLASK DEVELOPMENT SERVER")
    print("=" * 60)
    print(f"📁 Проект: {BASE_DIR}")
    print(f"🔧 Debug режим: {app.debug}")
    print(f"🌐 Сервер будет доступен по адресу:")
    print("   ➡️  http://localhost:5000")
    print("   ➡️  http://127.0.0.1:5000")
    print("=" * 60)

    # Запускаем сервер с правильными настройками для разработки
    app.run(
        debug=True,           # Включаем DEBUG режим
        host='127.0.0.1',     # Локальный хост
        port=5000,            # Порт
        use_reloader=True,    # Автоперезагрузка при изменениях
        use_debugger=True,    # Встроенный отладчик
        threaded=True         # Многопоточность
    )
