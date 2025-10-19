#!/usr/bin/env python3
"""
Финальное исправление проблемы CSRF - добавляем токен в сессию
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🔧 Финальное исправление CSRF...")

try:
    # Читаем текущий файл роутов
    routes_path = BASE_DIR / 'blog' / 'user' / 'routes.py'

    if routes_path.exists():
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Создаем резервную копию
        backup_path = routes_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Создана резервная копия: {backup_path}")

        # Добавляем обработку CSRF токена в сессию
        if '@users.route("/login", methods=["GET", "POST"])' in content:
            # Находим функцию login
            login_func_start = content.find('def login():')
            if login_func_start > 0:
                # Находим конец функции (следующая функция или конец файла)
                next_func = content.find('\n@', login_func_start + 1)
                if next_func == -1:
                    next_func = len(content)

                # Извлекаем функцию
                login_func = content[login_func_start:next_func]

                # Добавляем обработку CSRF токена в GET запросе
                if 'def login():' in login_func and 'response = client.get' not in login_func:
                    # Добавляем установку CSRF токена в сессию для GET запросов
                    modified_func = login_func.replace(
                        '    form = LoginForm()\n    # print(f"Generated CSRF token: {generate_csrf()}")  # CSRF отключен',
                        '''    form = LoginForm()

    # Устанавливаем CSRF токен в сессию для GET запросов
    if request.method == "GET" and app.config.get('WTF_CSRF_ENABLED'):
        from flask_wtf.csrf import generate_csrf
        with app.app_context():
            csrf_token = generate_csrf()
            session['csrf_token'] = csrf_token
            session.modified = True'''
                    )

                    # Заменяем функцию в содержимом
                    new_content = content[:login_func_start] + modified_func + content[next_func:]

                    # Записываем изменения
                    with open(routes_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    print("✅ Добавлена обработка CSRF токена в сессию для GET запросов")
                else:
                    print("⚠️ Функция login уже содержит обработку CSRF или имеет другую структуру")
            else:
                print("❌ Функция login не найдена")
        else:
            print("❌ Роут login не найден")
    else:
        print(f"❌ Файл роутов не найден: {routes_path}")

    # Также создаем альтернативный подход - middleware
    print("\n🔄 Создаем middleware для CSRF...")

    middleware_path = BASE_DIR / 'blog' / 'csrf_middleware.py'
    middleware_content = '''"""
Middleware для обработки CSRF токенов
"""

from flask import request, session, g
from flask_wtf.csrf import generate_csrf


@users.before_request
def set_csrf_token():
    """Устанавливает CSRF токен в сессию для GET запросов"""
    if request.method == "GET" and request.endpoint in ['users.login', 'users.register']:
        from flask import current_app
        if current_app.config.get('WTF_CSRF_ENABLED'):
            with current_app.app_context():
                csrf_token = generate_csrf()
                session['csrf_token'] = csrf_token
                session.modified = True
'''

    with open(middleware_path, 'w', encoding='utf-8') as f:
        f.write(middleware_content)

    print(f"✅ Создан файл middleware: {middleware_path}")

    # Интегрируем middleware в __init__.py
    init_path = BASE_DIR / 'blog' / '__init__.py'
    if init_path.exists():
        with open(init_path, 'r', encoding='utf-8') as f:
            init_content = f.read()

        # Добавляем импорт middleware после существующих импортов
        if 'from blog.csrf_middleware import set_csrf_token' not in init_content:
            # Находим место для добавления импорта
            import_end = init_content.find('from blog.settings import Config')
            if import_end > 0:
                # Находим конец строки
                line_end = init_content.find('\n', import_end)
                modified_init = init_content[:line_end+1] + 'from blog.csrf_middleware import set_csrf_token\n' + init_content[line_end+1:]

                # Записываем изменения
                with open(init_path, 'w', encoding='utf-8') as f:
                    f.write(modified_init)

                print("✅ Middleware добавлен в __init__.py")
            else:
                print("⚠️ Не удалось найти место для добавления импорта middleware")
        else:
            print("⚠️ Middleware уже импортирован в __init__.py")

    print("\n📋 Следующие шаги:")
    print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
    print("2. Проверьте работу: python3 debug_csrf_server.py")

except Exception as e:
    print(f"\n❌ Ошибка при финальном исправлении CSRF: {e}")
    import traceback
    traceback.print_exc()
