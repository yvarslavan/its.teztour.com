#!/bin/bash

echo "⚡ Быстрое исправление Flask Helpdesk"
echo "==================================="

# Остановка сервиса
sudo systemctl stop flask-helpdesk.service

# Переход в директорию
cd /var/www/flask_helpdesk

# Создание простого venv
python3 -m venv venv

# Установка базовых пакетов
venv/bin/pip install flask gunicorn

# Установка из requirements.txt
venv/bin/pip install -r requirements.txt

# Права доступа
sudo chown -R www-data:www-data /var/www/flask_helpdesk
sudo chmod +x venv/bin/python

# Перезапуск
sudo systemctl daemon-reload
sudo systemctl start flask-helpdesk.service

echo "✅ Готово! Проверьте статус:"
echo "sudo systemctl status flask-helpdesk.service"
