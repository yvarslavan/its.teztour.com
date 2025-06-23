#!/bin/bash

echo "🔧 Исправление Flask Helpdesk сервиса"
echo "======================================"

# Остановка сервиса
echo "1. Остановка сервиса..."
sudo systemctl stop flask-helpdesk.service

# Переход в директорию проекта
cd /var/www/flask_helpdesk

# Проверка наличия Python3
echo "2. Проверка Python3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установка..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Создание виртуального окружения
echo "3. Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "   Удаление старого venv..."
    rm -rf venv
fi

python3 -m venv venv
echo "   ✅ Виртуальное окружение создано"

# Активация и установка зависимостей
echo "4. Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Зависимости установлены"

# Проверка прав доступа
echo "5. Настройка прав доступа..."
sudo chown -R www-data:www-data /var/www/flask_helpdesk
sudo chmod +x /var/www/flask_helpdesk/venv/bin/python
echo "   ✅ Права настроены"

# Проверка wsgi.py
echo "6. Проверка wsgi.py..."
if [ -f "wsgi.py" ]; then
    echo "   ✅ wsgi.py найден"
else
    echo "   ❌ wsgi.py не найден!"
    exit 1
fi

# Перезагрузка systemd
echo "7. Перезагрузка systemd..."
sudo systemctl daemon-reload

# Запуск сервиса
echo "8. Запуск сервиса..."
sudo systemctl start flask-helpdesk.service

# Проверка статуса
echo "9. Проверка статуса..."
sleep 3
sudo systemctl status flask-helpdesk.service --no-pager

echo ""
echo "🎉 Исправление завершено!"
echo ""
echo "Для проверки логов используйте:"
echo "sudo journalctl -u flask-helpdesk.service -f"
echo ""
echo "Для проверки статуса:"
echo "sudo systemctl status flask-helpdesk.service"
