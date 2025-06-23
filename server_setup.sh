#!/bin/bash

# =======================================================
# СКРИПТ ПОДГОТОВКИ СЕРВЕРА ДЛЯ FLASK HELPDESK
# Версия: 2.0
# Дата: 2024-12-27
# =======================================================

set -e  # Прерывать выполнение при ошибке

echo "🚀 ПОДГОТОВКА СЕРВЕРА ДЛЯ FLASK HELPDESK"
echo "========================================="

# Проверка прав sudo
if [[ $EUID -eq 0 ]]; then
   echo "❌ Не запускайте этот скрипт от root. Используйте пользователя с sudo правами."
   exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "📦 Установка необходимых пакетов..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    pkg-config \
    nginx \
    supervisor \
    git \
    curl \
    wget \
    htop \
    ufw

# Создание пользователя для деплоя (если не существует)
DEPLOY_USER="deploy"
if ! id "$DEPLOY_USER" &>/dev/null; then
    echo "👤 Создание пользователя для деплоя..."
    sudo adduser --disabled-password --gecos "" $DEPLOY_USER
    sudo usermod -aG sudo $DEPLOY_USER
    echo "✅ Пользователь $DEPLOY_USER создан"
else
    echo "✅ Пользователь $DEPLOY_USER уже существует"
fi

# Создание директорий для проекта
echo "📁 Создание директорий..."
sudo mkdir -p /var/www/flask_helpdesk
sudo mkdir -p /var/backups/flask_helpdesk
sudo mkdir -p /var/log/flask_helpdesk

# Настройка прав доступа
echo "🔧 Настройка прав доступа..."
sudo chown -R www-data:www-data /var/www/flask_helpdesk
sudo chown -R $DEPLOY_USER:$DEPLOY_USER /var/backups/flask_helpdesk
sudo chown -R www-data:www-data /var/log/flask_helpdesk

sudo chmod -R 755 /var/www/flask_helpdesk
sudo chmod -R 755 /var/backups/flask_helpdesk
sudo chmod -R 755 /var/log/flask_helpdesk

# Добавление пользователя deploy в группу www-data
sudo usermod -aG www-data $DEPLOY_USER

# Настройка SSH для пользователя deploy
echo "🔑 Настройка SSH..."
sudo -u $DEPLOY_USER mkdir -p /home/$DEPLOY_USER/.ssh
sudo -u $DEPLOY_USER chmod 700 /home/$DEPLOY_USER/.ssh

echo "📝 Создайте SSH ключ для деплоя:"
echo "   ssh-keygen -t rsa -b 4096 -f ~/.ssh/flask_helpdesk_deploy"
echo "   Затем добавьте публичный ключ в /home/$DEPLOY_USER/.ssh/authorized_keys"

# Настройка firewall
echo "🛡️ Настройка firewall..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5000  # Flask dev server
sudo ufw --force enable

# Создание конфигурации Nginx
echo "🌐 Создание конфигурации Nginx..."
sudo tee /etc/nginx/sites-available/flask_helpdesk > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # Замените на ваш домен

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Увеличиваем таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы
    location /static {
        alias /var/www/flask_helpdesk/blog/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Логи
    access_log /var/log/nginx/flask_helpdesk_access.log;
    error_log /var/log/nginx/flask_helpdesk_error.log;
}
EOF

# Активация сайта Nginx
sudo ln -sf /etc/nginx/sites-available/flask_helpdesk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Создание шаблона systemd сервиса
echo "⚙️ Создание шаблона systemd сервиса..."
sudo tee /etc/systemd/system/flask-helpdesk.service > /dev/null <<EOF
[Unit]
Description=Flask Helpdesk Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/flask_helpdesk
Environment=PATH=/var/www/flask_helpdesk/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=app.py
ExecStart=/var/www/flask_helpdesk/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

# Логирование
StandardOutput=append:/var/log/flask_helpdesk/app.log
StandardError=append:/var/log/flask_helpdesk/error.log

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/www/flask_helpdesk /var/log/flask_helpdesk

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload

# Создание логrotate конфигурации
echo "📝 Настройка ротации логов..."
sudo tee /etc/logrotate.d/flask_helpdesk > /dev/null <<EOF
/var/log/flask_helpdesk/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload flask-helpdesk || true
    endscript
}
EOF

# Создание cron задачи для очистки старых бэкапов
echo "🗂️ Настройка очистки старых бэкапов..."
(crontab -l 2>/dev/null; echo "0 2 * * * find /var/backups/flask_helpdesk -name 'backup_*' -mtime +7 -delete") | crontab -

echo ""
echo "✅ СЕРВЕР ПОДГОТОВЛЕН УСПЕШНО!"
echo "================================"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "1. Создайте SSH ключ для деплоя:"
echo "   ssh-keygen -t rsa -b 4096 -f ~/.ssh/flask_helpdesk_deploy"
echo ""
echo "2. Добавьте публичный ключ на сервер:"
echo "   ssh-copy-id -i ~/.ssh/flask_helpdesk_deploy.pub $DEPLOY_USER@YOUR_SERVER"
echo ""
echo "3. Добавьте переменные в GitLab CI/CD:"
echo "   - SSH_PRIVATE_KEY (содержимое ~/.ssh/flask_helpdesk_deploy)"
echo "   - DEPLOY_SERVER (IP или домен сервера)"
echo "   - DEPLOY_USER ($DEPLOY_USER)"
echo ""
echo "4. Обновите .gitlab-ci.yml для активации деплоя"
echo ""
echo "🎯 Готово к деплою!"
