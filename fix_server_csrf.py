#!/usr/bin/env python3
"""
Скрипт для исправления проблемы CSRF на сервере
Запускать на сервере: python3 fix_server_csrf.py
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🔧 Исправление CSRF на сервере...")

try:
    # Проверяем наличие .env.production
    env_file = BASE_DIR / '.env.production'
    if not env_file.exists():
        print("❌ Файл .env.production не найден")
        print("Создаем базовый .env.production...")

        # Создаем базовый .env.production
        with open(env_file, 'w') as f:
            f.write("""# =============================================================================
# ОСНОВНЫЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ (ПРОДАКШЕН)
# =============================================================================
FLASK_ENV=production
SECRET_KEY=production-secret-key-change-this-in-real-deployment-2024
DEBUG=False

# =============================================================================
# НАСТРОЙКИ CSRF И СЕССИЙ
# =============================================================================
WTF_CSRF_ENABLED=True
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400

# =============================================================================
# НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА
# =============================================================================
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_DOMAIN=its.tez-tour.com
""")
        print("✅ Создан файл .env.production")

    # Проверяем права на директорию сессий
    session_dir = '/tmp/flask_sessions'
    if not os.path.exists(session_dir):
        print(f"📁 Создаем директорию сессий: {session_dir}")
        os.makedirs(session_dir, exist_ok=True)
        os.chmod(session_dir, 0o777)
        print("✅ Директория создана")
    else:
        print(f"✅ Директория сессий существует: {session_dir}")
        # Проверяем права
        stat_info = os.stat(session_dir)
        permissions = oct(stat_info.st_mode)[-3:]
        print(f"🔒 Права доступа: {permissions}")
        if permissions != '777':
            os.chmod(session_dir, 0o777)
            print("✅ Права доступа изменены на 777")

    # Теперь проверим, что Flask загрузит правильные настройки
    print("\n🧪 Тестирование загрузки конфигурации...")

    # Устанавливаем переменные окружения явно
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SECRET_KEY'] = 'production-secret-key-change-this-in-real-deployment-2024'
    os.environ['DEBUG'] = 'False'
    os.environ['WTF_CSRF_ENABLED'] = 'True'
    os.environ['SESSION_TYPE'] = 'filesystem'
    os.environ['SESSION_FILE_DIR'] = '/tmp/flask_sessions'
    os.environ['SESSION_COOKIE_SECURE'] = 'True'
    os.environ['SESSION_COOKIE_HTTPONLY'] = 'True'
    os.environ['SESSION_COOKIE_SAMESITE'] = 'Lax'
    os.environ['SESSION_COOKIE_DOMAIN'] = 'its.tez-tour.com'

    # Загружаем .env.production если он есть
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ Загружен .env.production")

    # Создаем приложение и проверяем конфигурацию
    from blog import create_app
    app = create_app()

    print("\n🔍 Конфигурация приложения после исправлений:")
    print(f"DEBUG: {app.debug}")
    print(f"WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")
    print(f"SECRET_KEY установлен: {'да' if app.secret_key else 'нет'}")
    print(f"SESSION_TYPE: {app.config.get('SESSION_TYPE')}")
    print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
    print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
    print(f"SESSION_COOKIE_DOMAIN: {app.config.get('SESSION_COOKIE_DOMAIN')}")
    print(f"SESSION_FILE_DIR: {app.config.get('SESSION_FILE_DIR')}")

    # Тестируем CSRF
    print("\n🧪 Тестирование CSRF...")
    client = app.test_client()

    with app.app_context():
        # Получаем страницу входа
        response = client.get('/login')
        if response.status_code == 200:
            print("✅ Страница входа загружена")

            # Проверяем наличие CSRF токена в форме
            if b'csrf_token' in response.data:
                print("✅ CSRF токен найден в форме")

                # Извлекаем CSRF токен
                import re
                csrf_match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
                if csrf_match:
                    csrf_token = csrf_match.group(1).decode('utf-8')
                    print(f"🔍 CSRF токен: {csrf_token[:20]}...")

                    # Отправляем форму с CSRF токеном
                    response = client.post('/login', data={
                        'csrf_token': csrf_token,
                        'username': 'test',
                        'password': 'test'
                    })

                    print(f"🔍 Статус POST с CSRF: {response.status_code}")
                    if response.status_code != 400 or b'csrf' not in response.data.lower():
                        print("✅ CSRF токен принят!")
                    else:
                        print("❌ CSRF токен отклонен")
                else:
                    print("❌ Не удалось извлечь CSRF токен")
            else:
                print("❌ CSRF токен не найден в форме")
        else:
            print(f"❌ Ошибка загрузки страницы: {response.status_code}")

    print("\n🎉 Исправление CSRF завершено!")
    print("\n📋 Следующие шаги:")
    print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
    print("2. Проверьте работу сайта: https://its.tez-tour.com/login")

    # Создаем скрипт для systemd окружения
    systemd_env = BASE_DIR / 'flask-helpdesk.env'
    with open(systemd_env, 'w') as f:
        f.write(f"""FLASK_ENV=production
SECRET_KEY={os.environ.get('SECRET_KEY', 'production-secret-key-change-this-in-real-deployment-2024')}
DEBUG=False
WTF_CSRF_ENABLED=True
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_DOMAIN=its.tez-tour.com
PERMANENT_SESSION_LIFETIME=86400
""")
    print(f"3. Создан файл {systemd_env} для systemd")
    print("4. Возможно потребуется обновить сервис systemd для использования этого файла")

except Exception as e:
    print(f"\n❌ Ошибка при исправлении CSRF: {e}")
    import traceback
    traceback.print_exc()
