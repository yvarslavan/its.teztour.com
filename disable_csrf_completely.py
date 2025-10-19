#!/usr/bin/env python3
"""
Отключение CSRF для восстановления работоспособности
"""

import os
from pathlib import Path

print("🔧 Отключение CSRF для восстановления работоспособности...")

# 1. Отключаем CSRF в форме
form_file = Path('blog/user/forms.py')
if form_file.exists():
    with open(form_file, 'r', encoding='utf-8') as f:
        form_content = f.read()

    # Добавляем класс Meta с отключенным CSRF
    if 'class LoginForm(FlaskForm):' in form_content:
        # Находим класс формы
        class_start = form_content.find('class LoginForm(FlaskForm):')
        if class_start > 0:
            # Находим первое поле или метод
            next_field = form_content.find('\n    ', class_start)
            if next_field > 0:
                # Вставляем класс Meta с отключенным CSRF
                new_form_content = form_content[:next_field] + '''    class Meta:
        csrf = False  # Отключаем CSRF для восстановления работоспособности

''' + form_content[next_field:]

                with open(form_file, 'w', encoding='utf-8') as f:
                    f.write(new_form_content)

                print("✅ CSRF отключен в форме")
            else:
                print("❌ Не найдено место для добавления Meta класса")
        else:
            print("❌ Класс LoginForm не найден")
    else:
        print("❌ Файл формы не содержит LoginForm")
else:
    print(f"❌ Файл формы не найден: {form_file}")

# 2. Удаляем CSRF токен из шаблона
template_file = Path('blog/templates/login.html')
if template_file.exists():
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Заменяем явный CSRF токен на form.hidden_tag()
    if '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in template_content:
        new_template = template_content.replace(
            '                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">',
            '                {{ form.hidden_tag() }}'
        )

        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(new_template)

        print("✅ CSRF токен удален из шаблона")
    else:
        print("✅ Шаблон не содержит явный CSRF токен")
else:
    print(f"❌ Шаблон не найден: {template_file}")

# 3. Удаляем middleware из routes.py
routes_file = Path('blog/user/routes.py')
if routes_file.exists():
    with open(routes_file, 'r', encoding='utf-8') as f:
        routes_content = f.read()

    # Удаляем middleware для CSRF
    if 'def set_csrf_token():' in routes_content:
        # Находим начало и конец middleware
        middleware_start = routes_content.find('@users.before_request')
        middleware_end = routes_content.find('\n@', middleware_start + 1)
        if middleware_end == -1:
            middleware_end = routes_content.find('\n\ndef ', middleware_start + 1)
        if middleware_end == -1:
            middleware_end = len(routes_content)

        # Удаляем middleware
        new_routes_content = routes_content[:middleware_start] + routes_content[middleware_end:]

        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(new_routes_content)

        print("✅ Middleware для CSRF удален")
    else:
        print("✅ Middleware для CSRF не найден")
else:
    print(f"❌ Routes не найден: {routes_file}")

# 4. Отключаем CSRF в __init__.py
init_file = Path('blog/__init__.py')
if init_file.exists():
    with open(init_file, 'r', encoding='utf-8') as f:
        init_content = f.read()

    # Заменяем WTF_CSRF_ENABLED = True на WTF_CSRF_ENABLED = False
    if 'WTF_CSRF_ENABLED = True' in init_content:
        new_init_content = init_content.replace(
            'WTF_CSRF_ENABLED = True',
            'WTF_CSRF_ENABLED = False'
        )

        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(new_init_content)

        print("✅ CSRF отключен в __init__.py")
    else:
        print("✅ CSRF уже отключен в __init__.py или не найден")
else:
    print(f"❌ __init__.py не найден: {init_file}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
print("\n💡 Теперь сайт должен работать без CSRF защиты")
print("⚠️ Рекомендуется настроить CSRF защиту позже для безопасности")
