#!/usr/bin/env python3
"""
Скрипт для исправления генерации CSRF токена в шаблоне
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("🔧 Исправление генерации CSRF токена...")

try:
    # Проверяем текущий шаблон
    template_path = BASE_DIR / 'blog' / 'templates' / 'login.html'

    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("📄 Текущий шаблон login.html:")

        # Проверяем наличие form.hidden_tag()
        if 'form.hidden_tag()' in content:
            print("✅ Найден form.hidden_tag()")
        else:
            print("❌ form.hidden_tag() не найден")

        # Проверяем наличие ручного CSRF токена
        if 'csrf_token()' in content:
            print("✅ Найден вызов csrf_token()")
        else:
            print("❌ Вызов csrf_token() не найден")

        # Создаем исправленный шаблон
        new_content = content.replace(
            '                {{ form.hidden_tag() }}',
                """                {% if config.WTF_CSRF_ENABLED %}
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                {% else %}
                    {{ form.hidden_tag() }}
                {% endif %}"""
        )

        # Записываем изменения
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Шаблон обновлен с явной генерацией CSRF токена")

        # Также создаем резервную копию старого шаблона
        backup_path = template_path.with_suffix('.html.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Создана резервная копия: {backup_path}")

    else:
        print(f"❌ Файл шаблона не найден: {template_path}")

    # Теперь проверим, что csrf_token доступен в контексте
    print("\n🧪 Проверка доступности csrf_token в контексте...")

    # Устанавливаем переменные окружения
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-csrf-check'
    os.environ['WTF_CSRF_ENABLED'] = 'True'

    # Загружаем .env.production если он есть
    env_file = BASE_DIR / '.env.production'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ Загружен .env.production")

    # Создаем приложение
    from blog import create_app
    app = create_app()

    print(f"🔍 WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")
    print(f"🔍 SECRET_KEY установлен: {'да' if app.secret_key else 'нет'}")

    # Проверяем наличие csrf_token в контексте
    with app.test_request_context():
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        print(f"✅ CSRF токен сгенерирован: {token[:20]}...")

        # Проверяем, что функция доступна в контексте шаблона
        from flask import render_template_string

        template = """
        {% if config.WTF_CSRF_ENABLED %}
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        {% endif %}
        """

        rendered = render_template_string(template)
        if 'csrf_token' in rendered and 'value=' in rendered:
            print("✅ CSRF токен корректно рендерится в шаблоне")
            print(f"🔍 Рендеренный HTML: {rendered.strip()}")
        else:
            print("❌ CSRF токен не рендерится в шаблоне")
            print(f"🔍 Рендеренный HTML: {rendered}")

    print("\n🎉 Исправление CSRF токена завершено!")
    print("\n📋 Следующие шаги:")
    print("1. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
    print("2. Проверьте работу сайта: https://its.tez-tour.com/login")
    print("3. Если проблема осталась, проверьте логи: sudo journalctl -u flask-helpdesk -f")

except Exception as e:
    print(f"\n❌ Ошибка при исправлении CSRF токена: {e}")
    import traceback
    traceback.print_exc()
