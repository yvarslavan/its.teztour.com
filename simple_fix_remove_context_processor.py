#!/usr/bin/env python3
"""
Простое исправление - удаляем контекстный процессор и используем только middleware
"""

import os
import shutil
from pathlib import Path

print("🔧 Простое исправление - удаляем контекстный процессор...")

# Путь к файлу __init__.py
init_path = Path('blog/__init__.py')
backup_path = init_path.with_suffix('.py.backup')

if backup_path.exists():
    # Восстанавливаем из резервной копии
    shutil.copy(backup_path, init_path)
    print(f"✅ Восстановлен из резервной копии: {backup_path}")

    # Читаем текущий файл
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем новую резервную копию
    backup2_path = init_path.with_suffix('.py.backup4')
    with open(backup2_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup2_path}")

    # Удаляем контекстный процессор
    if '@app.context_processor' in content:
        # Находим начало и конец контекстного процессора
        cp_start = content.find('@app.context_processor')
        cp_end = content.find('\n@', cp_start + 1)
        if cp_end == -1:
            cp_end = content.find('\n\n', cp_start + 1)
        if cp_end == -1:
            cp_end = len(content)

        # Удаляем контекстный процессор
        new_content = content[:cp_start] + content[cp_end:]

        # Записываем изменения
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Удален контекстный процессор")
        print("💡 CSRF будет работать через middleware в routes.py")
    else:
        print("✅ Контекстный процессор не найден")

        # Проверяем наличие inject_csrf_functions
        if 'def inject_csrf_functions():' in content:
            # Находим начало и конец функции
            func_start = content.find('def inject_csrf_functions():')
            func_end = content.find('\n@', func_start + 1)
            if func_end == -1:
                func_end = content.find('\n\n', func_start + 1)
            if func_end == -1:
                func_end = len(content)

            # Удаляем функцию
            new_content = content[:func_start] + content[func_end:]

            # Записываем изменения
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print("✅ Удалена функция inject_csrf_functions")
else:
    print(f"❌ Резервная копия не найдена: {backup_path}")

    # Читаем текущий файл
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = init_path.with_suffix('.py.backup5')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Удаляем контекстный процессор
    if '@app.context_processor' in content:
        # Находим начало и конец контекстного процессора
        cp_start = content.find('@app.context_processor')
        cp_end = content.find('\n@', cp_start + 1)
        if cp_end == -1:
            cp_end = content.find('\n\n', cp_start + 1)
        if cp_end == -1:
            cp_end = len(content)

        # Удаляем контекстный процессор
        new_content = content[:cp_start] + content[cp_end:]

        # Записываем изменения
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Удален контекстный процессор")
    else:
        print("❌ Контекстный процессор не найден")

# Теперь проверяем routes.py и добавляем middleware, если нужно
routes_path = Path('blog/user/routes.py')
if routes_path.exists():
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()

    # Проверяем наличие middleware
    if 'def set_csrf_token():' not in routes_content:
        print("🔧 Добавляем middleware в routes.py...")

        # Находим место для добавления middleware
        blueprint_pos = routes_content.find('users = Blueprint("users", __name__)')
        if blueprint_pos > 0:
            # Находим конец строки
            line_end = routes_content.find('\n', blueprint_pos)

            # Создаем middleware
            middleware = '''

@users.before_request
def set_csrf_token():
    """Устанавливает CSRF токен в сессию для GET запросов"""
    if request.method == "GET" and request.endpoint in ['users.login', 'users.register']:
        if current_app.config.get('WTF_CSRF_ENABLED'):
            try:
                from flask_wtf.csrf import generate_csrf
                with current_app.app_context():
                    csrf_token = generate_csrf()
                    session['csrf_token'] = csrf_token
                    session.modified = True
            except Exception as e:
                current_app.logger.error(f"Error setting CSRF token: {e}")
'''

            # Вставляем middleware
            new_routes_content = routes_content[:line_end+1] + middleware + routes_content[line_end+1:]

            # Записываем изменения
            with open(routes_path, 'w', encoding='utf-8') as f:
                f.write(new_routes_content)

            print("✅ Добавлен middleware в routes.py")
        else:
            print("❌ Не найдено место для добавления middleware в routes.py")
    else:
        print("✅ Middleware уже есть в routes.py")
else:
    print(f"❌ Файл routes.py не найден: {routes_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
