#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Экстренное исправление прав доступа для Flask Helpdesk
Этот скрипт должен быть запущен на сервере под пользователем с sudo правами
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Выполнить команду с обработкой ошибок"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {cmd}")
        print(f"   Код ошибки: {e.returncode}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return None

def check_directory_ownership():
    """Проверить владельца директории"""
    print("🔍 Проверка прав доступа к /var/www/flask_helpdesk...")

    result = run_command("ls -la /var/www/flask_helpdesk", check=False)
    if result and result.stdout:
        print("Текущие права:")
        print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)

    # Проверить владельца директории
    result = run_command("stat -c '%U:%G' /var/www/flask_helpdesk", check=False)
    if result and result.stdout:
        owner = result.stdout.strip()
        print(f"📁 Владелец директории: {owner}")
        return owner
    return None

def fix_directory_permissions():
    """Исправить права доступа к директории"""
    print("\n🔧 ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА...")

    # Получить текущего пользователя
    result = run_command("whoami")
    if not result:
        print("❌ Не удалось определить текущего пользователя")
        return False

    current_user = result.stdout.strip()
    print(f"👤 Текущий пользователь: {current_user}")

    # Проверить, есть ли sudo права
    result = run_command("sudo -n true", check=False)
    if result is None or result.returncode != 0:
        print("❌ Нет sudo прав. Запустите скрипт с sudo или настройте sudo без пароля")
        return False

    print("✅ Sudo права подтверждены")

    # Создать директорию если не существует
    print("📁 Создание директории...")
    run_command("sudo mkdir -p /var/www/flask_helpdesk")

    # Изменить владельца директории
    print(f"👤 Изменение владельца на {current_user}...")
    result = run_command(f"sudo chown -R {current_user}:{current_user} /var/www/flask_helpdesk")
    if result is None:
        print("❌ Не удалось изменить владельца")
        return False

    # Установить права доступа
    print("🔐 Установка прав доступа...")
    result = run_command("sudo chmod -R 755 /var/www/flask_helpdesk")
    if result is None:
        print("❌ Не удалось установить права доступа")
        return False

    print("✅ Права доступа исправлены")
    return True

def clean_flask_session():
    """Очистить проблемные файлы flask_session"""
    print("\n🧹 ОЧИСТКА FLASK_SESSION...")

    session_dir = "/var/www/flask_helpdesk/flask_session"

    # Проверить существование директории
    if not os.path.exists(session_dir):
        print("📁 Директория flask_session не существует")
        return True

    # Попробовать удалить все файлы в flask_session
    print("🗑️ Удаление файлов сессий...")
    result = run_command(f"sudo rm -rf {session_dir}/*", check=False)

    # Создать директорию заново с правильными правами
    print("📁 Пересоздание директории flask_session...")
    run_command(f"sudo mkdir -p {session_dir}")

    # Получить текущего пользователя
    result = run_command("whoami")
    if result:
        current_user = result.stdout.strip()
        run_command(f"sudo chown {current_user}:{current_user} {session_dir}")
        run_command(f"sudo chmod 755 {session_dir}")

    print("✅ Flask session очищена")
    return True

def clean_cache_files():
    """Очистить кэш файлы"""
    print("\n🧹 ОЧИСТКА КЭША...")

    flask_dir = "/var/www/flask_helpdesk"

    # Удалить __pycache__ директорий
    print("🗑️ Удаление __pycache__...")
    run_command(f"sudo find {flask_dir} -name '__pycache__' -type d -exec rm -rf {{}} + 2>/dev/null || true", check=False)

    # Удалить .pyc файлы
    print("🗑️ Удаление .pyc файлов...")
    run_command(f"sudo find {flask_dir} -name '*.pyc' -delete 2>/dev/null || true", check=False)

    # Удалить виртуальное окружение
    print("🗑️ Удаление старого venv...")
    run_command(f"sudo rm -rf {flask_dir}/venv", check=False)

    print("✅ Кэш очищен")
    return True

def setup_service_permissions():
    """Настроить права для systemd сервиса"""
    print("\n⚙️ НАСТРОЙКА ПРАВ ДЛЯ СЕРВИСА...")

    # Проверить существование сервиса
    result = run_command("sudo systemctl status flask-helpdesk", check=False)
    if result and result.returncode == 0:
        print("🔄 Остановка сервиса...")
        run_command("sudo systemctl stop flask-helpdesk", check=False)

    # Установить правильные права для рабочей директории
    flask_dir = "/var/www/flask_helpdesk"
    result = run_command("whoami")
    if result:
        current_user = result.stdout.strip()
        print(f"👤 Установка прав для пользователя {current_user}...")

        # Основные права
        run_command(f"sudo chown -R {current_user}:{current_user} {flask_dir}")
        run_command(f"sudo chmod -R 755 {flask_dir}")

                # Создать только служебные директории (НЕ ТРОГАЕМ ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ!)
        service_dirs = [
            f"{flask_dir}/logs",
            f"{flask_dir}/flask_session"
        ]

        for dir_path in service_dirs:
            run_command(f"sudo mkdir -p {dir_path}", check=False)
            run_command(f"sudo chown -R {current_user}:{current_user} {dir_path}", check=False)
            run_command(f"sudo chmod -R 755 {dir_path}", check=False)

    print("✅ Права для сервиса настроены")
    return True

def main():
    """Основная функция"""
    print("🚨 ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА FLASK HELPDESK")
    print("=" * 60)

    # Проверить, что скрипт запущен на сервере
    if not os.path.exists("/var/www"):
        print("❌ Этот скрипт должен быть запущен на сервере")
        sys.exit(1)

    try:
        # 1. Проверить текущие права
        check_directory_ownership()

        # 2. Исправить права доступа
        if not fix_directory_permissions():
            print("❌ Не удалось исправить права доступа")
            sys.exit(1)

        # 3. Очистить проблемные файлы
        clean_flask_session()
        clean_cache_files()

        # 4. Настроить права для сервиса
        setup_service_permissions()

        print("\n" + "=" * 60)
        print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("\nТеперь можно запустить развертывание GitLab CI/CD")
        print("\nДля перезапуска сервиса выполните:")
        print("sudo systemctl restart flask-helpdesk")
        print("sudo systemctl status flask-helpdesk")

    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
