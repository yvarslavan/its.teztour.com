#!/bin/bash
# Скрипт для создания SSH туннеля к MySQL серверу

# Настройки (замените на ваши)
SSH_USER="your_username"
SSH_HOST="helpdesk.teztour.com"  # или IP сервера
SSH_PORT=22
LOCAL_MYSQL_PORT=3306
REMOTE_MYSQL_HOST="localhost"  # MySQL на удаленном сервере
REMOTE_MYSQL_PORT=3306

echo "🔌 Создание SSH туннеля для MySQL..."
echo "   Локальный порт: $LOCAL_MYSQL_PORT"
echo "   Удаленный: $REMOTE_MYSQL_HOST:$REMOTE_MYSQL_PORT через $SSH_USER@$SSH_HOST"
echo ""
echo "Команда для запуска:"
echo "ssh -L $LOCAL_MYSQL_PORT:$REMOTE_MYSQL_HOST:$REMOTE_MYSQL_PORT $SSH_USER@$SSH_HOST -N"
echo ""
echo "После создания туннеля, в .env укажите:"
echo "MYSQL_HOST=localhost"
echo ""
echo "⚠️  Оставьте терминал открытым, пока работаете с приложением!"

