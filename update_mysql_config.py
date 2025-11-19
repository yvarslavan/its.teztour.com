#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для обновления настроек MySQL в .env файле"""

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

# Новые настройки MySQL для Easy Redmine
mysql_config = {
    'MYSQL_HOST': '10.0.0.172',  # IP адрес сервера MySQL
    'MYSQL_DATABASE': 'redmine',  # Имя базы данных
    'MYSQL_USER': 'easyredmine',
    'MYSQL_PASSWORD': 'QhAKtwCLGW'
}

print("🔧 Обновление настроек MySQL в .env...")
print()

# Обновляем каждую переменную
updated = []
for key, value in mysql_config.items():
    # Ищем существующую строку с этой переменной
    pattern = rf'^{key}=.*$'
    replacement = f'{key}={value}'
    
    if re.search(pattern, content, re.MULTILINE):
        # Заменяем существующую строку
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        updated.append(key)
        print(f"✅ Обновлено: {key}={value}")
    else:
        # Добавляем новую строку после секции MySQL (если есть комментарий)
        mysql_section = re.search(r'# MySQL.*?Database Configuration', content, re.IGNORECASE | re.DOTALL)
        if mysql_section:
            # Вставляем после комментария
            insert_pos = mysql_section.end()
            # Находим конец блока MySQL настроек
            next_section = re.search(r'^# [A-Z]', content[insert_pos:], re.MULTILINE)
            if next_section:
                insert_pos = insert_pos + next_section.start()
            
            new_line = f'{key}={value}\n'
            content = content[:insert_pos] + new_line + content[insert_pos:]
            updated.append(key)
            print(f"✅ Добавлено: {key}={value}")
        else:
            # Добавляем в конец файла
            content += f'\n{key}={value}\n'
            updated.append(key)
            print(f"✅ Добавлено в конец: {key}={value}")

# Сохраняем обновленный файл
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("=" * 60)
print("✅ Настройки MySQL обновлены!")
print("=" * 60)
print()
print("📋 Обновленные переменные:")
for key in updated:
    print(f"   {key}")
print()
print("⚠️  ВАЖНО:")
print("   1. База данных: redmine")
print("   2. Убедитесь, что IP 10.0.0.172 доступен с вашей машины")
print("      Если нет - используйте SSH туннель или VPN (см. LOCAL_DEVELOPMENT_SETUP.md)")
print("   3. Если нужны настройки MYSQL_QUALITY_* - добавьте их отдельно")
print()
print("🚀 Теперь можно запустить приложение:")
print("   python3 app.py")

