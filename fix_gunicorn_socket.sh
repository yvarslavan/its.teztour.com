#!/bin/bash

# Скрипт для исправления проблем с сокетом gunicorn
# Запускайте с правами sudo: sudo ./fix_gunicorn_socket.sh

echo "🔧 Исправление проблем с сокетом gunicorn..."

# Проверяем и создаем директорию для сокета
if [ ! -d "/run/gunicorn" ]; then
    mkdir -p /run/gunicorn
    echo "✅ Создана директория /run/gunicorn"
fi

# Устанавливаем права для директории сокета
chmod 755 /run/gunicorn
chown yvarslavan:yvarslavan /run/gunicorn
echo "✅ Установлены права для /run/gunicorn"

# Перезапускаем сервис
echo "🔄 Перезапускаем сервис flask-helpdesk..."
systemctl daemon-reload
systemctl restart flask-helpdesk

# Ждем несколько секунд для запуска сервиса
sleep 3

# Проверяем статус сокета
if [ -S "/run/gunicorn/gunicorn.sock" ]; then
    echo "✅ Сокет gunicorn создан успешно"
    ls -la /run/gunicorn/gunicorn.sock
else
    echo "❌ Проблема с созданием сокета остается"
    echo "📋 Проверяем процессы gunicorn:"
    ps aux | grep gunicorn
    echo "📋 Проверяем логи:"
    journalctl -u flask-helpdesk --no-pager -n 20
fi

echo "🎉 Исправление завершено!"
