#!/bin/bash

# Скрипт для диагностики ошибок Flask Helpdesk
# Запускайте от имени пользователя yvarslavan

echo "🔍 Диагностика ошибок Flask Helpdesk..."

# Проверяем логи приложения
echo "📋 Логи приложения:"
if [ -f "logs/error.log" ]; then
    tail -n 20 logs/error.log
else
    echo "❌ Файл logs/error.log не найден"
fi

# Проверяем логи systemd
echo -e "\n📋 Логи systemd:"
sudo journalctl -u flask-helpdesk --no-pager -n 20

# Проверяем логи Nginx
echo -e "\n📋 Логи Nginx:"
sudo tail -n 20 /var/log/nginx/flask-helpdesk-error.log

# Проверяем конфигурацию Nginx
echo -e "\n📋 Проверка конфигурации Nginx:"
sudo nginx -t

# Проверяем статус сокета
echo -e "\n📋 Проверка статуса сокета:"
if [ -S "/run/gunicorn/gunicorn.sock" ]; then
    echo "✅ Сокет gunicorn существует"
    ls -la /run/gunicorn/gunicorn.sock
else
    echo "❌ Сокет gunicorn не найден"
    echo "📋 Проверяем директорию /run/gunicorn:"
    ls -la /run/gunicorn/
    echo "📋 Проверяем процессы gunicorn:"
    ps aux | grep gunicorn
fi

# Проверяем переменные окружения
echo -e "\n📋 Переменные окружения:"
cd /opt/www/its.teztour.com
source .env.production 2>/dev/null || echo "⚠️ Не удалось загрузить .env.production"
echo "FLASK_ENV: $FLASK_ENV"
echo "WTF_CSRF_ENABLED: $WTF_CSRF_ENABLED"
echo "SESSION_TYPE: $SESSION_TYPE"

# Проверяем версию Python и модулей
echo -e "\n📋 Версия Python и модулей:"
/opt/www/its.teztour.com/venv/bin/python --version
/opt/www/its.teztour.com/venv/bin/pip list | grep -E "(Flask|WTF|Flask-WTF|Flask-Session)"

echo -e "\n🎉 Диагностика завершена!"
