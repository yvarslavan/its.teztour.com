#!/bin/bash
# Экстренные команды для исправления прав доступа на сервере
# Выполнять на сервере ubuntu@10.7.74.252

echo "🚨 ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА"
echo "======================================"

# Проверить текущие права
echo "🔍 Проверка текущих прав..."
ls -la /var/www/flask_helpdesk/ | head -10
echo "Владелец директории:"
stat -c '%U:%G' /var/www/flask_helpdesk 2>/dev/null || echo "Директория не существует"

# Остановить сервис
echo "🔄 Остановка сервиса..."
sudo systemctl stop flask-helpdesk 2>/dev/null || echo "Сервис не запущен"

# Изменить владельца (директория уже существует)
echo "👤 Изменение владельца..."
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk

# Установить права
echo "🔐 Установка прав доступа..."
sudo chmod -R 755 /var/www/flask_helpdesk

# Очистить проблемные файлы
echo "🧹 Очистка проблемных файлов..."
sudo rm -rf /var/www/flask_helpdesk/flask_session/* 2>/dev/null || true
sudo rm -rf /var/www/flask_helpdesk/__pycache__ 2>/dev/null || true
sudo find /var/www/flask_helpdesk -name "*.pyc" -delete 2>/dev/null || true
sudo rm -rf /var/www/flask_helpdesk/venv 2>/dev/null || true

# Пересоздать только пустые служебные директории
echo "📁 Пересоздание служебных директорий..."
sudo mkdir -p /var/www/flask_helpdesk/flask_session
sudo mkdir -p /var/www/flask_helpdesk/logs

# Установить права для всех директорий
echo "🔐 Финальная настройка прав..."
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk
sudo chmod -R 755 /var/www/flask_helpdesk

# Запустить сервис обратно
echo "🚀 Запуск сервиса..."
sudo systemctl start flask-helpdesk

# Проверить результат
echo "✅ Проверка результата..."
ls -la /var/www/flask_helpdesk/ | head -5
echo "Владелец директории:"
stat -c '%U:%G' /var/www/flask_helpdesk

# Тест записи
echo "📝 Тест записи..."
if touch /var/www/flask_helpdesk/test_write 2>/dev/null; then
    rm /var/www/flask_helpdesk/test_write
    echo "✅ Запись работает!"
else
    echo "❌ Проблемы с записью остались"
fi

# Проверить статус сервиса
echo "📊 Проверка статуса сервиса..."
sudo systemctl status flask-helpdesk --no-pager -l

echo "======================================"
echo "✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "Теперь можно запустить GitLab CI/CD pipeline"
