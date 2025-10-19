#!/usr/bin/env python3
"""
Тестовый скрипт для проверки конфигурации Flask приложения
Запускайте из директории проекта: /opt/www/its.teztour.com/
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Загружаем переменные окружения
if os.path.exists('.env.production'):
    from dotenv import load_dotenv
    load_dotenv('.env.production')
    print("✅ Загружен .env.production")
else:
    print("❌ Файл .env.production не найден")

# Проверяем переменные окружения
print("\n📋 Переменные окружения:")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'не установлено')}")
print(f"WTF_CSRF_ENABLED: {os.environ.get('WTF_CSRF_ENABLED', 'не установлено')}")
print(f"SESSION_TYPE: {os.environ.get('SESSION_TYPE', 'не установлено')}")
print(f"SECRET_KEY: {'установлен' if os.environ.get('SECRET_KEY') else 'не установлен'}")

# Пробуем импортировать и создать приложение
try:
    from blog import create_app
    app = create_app()

    print("\n📋 Конфигурация Flask:")
    print(f"DEBUG: {app.debug}")
    print(f"WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED', 'не установлено')}")
    print(f"SESSION_TYPE: {app.config.get('SESSION_TYPE', 'не установлено')}")
    print(f"SECRET_KEY: {'установлен' if app.config.get('SECRET_KEY') else 'не установлен'}")

    # Проверяем наличие CSRF в расширениях (правильный способ)
    if 'csrf' in app.extensions:
        print("\n✅ CSRF найден в расширениях Flask")
    else:
        print("\n❌ CSRF не найден в расширениях Flask")

    # Проверяем наличие CSRF как атрибута приложения
    if hasattr(app, 'csrf'):
        print("✅ CSRF инициализирован как атрибут приложения")
    else:
        print("❌ CSRF не инициализирован как атрибут приложения")

    print("\n🎉 Конфигурация приложения успешно загружена!")

except Exception as e:
    print(f"\n❌ Ошибка при создании приложения: {e}")
    import traceback
    traceback.print_exc()
