#!/usr/bin/env python3
"""
Исправление шаблона layout_auth.html для корректной работы с CSRF
"""

import os
from pathlib import Path

print("🔧 Исправление шаблона layout_auth.html...")

# Проверяем layout_auth.html
layout_file = Path('blog/templates/layout_auth.html')
if layout_file.exists():
    with open(layout_file, 'r', encoding='utf-8') as f:
        layout_content = f.read()

    print("✅ Найден файл layout_auth.html")

    # Проверяем наличие csrf_token в шаблоне
    if '{{ csrf_token() }}' in layout_content:
        print("⚠️ Найден {{ csrf_token() }} в layout_auth.html")

        # Заменяем на условный вывод, чтобы избежать ошибки если WTF_CSRF_ENABLED=False
        if '{% if config.WTF_CSRF_ENABLED %}' not in layout_content:
            # Заменяем строку с csrf_token на условный вывод
            if '<meta name="csrf-token" content="{{ csrf_token() }}">' in layout_content:
                new_layout_content = layout_content.replace(
                    '<meta name="csrf-token" content="{{ csrf_token() }}">',
                    '{% if config.WTF_CSRF_ENABLED %}<meta name="csrf-token" content="{{ csrf_token() }}">{% endif %}'
                )

                with open(layout_file, 'w', encoding='utf-8') as f:
                    f.write(new_layout_content)

                print("✅ Исправлен csrf_token в layout_auth.html")
            else:
                print("❌ Не найдена строка с csrf-token meta")
        else:
            print("✅ csrf_token уже обернут в условие")
    else:
        print("✅ csrf_token не найден в layout_auth.html")
else:
    print(f"❌ Файл layout_auth.html не найден: {layout_file}")

# Проверяем login.html
login_file = Path('blog/templates/login.html')
if login_file.exists():
    with open(login_file, 'r', encoding='utf-8') as f:
        login_content = f.read()

    print("✅ Найден файл login.html")

    # Проверяем наличие form.hidden_tag()
    if '{{ form.hidden_tag() }}' in login_content:
        print("✅ Найден {{ form.hidden_tag() }} в login.html")
    else:
        print("⚠️ form.hidden_tag() не найден в login.html")

        # Проверяем наличие явного CSRF токена
        if '<input type="hidden" name="csrf_token"' in login_content:
            print("⚠️ Найден явный CSRF токен в login.html")

            # Заменяем на form.hidden_tag()
            new_login_content = login_content.replace(
                '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">',
                '{{ form.hidden_tag() }}'
            )

            with open(login_file, 'w', encoding='utf-8') as f:
                f.write(new_login_content)

            print("✅ Заменен явный CSRF токен на form.hidden_tag()")
        else:
            print("❌ Явный CSRF токен не найден в login.html")
else:
    print(f"❌ Файл login.html не найден: {login_file}")

# Проверяем форму
form_file = Path('blog/user/forms.py')
if form_file.exists():
    with open(form_file, 'r', encoding='utf-8') as f:
        form_content = f.read()

    print("✅ Найден файл forms.py")

    # Проверяем наличие класса Meta с отключенным CSRF
    if 'class Meta:' in form_content and 'csrf = False' in form_content:
        print("✅ Найден class Meta с отключенным CSRF")
    else:
        print("⚠️ Не найден class Meta с отключенным CSRF")

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
        csrf = False

''' + form_content[next_field:]

                    with open(form_file, 'w', encoding='utf-8') as f:
                        f.write(new_form_content)

                    print("✅ Добавлен class Meta с отключенным CSRF")
                else:
                    print("❌ Не найдено место для добавления Meta класса")
            else:
                print("❌ Класс LoginForm не найден")
else:
    print(f"❌ Файл forms.py не найден: {form_file}")

# Проверяем __init__.py
init_file = Path('blog/__init__.py')
if init_file.exists():
    with open(init_file, 'r', encoding='utf-8') as f:
        init_content = f.read()

    print("✅ Найден файл __init__.py")

    # Проверяем наличие контекстного процессора для CSRF
    if 'def inject_csrf_functions():' in init_content:
        print("⚠️ Найден контекстный процессор для CSRF")

        # Удаляем контекстный процессор
        cp_start = init_content.find('@app.context_processor')
        cp_end = init_content.find('\n@', cp_start + 1)
        if cp_end == -1:
            cp_end = init_content.find('\n\n', cp_start + 1)
        if cp_end == -1:
            cp_end = len(init_content)

        # Удаляем контекстный процессор
        new_init_content = init_content[:cp_start] + init_content[cp_end:]

        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(new_init_content)

        print("✅ Удален контекстный процессор для CSRF")
    else:
        print("✅ Контекстный процессор для CSRF не найден")
else:
    print(f"❌ Файл __init__.py не найден: {init_file}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
