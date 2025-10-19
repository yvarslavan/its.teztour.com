#!/usr/bin/env python3
"""
Простой тест для проверки работы CSRF
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🧪 Простой тест CSRF...")

try:
    # Загружаем переменные окружения
    if os.path.exists('.env.production'):
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        print("✅ Загружен .env.production")

    # Создаем тестовый клиент Flask
    from blog import create_app
    app = create_app()

    # Создаем тестовый клиент
    client = app.test_client()

    with app.app_context():
        # Получаем страницу входа
        print("📄 Запрашиваем страницу входа...")
        response = client.get('/login')

        if response.status_code == 200:
            print("✅ Страница входа успешно загружена")

            # Извлекаем CSRF токен используя стандартный подход Flask-WTF
            with client.session_transaction() as sess:
                # Сохраняем сессию для дальнейшего использования
                print(f"🔍 Сессия после GET запроса: {list(sess.keys())}")

            # Пытаемся отправить форму без данных (должно сработать с CSRF)
            print("\n📤 Тестируем отправку пустой формы...")
            response = client.post('/login', data={}, follow_redirects=False)

            print(f"🔍 Статус POST запроса: {response.status_code}")
            if response.status_code == 200:
                print("✅ Форма принята без ошибки CSRF (пустая форма)")
            elif response.status_code == 400:
                print("❌ Форма отклонена с ошибкой 400")
                if b'csrf' in response.data.lower():
                    print("❌ Это ошибка CSRF")
                else:
                    print("✅ Это не ошибка CSRF, а другая проблема валидации")
            else:
                print(f"🔍 Ответ со статусом: {response.status_code}")

            # Пробуем с правильными данными пользователя
            print("\n📤 Тестируем отправку формы с данными...")
            response = client.post('/login', data={
                'username': 'test_user',
                'password': 'test_password',
                'remember': False
            }, follow_redirects=False)

            print(f"🔍 Статус POST запроса: {response.status_code}")
            if response.status_code == 200:
                print("✅ Форма принята без ошибки CSRF")
            elif response.status_code == 400:
                print("❌ Форма отклонена с ошибкой 400")
                if b'csrf' in response.data.lower():
                    print("❌ Это ошибка CSRF")
                else:
                    print("✅ Это не ошибка CSRF, а другая проблема валидации")
            else:
                print(f"🔍 Ответ со статусом: {response.status_code}")

        else:
            print(f"❌ Ошибка загрузки страницы входа: {response.status_code}")

    print("\n🎉 Тестирование CSRF завершено!")

except Exception as e:
    print(f"\n❌ Ошибка при тестировании CSRF: {e}")
    import traceback
    traceback.print_exc()
