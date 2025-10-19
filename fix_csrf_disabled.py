#!/usr/bin/env python3
"""
Исправление отключенного CSRF в продакшене
"""

import os
from pathlib import Path

print("🔧 Исправление отключенного CSRF в продакшене...")

# Проверяем .env.production
env_file = Path('.env.production')
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()

    print("✅ Найден .env.production")

    # Проверяем WTF_CSRF_ENABLED
    if 'WTF_CSRF_ENABLED=True' in content:
        print("✅ WTF_CSRF_ENABLED=True в .env.production")
    else:
        print("❌ WTF_CSRF_ENABLED не равно True в .env.production")

        # Исправляем
        if 'WTF_CSRF_ENABLED=' in content:
            new_content = content.replace(
                'WTF_CSRF_ENABLED=False',
                'WTF_CSRF_ENABLED=True'
            )
        else:
            # Добавляем WTF_CSRF_ENABLED=True
            new_content = content.replace(
                'SESSION_TYPE=filesystem',
                'WTF_CSRF_ENABLED=True\nSESSION_TYPE=filesystem'
            )

        with open(env_file, 'w') as f:
            f.write(new_content)

        print("✅ Исправлен WTF_CSRF_ENABLED=True в .env.production")

    # Проверяем SECRET_KEY
    if 'SECRET_KEY=' in content:
        print("✅ SECRET_KEY найден в .env.production")
    else:
        print("❌ SECRET_KEY не найден в .env.production")

        # Добавляем SECRET_KEY
        new_content = content.replace(
            'FLASK_ENV=production',
            'FLASK_ENV=production\nSECRET_KEY=production-secret-key-change-this-in-real-deployment-2024'
        )

        with open(env_file, 'w') as f:
            f.write(new_content)

        print("✅ Добавлен SECRET_KEY в .env.production")
else:
    print("❌ .env.production не найден")

# Проверяем blog/__init__.py
init_file = Path('blog/__init__.py')
if init_file.exists():
    with open(init_file, 'r') as f:
        init_content = f.read()

    # Проверяем, есть ли код, который отключает CSRF
    if 'CSRF temporarily disabled' in init_content:
        print("❌ Найден код, отключающий CSRF в blog/__init__.py")

        # Находим и исправляем код, который отключает CSRF
        if 'if not app.debug:' in init_content and 'WTF_CSRF_ENABLED = False' in init_content:
            # Заменяем условие, чтобы CSRF был включен в продакшене
            new_init_content = init_content.replace(
                'if not app.debug:\n        WTF_CSRF_ENABLED = False',
                'if not app.debug:\n        WTF_CSRF_ENABLED = True'
            )

            with open(init_file, 'w') as f:
                f.write(new_init_content)

            print("✅ Исправлен код, включающий CSRF в продакшене")
        else:
            print("❌ Не удалось найти код для исправления")
    else:
        print("✅ Код, отключающий CSRF, не найден")
else:
    print(f"❌ blog/__init__.py не найден")

# Создаем скрипт для проверки переменных окружения
check_script = Path('check_env.py')
with open(check_script, 'w') as f:
    f.write('''#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Загружаем .env.production
load_dotenv('.env.production')

print("Проверка переменных окружения:")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'не установлена')}")
print(f"WTF_CSRF_ENABLED: {os.environ.get('WTF_CSRF_ENABLED', 'не установлена')}")
print(f"SECRET_KEY: {'установлен' if os.environ.get('SECRET_KEY') else 'не установлен'}")
print(f"SESSION_TYPE: {os.environ.get('SESSION_TYPE', 'не установлена')}")
''')

print(f"✅ Создан скрипт проверки: {check_script}")

print("\n📋 Следующие шаги:")
print("1. Проверьте переменные окружения: python3 check_env.py")
print("2. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("3. Проверьте работу: python3 debug_csrf_server.py")
