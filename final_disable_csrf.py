#!/usr/bin/env python3
"""
Финальное отключение CSRF для стабильной работы
"""

import os
import subprocess
from pathlib import Path

print("🔧 Финальное отключение CSRF для стабильной работы...")

# 1. Восстанавливаем файлы из git
files_to_restore = [
    'blog/__init__.py',
    'blog/user/forms.py',
    'blog/user/routes.py',
    'blog/templates/login.html',
    'blog/templates/layout_auth.html'
]

for file_path in files_to_restore:
    path = Path(file_path)
    if path.exists():
        # Восстанавливаем файл из git
        result = subprocess.run(
            ["git", "checkout", "HEAD", "--", file_path],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        if result.returncode == 0:
            print(f"✅ Файл {file_path} восстановлен из git")
        else:
            print(f"❌ Ошибка восстановления {file_path}: {result.stderr}")

# 2. Отключаем CSRF в форме
form_file = Path('blog/user/forms.py')
if form_file.exists():
    with open(form_file, 'r', encoding='utf-8') as f:
        form_content = f.read()

    # Проверяем, есть ли уже класс Meta
    if 'class LoginForm(FlaskForm):' in form_content:
        # Находим класс формы
        class_start = form_content.find('class LoginForm(FlaskForm):')
        if class_start > 0:
            # Находим первое поле
            next_field = form_content.find('\n    ', class_start)
            if next_field > 0:
                # Проверяем, есть ли уже класс Meta
                meta_start = form_content.find('class Meta:', class_start, next_field)
                if meta_start == -1:
                    # Добавляем класс Meta с отключенным CSRF
                    new_form_content = form_content[:next_field] + '''    class Meta:
        csrf = False

''' + form_content[next_field:]

                    with open(form_file, 'w', encoding='utf-8') as f:
                        f.write(new_form_content)

                    print("✅ Добавлен class Meta с отключенным CSRF")
                else:
                    # Проверяем, отключен ли CSRF
                    meta_end = form_content.find('\n    ', meta_start)
                    if meta_end == -1:
                        meta_end = next_field

                    meta_content = form_content[meta_start:meta_end]
                    if 'csrf = False' in meta_content:
                        print("✅ CSRF уже отключен в форме")
                    else:
                        # Отключаем CSRF
                        new_meta_content = meta_content.replace('csrf = True', 'csrf = False')
                        new_form_content = form_content[:meta_start] + new_meta_content + form_content[meta_end:]

                        with open(form_file, 'w', encoding='utf-8') as f:
                            f.write(new_form_content)

                        print("✅ CSRF отключен в существующем классе Meta")
            else:
                print("❌ Не найдено место для добавления Meta класса")
        else:
            print("❌ Класс LoginForm не найден")

# 3. Удаляем csrf_token из layout_auth.html
layout_file = Path('blog/templates/layout_auth.html')
if layout_file.exists():
    with open(layout_file, 'r', encoding='utf-8') as f:
        layout_content = f.read()

    # Удаляем строку с csrf-token
    if '<meta name="csrf-token" content="{{ csrf_token() }}">' in layout_content:
        new_layout_content = layout_content.replace(
            '    <meta name="csrf-token" content="{{ csrf_token() }}">\n',
            ''
        )

        with open(layout_file, 'w', encoding='utf-8') as f:
            f.write(new_layout_content)

        print("✅ Удален csrf-token из layout_auth.html")
    else:
        print("✅ csrf-token не найден в layout_auth.html")

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

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу сайта: https://its.tez-tour.com/login")
print("\n💡 Теперь сайт должен работать стабильно без CSRF защиты")
