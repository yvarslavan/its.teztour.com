#!/usr/bin/env python3
"""
Утилита для диагностики и очистки кэша шаблонов Flask
"""

import os
import shutil
from pathlib import Path
from blog import create_app

def clear_template_cache():
    """Очищает все виды кэша связанного с шаблонами"""

    print("🧹 Очистка всех видов кэша шаблонов...")

    # Очищаем Python кэш
    cache_dirs = [
        '__pycache__',
        'blog/__pycache__',
        'blog/templates/__pycache__',
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Удален {cache_dir}")
            except Exception as e:
                print(f"❌ Ошибка удаления {cache_dir}: {e}")

    # Очищаем .pyc файлы
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print(f"✅ Удален {file}")
                except Exception as e:
                    print(f"❌ Ошибка удаления {file}: {e}")

def diagnose_template_config():
    """Диагностирует конфигурацию шаблонов Flask"""

    print("🔍 Диагностика конфигурации шаблонов...")

    try:
        app = create_app()

        print(f"📊 Состояние приложения:")
        print(f"   DEBUG: {app.debug}")
        print(f"   TEMPLATES_AUTO_RELOAD: {app.config.get('TEMPLATES_AUTO_RELOAD')}")
        print(f"   SEND_FILE_MAX_AGE_DEFAULT: {app.config.get('SEND_FILE_MAX_AGE_DEFAULT')}")
        print(f"   jinja_env.auto_reload: {app.jinja_env.auto_reload}")
        print(f"   jinja_env.cache size: {len(app.jinja_env.cache) if hasattr(app.jinja_env, 'cache') else 'N/A'}")

        # Проверяем пути к шаблонам
        print(f"📁 Пути к шаблонам:")
        for template_folder in app.jinja_loader.searchpath:
            print(f"   {template_folder}")
            if os.path.exists(template_folder):
                print(f"     ✅ Существует")
                # Показываем несколько файлов шаблонов
                templates = [f for f in os.listdir(template_folder) if f.endswith('.html')][:5]
                for template in templates:
                    template_path = os.path.join(template_folder, template)
                    mtime = os.path.getmtime(template_path)
                    print(f"     📄 {template} (изменен: {mtime})")
            else:
                print(f"     ❌ Не существует")

        # Переменные окружения
        print(f"🌍 Переменные окружения:")
        env_vars = ['FLASK_ENV', 'FLASK_DEBUG', 'TEMPLATES_AUTO_RELOAD', 'PYTHONDONTWRITEBYTECODE']
        for var in env_vars:
            print(f"   {var}: {os.environ.get(var, 'НЕ УСТАНОВЛЕНА')}")

    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")

def force_template_reload():
    """Принудительно перезагружает шаблоны"""

    print("🔄 Принудительная перезагрузка шаблонов...")

    try:
        app = create_app()

        # Очищаем кэш Jinja
        if hasattr(app.jinja_env, 'cache'):
            app.jinja_env.cache.clear()
            print("✅ Кэш Jinja очищен")

        # Принудительно устанавливаем настройки
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        print("✅ Настройки перезагрузки шаблонов обновлены")

    except Exception as e:
        print(f"❌ Ошибка перезагрузки: {e}")

def check_template_modification_time(template_name='tasks.html'):
    """Проверяет время изменения конкретного шаблона"""

    template_path = f"blog/templates/{template_name}"

    if os.path.exists(template_path):
        mtime = os.path.getmtime(template_path)
        size = os.path.getsize(template_path)
        print(f"📄 {template_name}:")
        print(f"   Путь: {os.path.abspath(template_path)}")
        print(f"   Изменен: {mtime}")
        print(f"   Размер: {size} байт")

        # Читаем первые несколько строк
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
            print("   Первые строки:")
            for i, line in enumerate(lines, 1):
                print(f"     {i}: {line.rstrip()}")
        except Exception as e:
            print(f"   ❌ Ошибка чтения: {e}")
    else:
        print(f"❌ Шаблон {template_name} не найден")

if __name__ == "__main__":
    print("🔧 Утилита диагностики кэша шаблонов Flask")
    print("=" * 50)

    clear_template_cache()
    print()

    diagnose_template_config()
    print()

    force_template_reload()
    print()

    check_template_modification_time('tasks.html')
    print()

    print("🎯 Рекомендации:")
    print("1. Запустите сервер через restart_dev_server.bat")
    print("2. Используйте Ctrl+F5 для жесткой перезагрузки в браузере")
    print("3. Проверьте, что DEBUG: True в выводе сервера")
    print("4. Если проблема остается, проверьте кэш браузера в DevTools")
