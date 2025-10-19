#!/usr/bin/env python3
"""
Анализ настроек .env.production
"""

import os
from pathlib import Path

print("🔍 Анализ настроек .env.production...")

# Проверяем наличие файла .env.production
env_file = Path('.env.production')
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()

    print("✅ Найден файл .env.production")
    print("\n📄 Содержимое файла:")
    print(content)

    # Анализируем настройки
    print("\n🔍 Анализ настроек:")

    # Проверяем основные настройки
    if 'FLASK_ENV=production' in content:
        print("✅ FLASK_ENV установлен в production")
    else:
        print("❌ FLASK_ENV не установлен в production")

    if 'SECRET_KEY=' in content:
        print("✅ SECRET_KEY установлен")
    else:
        print("❌ SECRET_KEY не установлен")

    if 'WTF_CSRF_ENABLED=True' in content:
        print("✅ WTF_CSRF_ENABLED включен")
    else:
        print("❌ WTF_CSRF_ENABLED не включен")

    if 'SESSION_TYPE=filesystem' in content:
        print("✅ SESSION_TYPE установлен в filesystem")
    else:
        print("❌ SESSION_TYPE не установлен в filesystem")

    if 'SESSION_FILE_DIR=' in content:
        print("✅ SESSION_FILE_DIR установлен")
        # Извлекаем путь
        for line in content.split('\n'):
            if line.startswith('SESSION_FILE_DIR='):
                session_dir = line.split('=', 1)[1]
                print(f"   Путь: {session_dir}")

                # Проверяем существование директории
                if os.path.exists(session_dir):
                    print(f"   ✅ Директория существует")
                    # Проверяем права
                    stat_info = os.stat(session_dir)
                    permissions = oct(stat_info.st_mode)[-3:]
                    print(f"   🔒 Права доступа: {permissions}")
                else:
                    print(f"   ❌ Директория не существует")
    else:
        print("❌ SESSION_FILE_DIR не установлен")

    # Проверяем настройки cookies
    if 'SESSION_COOKIE_SECURE=True' in content:
        print("✅ SESSION_COOKIE_SECURE включен")
    else:
        print("❌ SESSION_COOKIE_SECURE не включен")

    if 'SESSION_COOKIE_SAMESITE=Lax' in content:
        print("✅ SESSION_COOKIE_SAMESITE установлен в Lax")
    else:
        print("❌ SESSION_COOKIE_SAMESITE не установлен")

    if 'SESSION_COOKIE_DOMAIN=' in content:
        print("✅ SESSION_COOKIE_DOMAIN установлен")
        # Извлекаем домен
        for line in content.split('\n'):
            if line.startswith('SESSION_COOKIE_DOMAIN='):
                domain = line.split('=', 1)[1]
                print(f"   Домен: {domain}")

                # Проверяем соответствие с текущим сайтом
                if 'its.tez-tour.com' in domain:
                    print("   ✅ Домен соответствует сайту")
                else:
                    print("   ❌ Домен не соответствует сайту")
    else:
        print("❌ SESSION_COOKIE_DOMAIN не установлен")

    # Проверяем наличие PERMANENT_SESSION_LIFETIME
    if 'PERMANENT_SESSION_LIFETIME=' in content:
        print("✅ PERMANENT_SESSION_LIFETIME установлен")
    else:
        print("⚠️ PERMANENT_SESSION_LIFETIME не установлен (рекомендуется)")

    # Сравниваем с настройками для разработки
    dev_file = Path('.env.development')
    if dev_file.exists():
        print("\n🔍 Сравнение с .env.development:")
        with open(dev_file, 'r') as f:
            dev_content = f.read()

        # Проверяем наличие важных настроек в dev
        if 'FLASK_ENV=development' in dev_content:
            print("✅ FLASK_ENV=development в .env.development")

        if 'WTF_CSRF_ENABLED=' in dev_content:
            for line in dev_content.split('\n'):
                if line.startswith('WTF_CSRF_ENABLED='):
                    dev_csrf = line.split('=', 1)[1]
                    print(f"🔍 WTF_CSRF_ENABLED в разработке: {dev_csrf}")
                    if dev_csrf == 'False':
                        print("⚠️ CSRF отключен в разработке, но включен в продакшене")
                    else:
                        print("✅ CSRF включен в разработке и продакшене")

        # Проверяем наличие SECRET_KEY в dev
        if 'SECRET_KEY=' in dev_content:
            print("✅ SECRET_KEY есть в .env.development")
        else:
            print("❌ SECRET_KEY отсутствует в .env.development")

    print("\n💡 Рекомендации:")
    print("1. Убедитесь, что SESSION_FILE_DIR существует и имеет права 777")
    print("2. Проверьте, что systemd сервис загружает .env.production")
    print("3. Убедитесь, что SECRET_KEY одинаковый в разработке и продакшене")
    print("4. Проверьте, что домен в SESSION_COOKIE_DOMAIN соответствует сайту")

else:
    print("❌ Файл .env.production не найден")
