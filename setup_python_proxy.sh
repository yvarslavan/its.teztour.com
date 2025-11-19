#!/bin/bash
# Настройка окружения через локальный Python Proxy
# Решает проблемы с доступом к MySQL, Oracle и HTTPS (Redmine) из WSL

echo "=========================================="
echo "  Настройка Python Proxy для WSL"
echo "=========================================="
echo ""

# 1. Определить IP Windows
# В режиме Mirroring (WSL2) 127.0.0.1 доступен для связи с Windows
# Это должно работать стабильнее, чем внешний IP
WSL_HOST=127.0.0.1
echo "✅ Windows Host: $WSL_HOST (Localhost Mode)"

# 2. Запустить прокси (в фоне)
echo "🚀 Запуск прокси серверов..."
pkill -f "python3 proxy.py" 2>/dev/null

# MySQL Helpdesk (3306 -> Windows:3306)
nohup python3 proxy.py 13306 $WSL_HOST 3306 > /tmp/proxy_3306.log 2>&1 &
echo "   Proxy 13306 -> $WSL_HOST:3306 started"

# MySQL Quality (3307 -> Windows:3307)
nohup python3 proxy.py 13307 $WSL_HOST 3307 > /tmp/proxy_3307.log 2>&1 &
echo "   Proxy 13307 -> $WSL_HOST:3307 started"

# Oracle (1521 -> Windows:1521)
nohup python3 proxy.py 11521 $WSL_HOST 1521 > /tmp/proxy_1521.log 2>&1 &
echo "   Proxy 11521 -> $WSL_HOST:1521 started"

# MySQL VoIP CRM (3308 -> Windows:3308)
nohup python3 proxy.py 13308 $WSL_HOST 3308 > /tmp/proxy_3308.log 2>&1 &
echo "   Proxy 13308 -> $WSL_HOST:3308 started"

# Redmine HTTPS (443 -> Windows:8443)
# Запускаем на порту 443, чтобы обойти проблемы с редиректами и портами
# Требуется sudo для порта < 1024
sudo nohup python3 proxy.py 443 $WSL_HOST 8443 > /tmp/proxy_443.log 2>&1 &
echo "   Proxy 443 -> $WSL_HOST:8443 (HTTPS) started (sudo required)"

sleep 1

# 2.5 Настройка /etc/hosts (требуется sudo)
echo "🔧 Настройка /etc/hosts..."
if ! grep -q "helpdesk.teztour.com" /etc/hosts; then
    echo "127.0.0.1 helpdesk.teztour.com" | sudo tee -a /etc/hosts > /dev/null
    echo "   ✅ Добавлена запись в /etc/hosts"
else
    echo "   ✅ Запись в /etc/hosts уже существует"
fi

# 3. Обновить .env
echo "📝 Обновление конфигурации..."

# Создать новый .env
cat > .env << EOF
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-flask-helpdesk-2024-change-in-production

# MySQL (Local Proxy)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=13306
MYSQL_DATABASE=redmine
MYSQL_USER=easyredmine
MYSQL_PASSWORD=QhAKtwCLGW

# MySQL Quality (Local Proxy)
MYSQL_QUALITY_HOST=127.0.0.1:13307
MYSQL_QUALITY_DATABASE=redmine
MYSQL_QUALITY_USER=easyredmine
MYSQL_QUALITY_PASSWORD=QhAKtwCLGW

# MySQL VoIP CRM (Local Proxy)
MYSQL_VOIP_HOST=127.0.0.1
MYSQL_VOIP_PORT=13308
MYSQL_VOIP_DATABASE=tez_tour_cc
MYSQL_VOIP_USER=root
MYSQL_VOIP_PASSWORD=weo2ik3jc

# Oracle (Local Proxy)
ORACLE_HOST=127.0.0.1
ORACLE_PORT=11521
ORACLE_SERVICE_NAME=ENISK.TEZTOUR.COM
ORACLE_USER=helpdesk
ORACLE_PASSWORD=alex2085

# Redmine API (HTTPS Proxy)
REDMINE_URL=https://helpdesk.teztour.com
REDMINE_API_KEY=your_redmine_api_key_here
REDMINE_LOGIN_ADMIN=admin
REDMINE_PASSWORD_ADMIN=admin
REDMINE_QUALITY_URL=https://quality.teztour.com
REDMINE_QUALITY_API_KEY=your_quality_api_key_here
REDMINE_QUALITY_LOGIN_ADMIN=admin
REDMINE_QUALITY_PASSWORD_ADMIN=admin
REDMINE_QUALITY_ANONYMOUS_USER_ID=4
REDMINE_ANONYMOUS_USER_ID=4

# Other
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400
DB_PATH=blog/db/blog.db
LOG_LEVEL=INFO
LOG_PATH=logs/app.log
EOF

echo "✅ Конфигурация обновлена"
echo ""
echo "🔍 Проверка подключения..."
# Проверяем подключение к ПРОКСИ (локально), а не к удаленному хосту
timeout 1 bash -c "</dev/tcp/127.0.0.1/13306" && echo "   ✅ MySQL Proxy OK" || echo "   ❌ MySQL Proxy FAIL"
timeout 1 bash -c "</dev/tcp/127.0.0.1/13307" && echo "   ✅ Quality Proxy OK" || echo "   ❌ Quality Proxy FAIL"
timeout 1 bash -c "</dev/tcp/127.0.0.1/13308" && echo "   ✅ VoIP CRM Proxy OK" || echo "   ❌ VoIP CRM Proxy FAIL"
timeout 1 bash -c "</dev/tcp/127.0.0.1/11521" && echo "   ✅ Oracle Proxy OK" || echo "   ⚠️  Oracle Proxy FAIL (возможно не настроен в Windows)"
timeout 1 bash -c "</dev/tcp/127.0.0.1/443" && echo "   ✅ HTTPS Proxy OK" || echo "   ⚠️  HTTPS Proxy FAIL (sudo required?)"

echo ""
echo "⚠️  ВАЖНО: В Windows выполните (Admin PowerShell):"
echo "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=1521 connectaddress=10.7.23.4 connectport=1521"
echo "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306"
echo "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306"
echo "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3308 connectaddress=voipcrm.tez-tour.com connectport=3306"
echo "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=8443 connectaddress=helpdesk.teztour.com connectport=443"
echo ""
echo "🚀 Готово! Запускайте приложение:"
echo "   python3 app.py"
