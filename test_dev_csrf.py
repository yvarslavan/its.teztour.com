#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы CSRF в режиме разработки
Запускайте из директории проекта: /opt/www/its.teztour.com/
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🧪 Тестирование CSRF в режиме разработки...")

try:
    # Устанавливаем режим разработки
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'True'

    # Создаем тестовый клиент Flask
    from blog import create_app
    app = create_app()

    # Устанавливаем режим отладки
    app.debug = True

    # Создаем тестовый клиент
    client = app.test_client()

    with app.app_context():
        print(f"🔧 Режим отладки: {app.debug}")
        print(f"🔧 WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")

        # Получаем страницу входа
        print("📄 Запрашиваем страницу входа...")
        response = client.get('/login')

        if response.status_code == 200:
            print("✅ Страница входа успешно загружена")

            # Проверяем наличие CSRF токена в форме
            if b'csrf_token' in response.data:
                print("✅ CSRF токен найден в форме")
            else:
                print("❌ CSRF токен не найден в форме (ожидается для режима разработки)")

            # Пытаемся отправить форму
            print("\n📤 Тестируем отправку формы...")
            response = client.post('/login', data={
                'username': 'test',
                'password': 'test',
                'remember': 'y'
            }, follow_redirects=True)

            if response.status_code == 200:
                print("✅ Форма принята без ошибки CSRF (ожидается для режима разработки)")
            else:
                print(f"❌ Ошибка при отправке формы: {response.status_code}")

        else:
            print(f"❌ Ошибка загрузки страницы входа: {response.status_code}")

    print("\n🎉 Тестирование CSRF в режиме разработки завершено!")

except Exception as e:
    print(f"\n❌ Ошибка при тестировании CSRF: {e}")
    import traceback
    traceback.print_exc()
