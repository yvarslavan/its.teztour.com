#!/bin/bash

# Скрипт для настройки Red Hat сервера для Flask приложения
# Выполняется от пользователя с sudo правами

set -e

echo "🚀 Начинаем настройку Red Hat сервера для Flask Helpdesk..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода ошибок
error() {
    echo -e "${RED}❌ Ошибка: $1${NC}" >&2
    exit 1
}

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Функция для вывода предупреждений
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Проверяем что у пользователя есть sudo права
if ! sudo -n true 2>/dev/null; then
    echo "🔐 Требуется ввести пароль для sudo..."
    if ! sudo true; then
        error "У пользователя нет sudo прав или неверный пароль"
    fi
fi

echo "✅ Sudo права подтверждены"

# Переменные
DEPLOY_USER="deploy"
PROJECT_PATH="/opt/www"
BACKUP_PATH="/opt/backups/flask_helpdesk"
DOMAIN="its.tez-tour.com"
CURRENT_USER=$(whoami)

echo "📋 Параметры настройки:"
echo "   Текущий пользователь: $CURRENT_USER"
echo "   Пользователь для деплоя: $DEPLOY_USER"
echo "   Путь проекта: $PROJECT_PATH"
echo "   Путь бэкапов: $BACKUP_PATH"
echo "   Домен: $DOMAIN"
echo

# Обновляем систему
echo "🔄 Обновляем систему Red Hat..."
sudo dnf update -y || error "Не удалось обновить систему"
success "Система обновлена"

# Устанавливаем необходимые пакеты
echo "📦 Устанавливаем необходимые пакеты..."
sudo dnf install -y python3 python3-pip nginx git sqlite-devel \
    gcc python3-devel mysql-devel pkg-config openssl-devel \
    libffi-devel systemd-devel firewalld certbot python3-certbot-nginx \
    rsync tar gzip curl wget || error "Не удалось установить пакеты"
success "Пакеты установлены"

# Создаем пользователя для деплоя
echo "👤 Создаем пользователя $DEPLOY_USER..."
if ! id "$DEPLOY_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $DEPLOY_USER
    sudo usermod -aG wheel $DEPLOY_USER
    success "Пользователь $DEPLOY_USER создан"
else
    warning "Пользователь $DEPLOY_USER уже существует"
fi

# Создаем директории для проекта
echo "📁 Создаем директории..."
sudo mkdir -p $PROJECT_PATH
sudo mkdir -p $BACKUP_PATH
sudo chown $DEPLOY_USER:$DEPLOY_USER $PROJECT_PATH
sudo chown $DEPLOY_USER:$DEPLOY_USER $BACKUP_PATH
sudo chmod 755 $PROJECT_PATH
sudo chmod 755 $BACKUP_PATH
success "Директории созданы"

# Настраиваем Nginx
echo "🌐 Настраиваем Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Проверяем что Nginx запустился
if ! sudo systemctl is-active --quiet nginx; then
    error "Nginx не запустился"
fi
success "Nginx настроен и запущен"

# Настраиваем Firewall
echo "🔥 Настраиваем Firewall..."
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
success "Firewall настроен"

# Настраиваем SELinux (если активен)
echo "🔒 Проверяем SELinux..."
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce)
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo "SELinux активен, настраиваем политики..."
        sudo setsebool -P httpd_can_network_connect on || warning "Не удалось настроить SELinux для HTTP"
        sudo setsebool -P httpd_execmem on || warning "Не удалось настроить SELinux для памяти"
        success "SELinux настроен"
    else
        echo "SELinux не активен или в режиме Permissive"
    fi
fi

# Создаем SSH директорию для пользователя deploy
echo "🔐 Настраиваем SSH для пользователя $DEPLOY_USER..."
sudo -u $DEPLOY_USER mkdir -p /home/$DEPLOY_USER/.ssh
sudo -u $DEPLOY_USER chmod 700 /home/$DEPLOY_USER/.ssh
sudo -u $DEPLOY_USER touch /home/$DEPLOY_USER/.ssh/authorized_keys
sudo -u $DEPLOY_USER chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
success "SSH директория создана"

# Создаем базовую конфигурацию Nginx
echo "📝 Создаем базовую конфигурацию Nginx..."
sudo tee /etc/nginx/conf.d/default.conf > /dev/null << 'EOF'
server {
    listen 80 default_server;
    server_name _;

    location / {
        return 200 'Red Hat server is ready for Flask deployment';
        add_header Content-Type text/plain;
    }
}
EOF

sudo nginx -t || error "Конфигурация Nginx некорректна"
sudo systemctl reload nginx
success "Базовая конфигурация Nginx создана"

# Проверяем Python
echo "🐍 Проверяем Python..."
PYTHON_VERSION=$(python3 --version)
echo "Установлен: $PYTHON_VERSION"
success "Python готов к использованию"

# Создаем тестовое виртуальное окружение
echo "🧪 Тестируем создание виртуального окружения..."
sudo -u $DEPLOY_USER python3 -m venv /tmp/test_venv
sudo -u $DEPLOY_USER /tmp/test_venv/bin/pip install --upgrade pip
sudo rm -rf /tmp/test_venv
success "Виртуальное окружение работает"

# Добавляем текущего пользователя в sudoers для удобства (опционально)
echo "🔧 Настраиваем дополнительные права..."
# Добавляем возможность текущему пользователю управлять сервисами без пароля
sudo tee /etc/sudoers.d/flask-helpdesk > /dev/null << EOF
# Права для управления Flask Helpdesk сервисами
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl start flask-helpdesk
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl stop flask-helpdesk
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart flask-helpdesk
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl status flask-helpdesk
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/journalctl -u flask-helpdesk *
$DEPLOY_USER ALL=(ALL) NOPASSWD: ALL
EOF
success "Дополнительные права настроены"

# Информация о логах
echo "📋 Полезная информация:"
echo "   Логи Nginx: /var/log/nginx/"
echo "   Логи systemd: journalctl -u flask-helpdesk -f"
echo "   Статус сервисов: systemctl status nginx"
echo "   Пользователь для деплоя: $DEPLOY_USER"
echo "   Домашняя директория: /home/$DEPLOY_USER"
echo "   Текущий пользователь: $CURRENT_USER"
echo

# Инструкции для следующих шагов
echo "📖 Следующие шаги:"
echo "1. Добавьте SSH ключ в /home/$DEPLOY_USER/.ssh/authorized_keys"
echo "   Команда: sudo nano /home/$DEPLOY_USER/.ssh/authorized_keys"
echo "2. Настройте DNS запись для домена $DOMAIN"
echo "3. Настройте переменные в GitLab CI/CD:"
echo "   - SSH_PRIVATE_KEY: содержимое приватного ключа"
echo "   - DEPLOY_SERVER: IP адрес этого сервера"
echo "   - DEPLOY_USER: $DEPLOY_USER"
echo "4. Запустите pipeline в GitLab"
echo

success "Сервер Red Hat готов для деплоя Flask приложения!"

echo "🔍 Статус сервисов:"
sudo systemctl status nginx --no-pager -l
echo
sudo systemctl status firewalld --no-pager -l

echo
echo "🌐 Тест локального подключения:"
curl -I http://localhost/ || warning "Локальное подключение не работает"

echo
echo "🎉 Настройка завершена успешно!"
echo "   Скрипт выполнен пользователем: $CURRENT_USER"
echo "   Теперь добавьте SSH ключ и запустите деплой из GitLab"

# Показываем команду для добавления SSH ключа
echo
echo "💡 Быстрое добавление SSH ключа:"
echo "   sudo nano /home/$DEPLOY_USER/.ssh/authorized_keys"
echo "   (вставьте содержимое вашего публичного ключа)"
