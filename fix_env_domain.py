#!/usr/bin/env python3
"""
Скрипт для исправления домена в .env.production файле
"""

import os
import re

# Путь к файлу .env.production
env_file = '.env.production'

print("🔧 Исправление домена в .env.production...")

try:
    # Читаем текущий файл
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()

        print(f"📄 Текущий SESSION_COOKIE_DOMAIN: {re.search(r'SESSION_COOKIE_DOMAIN=(.*)', content).group(1) if re.search(r'SESSION_COOKIE_DOMAIN=(.*)', content) else 'не найден'}")

        # Заменяем домен
        new_content = re.sub(
            r'SESSION_COOKIE_DOMAIN=.*',
            'SESSION_COOKIE_DOMAIN=its.tez-tour.com',
            content
        )

        # Записываем изменения
        with open(env_file, 'w') as f:
            f.write(new_content)

        print("✅ SESSION_COOKIE_DOMAIN изменен на its.tez-tour.com")

        # Также проверяем, нужно ли добавить PERMANENT_SESSION_LIFETIME
        if 'PERMANENT_SESSION_LIFETIME=' not in new_content:
            with open(env_file, 'a') as f:
                f.write('\nPERMANENT_SESSION_LIFETIME=86400\n')
            print("✅ Добавлен PERMANENT_SESSION_LIFETIME=86400")

    else:
        print(f"❌ Файл {env_file} не найден")

except Exception as e:
    print(f"❌ Ошибка при исправлении домена: {e}")
