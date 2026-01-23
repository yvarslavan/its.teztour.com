#!/bin/bash
# Настройка .env для использования порт-прокси Windows

echo "=========================================="
echo "  Настройка .env для порт-прокси"
echo "=========================================="
echo ""

# Получить IP адрес Windows хоста (для WSL)
WSL_HOST_IP=$(ip route show | grep -i default | awk '{ print $3}')

if [ -z "$WSL_HOST_IP" ]; then
    echo "❌ Не удалось определить IP адрес Windows хоста"
    exit 1
fi

echo "✅ IP адрес Windows хоста: $WSL_HOST_IP"
echo ""

# Создать резервную копию
if [ -f .env ]; then
    cp .env .env.backup.portproxy
    echo "✅ Создана резервная копия: .env.backup.portproxy"
fi

# Создать новый .env с порт-прокси
cat > .env << EOF
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-flask-helpdesk-2024-change-in-production

# MySQL Redmine Database (через порт-прокси Windows)
# Windows хост: $WSL_HOST_IP
MYSQL_HOST=$WSL_HOST_IP
MYSQL_PORT=3306
MYSQL_DATABASE=redmine
MYSQL_USER=easyredmine
MYSQL_PASSWORD=QhAKtwCLGW

# MySQL Quality Database (через порт-прокси Windows на порт 3307)
MYSQL_QUALITY_HOST=$WSL_HOST_IP
MYSQL_QUALITY_PORT=3307
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

# Oracle Configuration
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_USER=system
ORACLE_PASSWORD=oracle

# Database Path
DB_PATH=blog/db/blog.db

# XMPP Configuration
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
EOF

echo ""
echo "✅ Файл .env обновлен для порт-прокси"
echo ""
echo "📋 Конфигурация:"
echo "   MYSQL_HOST=$WSL_HOST_IP:3306 (прокси на helpdesk.teztour.com)"
echo "   MYSQL_QUALITY_HOST=$WSL_HOST_IP:3307 (прокси на quality.teztour.com)"
echo ""
echo "🔍 Проверка подключения к порт-прокси..."
echo ""

# Проверка доступности портов
if timeout 2 bash -c "</dev/tcp/$WSL_HOST_IP/3306" 2>/dev/null; then
    echo "   ✅ Порт 3306 (helpdesk) доступен"
else
    echo "   ❌ Порт 3306 (helpdesk) НЕдоступен"
    echo "   Убедитесь что порт-прокси настроен в Windows (setup_portproxy.ps1)"
fi

if timeout 2 bash -c "</dev/tcp/$WSL_HOST_IP/3307" 2>/dev/null; then
    echo "   ✅ Порт 3307 (quality) доступен"
else
    echo "   ❌ Порт 3307 (quality) НЕдоступен"
    echo "   Убедитесь что порт-прокси настроен в Windows (setup_portproxy.ps1)"
fi

echo ""
echo "=========================================="
echo "  Настройка завершена"
echo "=========================================="
echo ""
echo "🚀 Теперь можно запустить приложение:"
echo "   bash kill_port_5000.sh"
echo "   python3 app.py"
echo ""

