#!/usr/bin/env python3
"""
Исправление синтаксической ошибки в routes.py
"""

import os
from pathlib import Path

print("🔧 Исправление синтаксической ошибки...")

# Путь к файлу роутов
routes_path = Path('blog/user/routes.py')

if routes_path.exists():
    # Читаем текущий файл
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = routes_path.with_suffix('.py.backup3')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Исправляем синтаксическую ошибку в импортах
    if 'from flask import (, current_app' in content:
        # Находим строку с импортами
        import_start = content.find('from flask import (')
        if import_start > 0:
            # Находим конец строки с импортами
            import_end = content.find(')', import_start)
            if import_end > 0:
                # Извлекаем текущие импорты
                imports_line = content[import_start:import_end+1]
                print(f"🔍 Текущая строка импортов: {imports_line}")

                # Исправляем строку
                fixed_imports = 'from flask import ('
                # Добавляем все импорты кроме последней запятой
                imports = imports_line.replace('from flask import (', '').replace(')', '').strip().split(',')
                for i, imp in enumerate(imports):
                    imp = imp.strip()
                    if imp and imp != 'current_app':  # Пропускаем current_app, он уже есть в списке
                        fixed_imports += imp
                        if i < len(imports) - 1:
                            fixed_imports += ',\n    '

                fixed_imports += ')'

                # Заменяем строку импортов
                new_content = content.replace(imports_line, fixed_imports)

                # Записываем изменения
                with open(routes_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print("✅ Исправлена синтаксическая ошибка в импортах")
            else:
                print("❌ Не найден конец строки импортов")
        else:
            print("❌ Не найдено начало строки импортов")
    else:
        print("⚠️ Синтаксическая ошибка не найдена")

        # Проверяем наличие других проблем
        if 'from flask import' in content and 'current_app' in content:
            print("✅ current_app уже есть в импортах")
        else:
            print("❌ Не найдены импорты flask или current_app")
else:
    print(f"❌ Файл роутов не найден: {routes_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
