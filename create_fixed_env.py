#!/usr/bin/env python3
"""
Создание исправленного .env.production
"""

import os
from pathlib import Path

print("🔧 Создание исправленного .env.production...")

# Проверяем существующий файл
env_file = Path('.env.production')
existing_settings = {}

if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()

    # Читаем существующие настройки
    for line in content.split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            existing_settings[key] = value

    print("✅ Прочитаны существующие настройки")
else:
    print("⚠️ Файл .env.production не найден, создаем новый")

# Создаем исправленные настройки
fixed_settings = {
    # Основные настройки
    'FLASK_ENV': 'production',
    'SECRET_KEY': existing_settings.get('SECRET_KEY', 'production-secret-key-change-this-in-real-deployment-2024'),
    'FLASK_DEBUG': 'False',
    'FLASK_APP': 'run.py',

    # Настройки CSRF и сессий
    'WTF_CSRF_ENABLED': 'True',
    'SESSION_TYPE': 'filesystem',
    'SESSION_FILE_DIR': '/tmp/flask_sessions',
    'PERMANENT_SESSION_LIFETIME': '86400',  # 24 часа

    # Настройки безопасности
    'SESSION_COOKIE_SECURE': 'True',
    'SESSION_COOKIE_HTTPONLY': 'True',
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_DOMAIN': 'its.tez-tour.com',

    # Логирование
    'LOG_LEVEL': 'INFO',
    'LOG_FILE_PATH': 'logs/app.log',
    'ERROR_LOG_FILE_PATH': 'logs/error.log',
    'LOG_MAX_BYTES': '10485760',
    'LOG_BACKUP_COUNT': '7',
}

# Создаем новый .env.production
with open(env_file, 'w') as f:
    f.write("# =============================================================================\n")
    f.write("# ОСНОВНЫЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ (ПРОДАКШЕН)\n")
    f.write("# =============================================================================\n")
    f.write(f"FLASK_ENV={fixed_settings['FLASK_ENV']}\n")
    f.write(f"SECRET_KEY={fixed_settings['SECRET_KEY']}\n")
    f.write(f"FLASK_DEBUG={fixed_settings['FLASK_DEBUG']}\n")
    f.write(f"FLASK_APP={fixed_settings['FLASK_APP']}\n")
    f.write("\n")
    f.write("# =============================================================================\n")
    f.write("# НАСТРОЙКИ CSRF И СЕССИЙ\n")
    f.write("# =============================================================================\n")
    f.write(f"WTF_CSRF_ENABLED={fixed_settings['WTF_CSRF_ENABLED']}\n")
    f.write(f"SESSION_TYPE={fixed_settings['SESSION_TYPE']}\n")
    f.write(f"SESSION_FILE_DIR={fixed_settings['SESSION_FILE_DIR']}\n")
    f.write(f"PERMANENT_SESSION_LIFETIME={fixed_settings['PERMANENT_SESSION_LIFETIME']}\n")
    f.write("\n")
    f.write("# =============================================================================\n")
    f.write("# НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА\n")
    f.write("# =============================================================================\n")
    f.write(f"SESSION_COOKIE_SECURE={fixed_settings['SESSION_COOKIE_SECURE']}\n")
    f.write(f"SESSION_COOKIE_HTTPONLY={fixed_settings['SESSION_COOKIE_HTTPONLY']}\n")
    f.write(f"SESSION_COOKIE_SAMESITE={fixed_settings['SESSION_COOKIE_SAMESITE']}\n")
    f.write(f"SESSION_COOKIE_DOMAIN={fixed_settings['SESSION_COOKIE_DOMAIN']}\n")
    f.write("\n")
    f.write("# =============================================================================\n")
    f.write("# ЛОГИРОВАНИЕ В ПРОДАКШЕНЕ\n")
    f.write("# =============================================================================\n")
    f.write(f"LOG_LEVEL={fixed_settings['LOG_LEVEL']}\n")
    f.write(f"LOG_FILE_PATH={fixed_settings['LOG_FILE_PATH']}\n")
    f.write(f"ERROR_LOG_FILE_PATH={fixed_settings['ERROR_LOG_FILE_PATH']}\n")
    f.write(f"LOG_MAX_BYTES={fixed_settings['LOG_MAX_BYTES']}\n")
    f.write(f"LOG_BACKUP_COUNT={fixed_settings['LOG_BACKUP_COUNT']}\n")

print(f"✅ Создан исправленный файл: {env_file}")

# Создаем директорию для сессий
session_dir = Path(fixed_settings['SESSION_FILE_DIR'])
if not session_dir.exists():
    os.makedirs(session_dir, exist_ok=True)
    os.chmod(session_dir, 0o777)
    print(f"✅ Создана директория для сессий: {session_dir}")
else:
    # Устанавливаем права
    os.chmod(session_dir, 0o777)
    print(f"✅ Установлены права для директории сессий: {session_dir}")

# Создаем директорию для логов
log_dir = Path('logs')
if not log_dir.exists():
    os.makedirs(log_dir, exist_ok=True)
    print(f"✅ Создана директория для логов: {log_dir}")

# Создаем файл для systemd
systemd_env = Path('flask-helpdesk.env')
with open(systemd_env, 'w') as f:
    for key, value in fixed_settings.items():
        f.write(f"{key}={value}\n")

print(f"✅ Создан файл для systemd: {systemd_env}")

print("\n📋 Следующие шаги:")
print("1. Обновите systemd сервис для использования flask-helpdesk.env:")
print("   sudo nano /etc/systemd/system/flask-helpdesk.service")
print("   Добавьте строку: EnvironmentFile=/opt/www/its.teztour.com/flask-helpdesk.env")
print("2. Перезагрузите systemd: sudo systemctl daemon-reload")
print("3. Перезапустите сервис: sudo systemctl restart flask-helpdesk")
print("4. Проверьте работу: python3 debug_csrf_server.py")
