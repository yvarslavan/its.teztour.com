#!/usr/bin/env python3
"""
Исправление ошибки app.config в роуте login
"""

import os
from pathlib import Path

print("🔧 Исправление ошибки app.config...")

# Путь к файлу роутов
routes_path = Path('blog/user/routes.py')

if routes_path.exists():
    # Читаем текущий файл
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = routes_path.with_suffix('.py.backup2')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Заменяем app.config на current_app.config
    if 'app.config.get(\'WTF_CSRF_ENABLED\')' in content:
        # Проверяем, импортирован ли current_app
        if 'from flask import current_app' not in content:
            # Добавляем current_app в импорты
            imports_start = content.find('from flask import')
            if imports_start > 0:
                imports_end = content.find('\n', imports_start)
                modified_imports = content[:imports_end] + ', current_app' + content[imports_end:]
                content = modified_imports
                print("✅ Добавлен current_app в импорты")

        # Заменяем app.config на current_app.config
        new_content = content.replace(
            'app.config.get(\'WTF_CSRF_ENABLED\')',
            'current_app.config.get(\'WTF_CSRF_ENABLED\')'
        )

        # Записываем изменения
        with open(routes_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Исправлена ошибка app.config на current_app.config")
    else:
        print("⚠️ Ошибка app.config не найдена в файле")

        # Проверяем наличие current_app
        if 'current_app.config.get(\'WTF_CSRF_ENABLED\')' in content:
            print("✅ current_app.config уже используется")
        else:
            print("❌ Не найдено ни app.config ни current_app.config")
else:
    print(f"❌ Файл роутов не найден: {routes_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
