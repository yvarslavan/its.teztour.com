#!/usr/bin/env python3
"""
Быстрое исправление CSRF токена в шаблоне
"""

import os
from pathlib import Path

print("🔧 Быстрое исправление CSRF токена...")

# Путь к шаблону
template_path = Path('blog/templates/login.html')

if template_path.exists():
    # Читаем текущий шаблон
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = template_path.with_suffix('.html.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Заменяем form.hidden_tag() на явную генерацию CSRF токена
    if '{{ form.hidden_tag() }}' in content:
        new_content = content.replace(
            '                {{ form.hidden_tag() }}',
            """                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">"""
        )

        # Записываем изменения
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Шаблон обновлен с явной генерацией CSRF токена")
    else:
        print("⚠️ form.hidden_tag() не найден в шаблоне")

        # Проверяем, есть ли уже явный CSRF токен
        if 'csrf_token()' in content:
            print("✅ Явный CSRF токен уже есть в шаблоне")
        else:
            print("❌ CSRF токен не найден в шаблоне")
else:
    print(f"❌ Файл шаблона не найден: {template_path}")

print("\n📋 Следующие шаги:")
print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("2. Проверьте работу: python3 debug_csrf_server.py")
