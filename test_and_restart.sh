#!/bin/bash

# Скрипт для перезапуска сервиса и тестирования CSRF
# Запускайте от имени пользователя yvarslavan

echo "🔄 Перезапускаем сервис flask-helpdesk..."
sudo systemctl daemon-reload
sudo systemctl restart flask-helpdesk

# Ждем несколько секунд для запуска сервиса
sleep 3

# Проверяем статус
echo "📊 Проверяем статус сервиса..."
sudo systemctl status flask-helpdesk --no-pager

# Тестируем CSRF
echo "🧪 Тестируем CSRF..."
/opt/www/its.teztour.com/venv/bin/python test_csrf.py

echo "🎉 Тестирование завершено!"
