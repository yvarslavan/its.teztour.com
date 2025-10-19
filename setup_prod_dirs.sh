#!/bin/bash

# Скрипт для создания и настройки директорий для продакшена
# Запускайте с правами sudo: sudo ./setup_prod_dirs.sh

echo "Настройка директорий для продакшена Flask Helpdesk..."

# Определяем пользователя и группу
APP_USER="yvarslavan"
APP_GROUP="yvarslavan"

# Создаем директорию для сессий Flask
mkdir -p /tmp/flask_sessions
chmod 755 /tmp/flask_sessions
chown $APP_USER:$APP_GROUP /tmp/flask_sessions
echo "✅ Директория для сессий создана: /tmp/flask_sessions (владелец: $APP_USER)"

# Создаем директорию для логов
mkdir -p /var/www/flask_helpdesk/logs
chmod 755 /var/www/flask_helpdesk/logs
chown $APP_USER:$APP_GROUP /var/www/flask_helpdesk/logs
echo "✅ Директория для логов создана: /var/www/flask_helpdesk/logs (владелец: $APP_USER)"

# Создаем директорию для базы данных SQLite
mkdir -p /var/www/flask_helpdesk/blog/db
chmod 755 /var/www/flask_helpdesk/blog/db
chown $APP_USER:$APP_GROUP /var/www/flask_helpdesk/blog/db
echo "✅ Директория для базы данных создана: /var/www/flask_helpdesk/blog/db (владелец: $APP_USER)"

# Проверяем права доступа к директории gunicorn
mkdir -p /run/gunicorn
chmod 755 /run/gunicorn
chown $APP_USER:$APP_GROUP /run/gunicorn
echo "✅ Директория для gunicorn создана: /run/gunicorn (владелец: $APP_USER)"

echo "🎉 Настройка директорий завершена!"
