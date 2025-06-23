#!/bin/bash

# Скрипт для завершения деплоя Flask Helpdesk приложения
# Запускать с sudo правами: sudo bash complete_deployment.sh

set -e

echo "🚀 Завершение деплоя Flask Helpdesk..."

# Проверяем, что мы запущены с sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен с sudo правами"
    echo "Использование: sudo bash complete_deployment.sh"
    exit 1
fi

# Проверяем существование директории приложения
if [ ! -d "/var/www/flask_helpdesk" ]; then
    echo "❌ Директория /var/www/flask_helpdesk не найдена"
    exit 1
fi

echo "1. Копирование systemd сервиса..."
if [ -f "/var/www/flask_helpdesk/flask-helpdesk.service" ]; then
    cp /var/www/flask_helpdesk/flask-helpdesk.service /etc/systemd/system/
    echo "✅ Сервис скопирован"
else
    echo "⚠️  Файл flask-helpdesk.service не найден"
fi

echo "2. Перезагрузка systemd daemon..."
systemctl daemon-reload
echo "✅ Daemon перезагружен"

echo "3. Включение автозапуска сервиса..."
systemctl enable flask-helpdesk
echo "✅ Автозапуск включен"

echo "4. Установка правильных прав доступа..."
chown -R www-data:www-data /var/www/flask_helpdesk/
echo "✅ Права установлены"

echo "5. Остановка старого процесса (если запущен)..."
systemctl stop flask-helpdesk 2>/dev/null || echo "Сервис не был запущен"

echo "6. Запуск нового сервиса..."
systemctl start flask-helpdesk
echo "✅ Сервис запущен"

echo "7. Проверка статуса сервиса..."
if systemctl is-active --quiet flask-helpdesk; then
    echo "✅ Сервис успешно запущен и работает"
    systemctl status flask-helpdesk --no-pager -l
else
    echo "❌ Сервис не запустился. Проверьте логи:"
    journalctl -u flask-helpdesk --no-pager -l -n 20
    exit 1
fi

echo ""
echo "🎉 Деплой завершен успешно!"
echo "🌐 Приложение должно быть доступно по адресу: https://its.tez-tour.com"
echo ""
echo "Полезные команды для управления:"
echo "  sudo systemctl status flask-helpdesk    # Проверить статус"
echo "  sudo systemctl restart flask-helpdesk   # Перезапустить"
echo "  sudo systemctl stop flask-helpdesk      # Остановить"
echo "  sudo journalctl -u flask-helpdesk -f    # Просмотр логов в реальном времени"
