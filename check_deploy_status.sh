#!/bin/bash

# Скрипт проверки статуса деплоя Flask Helpdesk
# Версия: 1.0

echo "🔍 Проверка статуса деплоя Flask Helpdesk"
echo "========================================="

# Проверяем пользователя deploy
echo "👤 Проверка пользователя deploy:"
if id "deploy" &>/dev/null; then
    echo "✅ Пользователь 'deploy' существует"
    echo "📋 Группы: $(groups deploy)"
else
    echo "❌ Пользователь 'deploy' не найден"
fi

echo ""

# Проверяем директории
echo "📁 Проверка директорий:"
directories=(
    "/var/www/flask_helpdesk"
    "/var/backups/flask_helpdesk"
    "/var/log/flask_helpdesk"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir - существует"
        echo "   Владелец: $(stat -c '%U:%G' "$dir")"
        echo "   Права: $(stat -c '%a' "$dir")"
    else
        echo "❌ $dir - не найдена"
    fi
done

echo ""

# Проверяем SSH ключи
echo "🔐 Проверка SSH настроек:"
if [ -d "/home/deploy/.ssh" ]; then
    echo "✅ Директория .ssh существует"
    if [ -f "/home/deploy/.ssh/authorized_keys" ]; then
        echo "✅ Файл authorized_keys найден"
        echo "   Права: $(stat -c '%a' /home/deploy/.ssh/authorized_keys)"
        echo "   Количество ключей: $(wc -l < /home/deploy/.ssh/authorized_keys)"
    else
        echo "❌ Файл authorized_keys не найден"
    fi
else
    echo "❌ Директория .ssh не найдена"
fi

echo ""

# Проверяем сервис Flask
echo "🚀 Проверка сервиса Flask Helpdesk:"
if systemctl is-active --quiet flask-helpdesk; then
    echo "✅ Сервис flask-helpdesk запущен"
    echo "   Статус: $(systemctl is-active flask-helpdesk)"
    echo "   Включен при загрузке: $(systemctl is-enabled flask-helpdesk)"
else
    echo "❌ Сервис flask-helpdesk не запущен"
    echo "   Статус: $(systemctl is-active flask-helpdesk)"
fi

echo ""

# Проверяем веб-интерфейс
echo "🌐 Проверка веб-интерфейса:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    echo "✅ Веб-интерфейс доступен (HTTP 200)"
else
    echo "❌ Веб-интерфейс недоступен"
    echo "   HTTP код: $(curl -s -o /dev/null -w "%{http_code}" http://localhost)"
fi

echo ""

# Проверяем права записи
echo "🧪 Тест прав записи:"
TEST_FILE="/var/www/flask_helpdesk/deploy_test.tmp"

if sudo -u deploy touch "$TEST_FILE" 2>/dev/null; then
    echo "✅ Пользователь deploy может создавать файлы"
    sudo rm -f "$TEST_FILE"
else
    echo "❌ Пользователь deploy НЕ может создавать файлы"
fi

echo ""

# Показываем последние логи
echo "📋 Последние логи сервиса (последние 5 строк):"
if systemctl is-active --quiet flask-helpdesk; then
    journalctl -u flask-helpdesk --no-pager -n 5
else
    echo "Сервис не запущен, логи недоступны"
fi

echo ""
echo "🏁 Проверка завершена"
echo "===================="

# Итоговый статус
if id "deploy" &>/dev/null && [ -d "/var/www/flask_helpdesk" ] && [ -f "/home/deploy/.ssh/authorized_keys" ]; then
    echo "✅ ГОТОВ К ДЕПЛОЮ"
    echo "Можно запускать GitLab CI/CD pipeline"
else
    echo "❌ НЕ ГОТОВ К ДЕПЛОЮ"
    echo "Требуется дополнительная настройка"
    echo ""
    echo "📋 Рекомендуемые действия:"
    echo "1. Выполните: sudo bash fix_permissions.sh"
    echo "2. Настройте SSH ключи для пользователя deploy"
    echo "3. Проверьте переменные GitLab CI/CD"
fi
