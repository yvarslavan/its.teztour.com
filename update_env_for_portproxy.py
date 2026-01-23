#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт для обновления .env для работы через порт-прокси Windows"""

import re
from pathlib import Path

env_file = Path('.env')

if not env_file.exists():
    print("❌ Файл .env не найден!")
    exit(1)

# Читаем текущий .env
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Настройки для работы через порт-прокси Windows
# helpdesk.teztour.com -> 127.0.0.1:3306
# quality.teztour.com -> 127.0.0.1:3307
config_updates = {
    'MYSQL_HOST': '127.0.0.1',
    'MYSQL_QUALITY_HOST': '127.0.0.1:3307',  # SQLAlchemy поддерживает host:port
}

print("🔧 Обновление .env для работы через порт-прокси Windows...")
print()
print("📋 Настройки:")
print("   MYSQL_HOST=127.0.0.1 (прокси на helpdesk.teztour.com:3306)")
print("   MYSQL_QUALITY_HOST=127.0.0.1:3307 (прокси на quality.teztour.com:3306)")
print()

updated = []
for key, value in config_updates.items():
    pattern = rf'^{key}=.*$'
    replacement = f'{key}={value}'
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        updated.append(key)
        print(f"✅ Обновлено: {key}={value}")
    else:
        # Добавляем если нет
        content += f'\n{key}={value}\n'
        updated.append(key)
        print(f"➕ Добавлено: {key}={value}")

# Сохраняем
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("=" * 60)
print("✅ .env обновлён для работы через порт-прокси!")
print("=" * 60)
print()
print("⚠️  Убедитесь, что:")
print("   1. Cisco Secure Client подключен в Windows")
print("   2. Порт-прокси настроен в PowerShell:")
print("      netsh interface portproxy show all")
print("   3. Проверьте подключение из WSL:")
print("      nc -vz 127.0.0.1 3306")
print("      nc -vz 127.0.0.1 3307")
print()
print("🚀 Теперь можно запустить приложение:")
print("   python3 app.py")

