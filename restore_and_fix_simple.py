#!/usr/bin/env python3
"""
Простое восстановление и исправление CSRF
"""

import os
import shutil
from pathlib import Path

print("🔧 Простое восстановление и исправление CSRF...")

# Путь к файлу роутов
routes_path = Path('blog/user/routes.py')
backup_path = routes_path.with_suffix('.py.backup')

if backup_path.exists():
    # Восстанавливаем из резервной копии
    shutil.copy(backup_path, routes_path)
    print(f"✅ Восстановлен из резервной копии: {backup_path}")

    # Теперь просто добавляем current_app в импорты
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем, есть ли уже current_app в импортах
    if 'current_app' not in content:
        # Находим строку с импортами flask
        import_line = 'from flask import'
        if import_line in content:
            # Находим конец строки импортов
            start_pos = content.find(import_line)
            end_pos = content.find('\n', start_pos)

            if end_pos > start_pos:
                # Добавляем current_app в импорты
                modified_import = content[:end_pos] + ', current_app' + content[end_pos:]

                # Записываем изменения
                with open(routes_path, 'w', encoding='utf-8') as f:
                    f.write(modified_import)

                print("✅ Добавлен current_app в импорты")
            else:
                print("❌ Не найден конец строки импортов")
        else:
            print("❌ Не найдены импорты flask")
    else:
        print("✅ current_app уже есть в импортах")

    # Теперь заменяем app.config на current_app.config только в функции login
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Находим функцию login
    login_start = content.find('def login():')
    if login_start > 0:
        # Находим конец функции
        next_func = content.find('\n@', login_start + 1)
        if next_func == -1:
            next_func = len(content)

        # Извлекаем функцию
        login_func = content[login_start:next_func]

        # Заменяем только в этой функции
        modified_login = login_func.replace('app.config', 'current_app.config')

        # Заменяем в общем содержимом
        new_content = content[:login_start] + modified_login + content[next_func:]

        # Записываем изменения
        with open(routes_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Заменено app.config на current_app.config в функции login")
    else:
        print("❌ Функция login не найдена")

    print("\n📋 Следующие шаги:")
    print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
    print("2. Проверьте работу: python3 debug_csrf_server.py")

else:
    print(f"❌ Резервная копия не найдена: {backup_path}")
    print("Попробуйте восстановить из другой резервной копии или вручную исправьте файл")
