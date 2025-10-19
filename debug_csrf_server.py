#!/usr/bin/env python3
"""
Скрипт для отладки CSRF на сервере
Запускать на сервере: python3 debug_csrf_server.py
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🔧 Отладка CSRF на сервере...")

try:
    # Проверяем переменные окружения
    print("\n🔍 Проверка переменных окружения:")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'не установлена')}")
    print(f"FLASK_DEBUG: {os.environ.get('FLASK_DEBUG', 'не установлена')}")
    print(f"WTF_CSRF_ENABLED: {os.environ.get('WTF_CSRF_ENABLED', 'не установлена')}")

    # Загружаем переменные окружения
    if os.path.exists('.env.production'):
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        print("✅ Загружен .env.production")
    elif os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv('.env')
        print("✅ Загружен .env")
    else:
        print("❌ Файл .env не найден")

    # Создаем тестовый клиент Flask
    from blog import create_app
    app = create_app()

    print("\n🔍 Конфигурация приложения:")
    print(f"DEBUG: {app.debug}")
    print(f"WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")
    print(f"SECRET_KEY установлен: {'да' if app.secret_key else 'нет'}")
    print(f"SESSION_TYPE: {app.config.get('SESSION_TYPE', 'не установлен')}")
    print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
    print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")

    # Создаем тестовый клиент
    client = app.test_client()

    with app.app_context():
        # Получаем страницу входа
        print("\n📄 Запрашиваем страницу входа...")
        response = client.get('/login')

        if response.status_code == 200:
            print("✅ Страница входа успешно загружена")

            # Сохраняем HTML для анализа
            with open('login_page_debug.html', 'wb') as f:
                f.write(response.data)
            print("💾 HTML страницы сохранен в login_page_debug.html")

            # Проверяем наличие формы
            if b'<form' in response.data:
                print("✅ Форма найдена на странице")

                # Проверяем наличие скрытых полей
                if b'hidden' in response.data:
                    print("✅ Скрытые поля найдены")
                else:
                    print("❌ Скрытые поля не найдены")

                # Проверяем наличие CSRF токена
                if b'csrf_token' in response.data:
                    print("✅ CSRF токен найден в HTML")
                else:
                    print("❌ CSRF токен не найден в HTML")
            else:
                print("❌ Форма не найдена на странице")

            # Проверяем настройки сессии
            with client.session_transaction() as sess:
                print(f"\n🔍 Сессия после GET запроса: {list(sess.keys())}")
                if 'csrf_token' in sess:
                    print(f"✅ CSRF токен в сессии: {sess['csrf_token']}")
                else:
                    print("❌ CSRF токен отсутствует в сессии")

            # Тестируем POST запрос
            print("\n📤 Тестируем POST запрос...")

            # Сначала без CSRF токена
            response = client.post('/login', data={
                'username': 'test',
                'password': 'test'
            })

            print(f"🔍 Статус POST без CSRF: {response.status_code}")
            if response.status_code == 400 and b'csrf' in response.data.lower():
                print("✅ CSRF защита работает (запрос отклонен)")

            # Затем с CSRF токеном
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()

            # Устанавливаем токен в сессии
            with client.session_transaction() as sess:
                sess['csrf_token'] = csrf_token

            response = client.post('/login', data={
                'csrf_token': csrf_token,
                'username': 'test',
                'password': 'test'
            })

            print(f"🔍 Статус POST с CSRF: {response.status_code}")
            if response.status_code != 400 or b'csrf' not in response.data.lower():
                print("✅ CSRF токен принят")
            else:
                print("❌ CSRF токен отклонен")
                print(f"🔍 Ответ сервера: {response.data[:200]}")

        else:
            print(f"❌ Ошибка загрузки страницы входа: {response.status_code}")
            print(f"🔍 Ответ сервера: {response.data[:200]}")

    print("\n🎉 Отладка CSRF завершена!")
    print("\n💡 Рекомендации:")
    print("1. Убедитесь, что SECRET_KEY установлен в .env.production")
    print("2. Проверьте, что WTF_CSRF_ENABLED=True в продакшене")
    print("3. Убедитесь, что SESSION_TYPE настроен (filesystem или redis)")
    print("4. Проверьте права доступа к директории сессий")

except Exception as e:
    print(f"\n❌ Ошибка при отладке CSRF: {e}")
    import traceback
    traceback.print_exc()
