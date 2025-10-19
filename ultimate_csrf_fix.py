#!/usr/bin/env python3
"""
Окончательное исправление проблемы CSRF
"""

import os
import subprocess
from pathlib import Path

print("🔧 Окончательное исправление проблемы CSRF...")

# 1. Сначала исправляем blog/__init__.py
init_file = Path('blog/__init__.py')
if init_file.exists():
    # Восстанавливаем из git
    result = subprocess.run(
        ["git", "checkout", "HEAD", "--", "blog/__init__.py"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )

    if result.returncode == 0:
        print("✅ Файл blog/__init__.py восстановлен через git")
    else:
        print(f"❌ Ошибка git: {result.stderr}")

    # Читаем файл
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Находим и исправляем код, который отключает CSRF
    if 'if not app.debug:' in content and 'WTF_CSRF_ENABLED = False' in content:
        # Заменяем на правильный код
        new_content = content.replace(
            'if not app.debug:\n        WTF_CSRF_ENABLED = False',
            'if not app.debug:\n        WTF_CSRF_ENABLED = True'
        )

        # Записываем изменения
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Исправлен код, включающий CSRF в продакшене")
    else:
        print("❌ Не найден код для исправления в blog/__init__.py")

    # Удаляем контекстный процессор, если он есть
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
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Удален контекстный процессор")

# 2. Исправляем шаблон
template_file = Path('blog/templates/login.html')
if template_file.exists():
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Заменяем form.hidden_tag() на явный CSRF токен
    if '{{ form.hidden_tag() }}' in template_content:
        new_template = template_content.replace(
            '                {{ form.hidden_tag() }}',
            '                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        )

        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(new_template)

        print("✅ Шаблон исправлен для CSRF")
    else:
        print("✅ Шаблон уже содержит CSRF токен")

# 3. Исправляем форму
form_file = Path('blog/user/forms.py')
if form_file.exists():
    with open(form_file, 'r', encoding='utf-8') as f:
        form_content = f.read()

    # Удаляем класс Meta с отключенным CSRF
    if 'class Meta:' in form_content and 'csrf = False' in form_content:
        lines = form_content.split('\n')
        new_lines = []
        skip_lines = False

        for line in lines:
            if 'class Meta:' in line:
                skip_lines = True
            elif skip_lines and line.strip() and not line.startswith('    '):
                skip_lines = False

            if not skip_lines:
                new_lines.append(line)

        new_form_content = '\n'.join(new_lines)

        with open(form_file, 'w', encoding='utf-8') as f:
            f.write(new_form_content)

        print("✅ Форма исправлена для CSRF")
    else:
        print("✅ Форма уже настроена для CSRF")

# 4. Добавляем middleware в routes.py
routes_file = Path('blog/user/routes.py')
if routes_file.exists():
    with open(routes_file, 'r', encoding='utf-8') as f:
        routes_content = f.read()

    # Проверяем наличие current_app в импортах
    if 'current_app' not in routes_content:
        # Добавляем current_app в импорты
        import_line = 'from flask import'
        if import_line in routes_content:
            start_pos = routes_content.find(import_line)
            end_pos = routes_content.find('\n', start_pos)

            if end_pos > start_pos:
                modified_import = routes_content[:end_pos] + ', current_app' + routes_content[end_pos:]
                routes_content = modified_import
                print("✅ Добавлен current_app в импорты")

    # Добавляем middleware, если его нет
    if 'def set_csrf_token():' not in routes_content:
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
        if current_app.config.get('WTF_CSRF_ENABLED', True):
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
            with open(routes_file, 'w', encoding='utf-8') as f:
                f.write(new_routes_content)

            print("✅ Middleware добавлен в routes")
        else:
            print("❌ Не найдено место для добавления middleware")
    else:
        print("✅ Middleware уже есть в routes")

# 5. Создаем правильный .env.production
env_file = Path('.env.production')
with open(env_file, 'w') as f:
    f.write("""# =============================================================================
# ОСНОВНЫЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ (ПРОДАКШЕН)
# =============================================================================
FLASK_ENV=production
SECRET_KEY=production-secret-key-change-this-in-real-deployment-2024
FLASK_DEBUG=False

# =============================================================================
# НАСТРОЙКИ CSRF И СЕССИЙ
# =============================================================================
WTF_CSRF_ENABLED=True
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400

# =============================================================================
# НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА
# =============================================================================
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_DOMAIN=its.tez-tour.com
""")

print("✅ Создан правильный .env.production")

# 6. Создаем директорию для сессий
session_dir = Path('/tmp/flask_sessions')
if not session_dir.exists():
    os.makedirs(session_dir, exist_ok=True)
    os.chmod(session_dir, 0o777)
    print("✅ Создана директория для сессий")
else:
    os.chmod(session_dir, 0o777)
    print("✅ Установлены права для директории сессий")

# 7. Создаем файл для systemd
systemd_env = Path('flask-helpdesk.env')
with open(systemd_env, 'w') as f:
    f.write("""FLASK_ENV=production
SECRET_KEY=production-secret-key-change-this-in-real-deployment-2024
FLASK_DEBUG=False
WTF_CSRF_ENABLED=True
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_DOMAIN=its.tez-tour.com
""")

print(f"✅ Создан файл для systemd: {systemd_env}")

print("\n📋 Следующие шаги:")
print("1. Обновите systemd сервис:")
print("   sudo nano /etc/systemd/system/flask-helpdesk.service")
print("   Добавьте строку: EnvironmentFile=/opt/www/its.teztour.com/flask-helpdesk.env")
print("2. Перезагрузите systemd: sudo systemctl daemon-reload")
print("3. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("4. Проверьте работу: python3 debug_csrf_server.py")
