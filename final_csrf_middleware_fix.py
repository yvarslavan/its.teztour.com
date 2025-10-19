#!/usr/bin/env python3
"""
Финальное исправление CSRF с использованием middleware
"""

import os
from pathlib import Path

print("🔧 Финальное исправление CSRF с middleware...")

# Путь к файлу роутов
routes_path = Path('blog/user/routes.py')

if routes_path.exists():
    # Читаем текущий файл
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = routes_path.with_suffix('.py.backup4')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Добавляем middleware для CSRF
    csrf_middleware = '''
@users.before_request
def set_csrf_token():
    """Устанавливает CSRF токен в сессию для GET запросов"""
    if request.method == "GET" and request.endpoint in ['users.login', 'users.register']:
        if current_app.config.get('WTF_CSRF_ENABLED'):
            with current_app.app_context():
                from flask_wtf.csrf import generate_csrf
                csrf_token = generate_csrf()
                session['csrf_token'] = csrf_token
                session.modified = True

'''

    # Находим место для добавления middleware (после определения @users.before_request если он есть)
    before_request_pos = content.find('@users.before_request')
    if before_request_pos > 0:
        # Если уже есть @users.before_request, находим конец функции
        func_start = content.find('def ', before_request_pos)
        if func_start > 0:
            # Находим следующую функцию или декоратор
            next_func = content.find('\ndef ', func_start + 1)
            if next_func == -1:
                next_func = content.find('\n@', func_start + 1)
            if next_func == -1:
                next_func = len(content)

            # Вставляем middleware после существующей функции
            new_content = content[:next_func] + '\n' + csrf_middleware + '\n' + content[next_func:]
        else:
            # Вставляем после @users.before_request
            new_content = content[:before_request_pos] + csrf_middleware + '\n' + content[before_request_pos:]
    else:
        # Если нет @users.before_request, находим место после определения users = Blueprint
        blueprint_pos = content.find('users = Blueprint("users", __name__)')
        if blueprint_pos > 0:
            # Находим конец строки
            line_end = content.find('\n', blueprint_pos)
            new_content = content[:line_end+1] + '\n' + csrf_middleware + '\n' + content[line_end+1:]
        else:
            # Вставляем в начало файла
            new_content = csrf_middleware + '\n' + content

    # Записываем изменения
    with open(routes_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Добавлен middleware для CSRF")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
