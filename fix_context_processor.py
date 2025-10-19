#!/usr/bin/env python3
"""
Исправление контекстного процессора для CSRF
"""

import os
from pathlib import Path

print("🔧 Исправление контекстного процессора для CSRF...")

# Путь к файлу __init__.py
init_path = Path('blog/__init__.py')

if init_path.exists():
    # Читаем текущий файл
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = init_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Находим и исправляем контекстный процессор
    if 'def inject_csrf_functions():' in content:
        # Находим начало и конец функции
        func_start = content.find('def inject_csrf_functions():')
        func_end = content.find('\n@', func_start + 1)
        if func_end == -1:
            func_end = content.find('\n\n', func_start + 1)
        if func_end == -1:
            func_end = len(content)

        # Извлекаем функцию
        func_content = content[func_start:func_end]

        # Создаем исправленную функцию
        fixed_func = '''@app.context_processor
def inject_csrf_functions():
    """Передает функцию csrf_token в контекст шаблона"""
    def csrf_token():
        """Генерирует CSRF токен"""
        try:
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            return token
        except Exception as e:
            # В случае ошибки возвращаем пустую строку
            app.logger.error(f"Error generating CSRF token: {e}")
            return ""

    return dict(csrf_token=csrf_token)'''

        # Заменяем функцию в содержимом
        new_content = content[:func_start] + fixed_func + content[func_end:]

        # Записываем изменения
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Исправлен контекстный процессор для CSRF")
    else:
        print("❌ Контекстный процессор для CSRF не найден")

        # Добавляем контекстный процессор
        app_context_pos = content.find('app = Flask(__name__)')
        if app_context_pos > 0:
            # Находим конец строки
            line_end = content.find('\n', app_context_pos)

            # Находим место для вставки (перед созданием blueprint)
            blueprint_pos = content.find('from blog.user.routes import users')
            if blueprint_pos > 0:
                insert_pos = blueprint_pos
            else:
                insert_pos = content.find('# Регистрация blueprint', 0)
                if insert_pos == -1:
                    insert_pos = len(content)

            # Создаем контекстный процессор
            context_processor = '''
# Добавляем CSRF в контекст шаблонов
@app.context_processor
def inject_csrf_functions():
    """Передает функцию csrf_token в контекст шаблона"""
    def csrf_token():
        """Генерирует CSRF токен"""
        try:
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            return token
        except Exception as e:
            # В случае ошибки возвращаем пустую строку
            app.logger.error(f"Error generating CSRF token: {e}")
            return ""

    return dict(csrf_token=csrf_token)

'''

            # Вставляем контекстный процессор
            new_content = content[:insert_pos] + context_processor + content[insert_pos:]

            # Записываем изменения
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print("✅ Добавлен контекстный процессор для CSRF")
        else:
            print("❌ Не найдено место для добавления контекстного процессора")
else:
    print(f"❌ Файл __init__.py не найден: {init_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
