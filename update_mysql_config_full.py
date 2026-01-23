#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для обновления ВСЕХ настроек MySQL в .env файле"""

import re
from pathlib import Path

env_file = Path('.env')

if not env_file.exists():
    print("❌ Файл .env не найден!")
    print("💡 Создайте файл .env на основе env.template")
    exit(1)

# Читаем текущий .env
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Настройки MySQL для Easy Redmine (основная база)
# Используем 127.0.0.1 через порт-прокси Windows
mysql_config = {
    'MYSQL_HOST': '127.0.0.1',
    'MYSQL_DATABASE': 'redmine',
    'MYSQL_USER': 'easyredmine',
    'MYSQL_PASSWORD': 'QhAKtwCLGW'
}

# Настройки MySQL Quality (через порт-прокси на порт 3307)
# Формат host:port поддерживается SQLAlchemy
mysql_quality_config = {
    'MYSQL_QUALITY_HOST': '127.0.0.1:3307',  # Порт 3307 проброшен на quality.teztour.com
    'MYSQL_QUALITY_DATABASE': 'redmine',
    'MYSQL_QUALITY_USER': 'easyredmine',
    'MYSQL_QUALITY_PASSWORD': 'QhAKtwCLGW'
}

print("🔧 Обновление настроек MySQL в .env...")
print()
print("📋 Основная база Redmine:")
for key, value in mysql_config.items():
    masked_value = '***' if 'PASSWORD' in key else value
    print(f"   {key}={masked_value}")

print()
print("📋 База Quality:")
for key, value in mysql_quality_config.items():
    masked_value = '***' if 'PASSWORD' in key else value
    print(f"   {key}={masked_value}")

print()
print("=" * 60)

# Объединяем все настройки
all_config = {**mysql_config, **mysql_quality_config}

# Обновляем каждую переменную
updated = []
added = []

for key, value in all_config.items():
    # Ищем существующую строку с этой переменной
    pattern = rf'^{key}=.*$'
    replacement = f'{key}={value}'
    
    if re.search(pattern, content, re.MULTILINE):
        # Заменяем существующую строку
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        updated.append(key)
    else:
        # Добавляем новую строку
        # Если это переменная MYSQL_QUALITY_*, добавляем в секцию Quality
        if 'QUALITY' in key:
            # Ищем секцию MySQL Quality
            quality_section = re.search(r'# MySQL Quality.*?Configuration', content, re.IGNORECASE | re.DOTALL)
            if quality_section:
                insert_pos = quality_section.end()
                content = content[:insert_pos] + f'\n{key}={value}' + content[insert_pos:]
            else:
                # Создаем секцию Quality если её нет
                mysql_section_end = re.search(r'^MYSQL_PASSWORD=.*$', content, re.MULTILINE)
                if mysql_section_end:
                    insert_pos = mysql_section_end.end()
                    quality_header = '\n\n# MySQL Quality Database Configuration (ОБЯЗАТЕЛЬНО)\n'
                    content = content[:insert_pos] + quality_header + f'{key}={value}' + content[insert_pos:]
                else:
                    content += f'\n{key}={value}\n'
        else:
            # Для обычных MYSQL_* переменных
            mysql_section = re.search(r'# MySQL.*?Database Configuration', content, re.IGNORECASE | re.DOTALL)
            if mysql_section:
                insert_pos = mysql_section.end()
                content = content[:insert_pos] + f'\n{key}={value}' + content[insert_pos:]
            else:
                content += f'\n{key}={value}\n'
        
        added.append(key)

# Сохраняем обновленный файл
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Настройки MySQL обновлены!")
print("=" * 60)
print()

if updated:
    print("📝 Обновленные переменные:")
    for key in updated:
        print(f"   ✓ {key}")
    print()

if added:
    print("➕ Добавленные переменные:")
    for key in added:
        print(f"   + {key}")
    print()

print("⚠️  ВАЖНО:")
print("   1. Обе базы используют одинаковые данные подключения")
print("   2. Если база Quality отдельная - обновите MYSQL_QUALITY_* вручную")
print("   3. Убедитесь, что helpdesk.teztour.com:3306 доступен с вашей машины")
print("      Если нет - используйте SSH туннель или VPN")
print()
print("🚀 Проверьте подключение:")
print("   python3 test_mysql_connection.py")
print()
print("🚀 Запустите приложение:")
print("   python3 app.py")

