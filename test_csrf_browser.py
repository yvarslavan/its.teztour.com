#!/usr/bin/env python3
"""
Тест CSRF, имитирующий поведение браузера
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🧪 Тест CSRF с имитацией браузера...")

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

            # Извлекаем все скрытые поля из формы
            import re
            hidden_fields = {}
            hidden_input_pattern = rb'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\'][^>]*>'

            for match in re.finditer(hidden_input_pattern, response.data):
                field_name = match.group(1).decode('utf-8')
                field_value = match.group(2).decode('utf-8')
                hidden_fields[field_name] = field_value
                print(f"🔍 Найдено скрытое поле: {field_name} = {field_value}")

            # Проверяем наличие CSRF токена
            if 'csrf_token' in hidden_fields:
                csrf_token = hidden_fields['csrf_token']
                print(f"✅ CSRF токен найден: {csrf_token}")

                # Создаем данные для отправки формы
                form_data = hidden_fields.copy()
                form_data.update({
                    'username': 'test_user',
                    'password': 'test_password',
                    'remember': 'y'
                })

                print("\n📤 Отправляем форму с CSRF токеном...")

                # Отправляем форму
                response = client.post('/login', data=form_data, follow_redirects=False)

                print(f"🔍 Статус POST запроса: {response.status_code}")

                if response.status_code == 302:
                    print("✅ Перенаправление (успешная авторизация)")
                elif response.status_code == 200:
                    print("✅ Форма принята (остались ошибки валидации)")
                    # Проверяем, нет ли ошибки CSRF
                    if b'csrf' not in response.data.lower():
                        print("✅ Ошибок CSRF нет")
                    else:
                        print("❌ Присутствует ошибка CSRF")
                elif response.status_code == 400:
                    print("❌ Форма отклонена с ошибкой 400")
                    if b'csrf' in response.data.lower():
                        print("❌ Это ошибка CSRF")
                        print(f"🔍 Содержимое ошибки: {response.data[:200]}")
                    else:
                        print("✅ Это не ошибка CSRF, а другая проблема валидации")
                else:
                    print(f"🔍 Неожиданный статус: {response.status_code}")
            else:
                print("❌ CSRF токен не найден в форме")

                # Если CSRF токен не найден, пробуем сгенерировать его
                from flask_wtf.csrf import generate_csrf
                csrf_token = generate_csrf()
                print(f"🔍 Сгенерированный CSRF токен: {csrf_token}")

                # Устанавливаем токен в сессии
                with client.session_transaction() as sess:
                    sess['csrf_token'] = csrf_token

                # Отправляем форму с сгенерированным токеном
                form_data = {
                    'csrf_token': csrf_token,
                    'username': 'test_user',
                    'password': 'test_password',
                    'remember': 'y'
                }

                response = client.post('/login', data=form_data, follow_redirects=False)
                print(f"🔍 Статус POST запроса с сгенерированным токеном: {response.status_code}")

        else:
            print(f"❌ Ошибка загрузки страницы входа: {response.status_code}")

    print("\n🎉 Тестирование CSRF завершено!")

except Exception as e:
    print(f"\n❌ Ошибка при тестировании CSRF: {e}")
    import traceback
    traceback.print_exc()
