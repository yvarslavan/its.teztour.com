#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки конфигурации WSL с VPN
Создает правильный .env файл для работы в WSL с Cisco Secure Client
"""

from pathlib import Path
import sys

def create_wsl_env():
    """Создать .env файл для WSL с VPN"""
    
    env_content = """# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-flask-helpdesk-2024-change-in-production

# MySQL Redmine Database (прямое подключение через VPN в WSL)
MYSQL_HOST=helpdesk.teztour.com
MYSQL_DATABASE=redmine
MYSQL_USER=easyredmine
MYSQL_PASSWORD=QhAKtwCLGW

# MySQL Quality Database (прямое подключение через VPN в WSL)
MYSQL_QUALITY_HOST=quality.teztour.com
MYSQL_QUALITY_DATABASE=redmine
MYSQL_QUALITY_USER=easyredmine
MYSQL_QUALITY_PASSWORD=QhAKtwCLGW

# Redmine API Configuration
REDMINE_URL=https://helpdesk.teztour.com
REDMINE_API_KEY=your_redmine_api_key_here
REDMINE_LOGIN_ADMIN=admin
REDMINE_PASSWORD_ADMIN=admin

# Redmine Quality Configuration
REDMINE_QUALITY_URL=https://quality.teztour.com
REDMINE_QUALITY_API_KEY=your_quality_api_key_here
REDMINE_QUALITY_LOGIN_ADMIN=admin
REDMINE_QUALITY_PASSWORD_ADMIN=admin
REDMINE_QUALITY_ANONYMOUS_USER_ID=4
REDMINE_ANONYMOUS_USER_ID=4

# Session Configuration
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400

# Oracle Configuration (если используется)
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_USER=system
ORACLE_PASSWORD=oracle

# Database Path
DB_PATH=blog/db/blog.db

# XMPP Configuration (если используется)
XMPP_JABBERID=
XMPP_SENDER_PASSWORD=

# Recovery Password URL
RECOVERY_PASSWORD_URL=

# File Paths
ERP_FILE_PATH=

# Logging Configuration
LOG_LEVEL=INFO
LOG_PATH=logs/app.log

# Email Configuration
SENDER_EMAIL=
SENDER_PASSWORD=

# GitHub Configuration
GITHUB_TOKEN=
"""
    
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"
    
    # Создаем резервную копию если .env существует
    if env_file.exists():
        backup_file = base_dir / ".env.backup"
        import shutil
        shutil.copy2(env_file, backup_file)
        print(f"✅ Создана резервная копия: .env.backup")
    
    # Записываем новый .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Создан файл .env для WSL с VPN")
    print()
    print("📋 Конфигурация:")
    print("   MYSQL_HOST=helpdesk.teztour.com")
    print("   MYSQL_QUALITY_HOST=quality.teztour.com")
    print()
    print("⚠️  ВАЖНО: Убедитесь что VPN подключен в Windows!")
    print()
    print("🔍 Проверьте доступность серверов:")
    print("   ping -c 3 helpdesk.teztour.com")
    print("   ping -c 3 quality.teztour.com")
    print()
    print("🔌 Проверьте доступность портов MySQL:")
    print("   nc -zv helpdesk.teztour.com 3306")
    print("   nc -zv quality.teztour.com 3306")
    print()
    print("🚀 После проверки запустите приложение:")
    print("   python3 app.py")
    
    return True

if __name__ == "__main__":
    try:
        create_wsl_env()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

