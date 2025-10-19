#!/usr/bin/env python3
"""
Финальное простое решение - копируем рабочий файл
"""

import os
import subprocess
from pathlib import Path

print("🔧 Финальное простое решение...")

# Попробуем использовать git для восстановления файла
try:
    print("🔄 Попытка восстановления файла через git...")
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
        raise Exception("Git failed")

except Exception as e:
    print(f"⚠️ Не удалось использовать git: {e}")

    # Если git не сработал, создаем минимальный рабочий файл
    print("🔧 Создание минимального рабочего файла...")

    init_path = Path('blog/__init__.py')

    # Создаем базовый рабочий файл
    basic_content = '''import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения
basedir = Path(__file__).resolve().parent
load_dotenv(os.path.join(basedir, '.env.production'))

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

def create_app(config_class="config.Config"):
    app = Flask(__name__)

    # Конфигурация
    app.config.from_object(config_class)

    # Установка секретного ключа
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # Настройка Flask-Login
    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'info'

    # Регистрация blueprint
    from blog.user.routes import users
    app.register_blueprint(users, url_prefix="/")

    @login_manager.user_loader
    def load_user(user_id):
        from blog.models import User
        return User.query.get(int(user_id))

    return app
'''

    # Записываем базовый файл
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(basic_content)

    print("✅ Создан базовый рабочий файл blog/__init__.py")

# Теперь проверяем шаблон
template_path = Path('blog/templates/login.html')
if template_path.exists():
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Проверяем наличие CSRF токена
    if 'csrf_token()' not in template_content:
        print("🔧 Исправляем шаблон для CSRF...")

        # Заменяем form.hidden_tag() на явный CSRF токен
        if '{{ form.hidden_tag() }}' in template_content:
            new_template = template_content.replace(
                '                {{ form.hidden_tag() }}',
                '                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
            )

            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(new_template)

            print("✅ Шаблон исправлен для CSRF")
        else:
            print("⚠️ form.hidden_tag() не найден в шаблоне")
    else:
        print("✅ Шаблон уже содержит CSRF токен")
else:
    print(f"❌ Шаблон не найден: {template_path}")

# Проверяем форму
form_path = Path('blog/user/forms.py')
if form_path.exists():
    with open(form_path, 'r', encoding='utf-8') as f:
        form_content = f.read()

    # Проверяем наличие Meta класса с отключенным CSRF
    if 'class Meta:' in form_content and 'csrf = False' in form_content:
        print("🔧 Исправляем форму для CSRF...")

        # Удаляем класс Meta с отключенным CSRF
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

        with open(form_path, 'w', encoding='utf-8') as f:
            f.write(new_form_content)

        print("✅ Форма исправлена для CSRF")
    else:
        print("✅ Форма уже настроена для CSRF")
else:
    print(f"❌ Форма не найдена: {form_path}")

# Проверяем routes
routes_path = Path('blog/user/routes.py')
if routes_path.exists():
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()

    # Проверяем наличие middleware для CSRF
    if 'def set_csrf_token():' not in routes_content:
        print("🔧 Добавляем middleware для CSRF...")

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
            with open(routes_path, 'w', encoding='utf-8') as f:
                f.write(new_routes_content)

            print("✅ Middleware добавлен в routes")
        else:
            print("❌ Не найдено место для добавления middleware")
    else:
        print("✅ Middleware уже есть в routes")
else:
    print(f"❌ Routes не найден: {routes_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
print("\n💡 Если все еще есть ошибки, попробуйте:")
print("1. Полностью удалите блог/__init__.py и восстановите из git: git checkout HEAD -- blog/__init__.py")
print("2. Или скопируйте рабочий файл с другой машины")
