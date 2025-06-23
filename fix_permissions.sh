#!/bin/bash

# =======================================================
# СКРИПТ ИСПРАВЛЕНИЯ ПРАВ ДОСТУПА ДЛЯ FLASK HELPDESK
# Версия: 2.0 - Обновлено для пользователя deploy
# Дата: 2024-12-27
# =======================================================

set -e

echo "🔧 Исправление прав доступа для Flask Helpdesk (пользователь deploy)"
echo "=================================================================="

# Проверяем, что скрипт запущен с правами sudo
if [[ $EUID -eq 0 ]]; then
    echo "✅ Скрипт запущен с правами администратора"
else
    echo "❌ Этот скрипт должен быть запущен с sudo"
    echo "Использование: sudo bash fix_permissions.sh"
    exit 1
fi

# Проверяем существование пользователя deploy
if ! id "deploy" &>/dev/null; then
    echo "❌ Пользователь 'deploy' не существует!"
    echo "Создайте пользователя командой: sudo adduser deploy"
    exit 1
else
    echo "✅ Пользователь 'deploy' найден"
fi

# Переменные
DEPLOY_USER="deploy"
WEB_GROUP="www-data"
APP_PATH="/var/www/flask_helpdesk"
BACKUP_PATH="/var/backups/flask_helpdesk"
LOG_PATH="/var/log/flask_helpdesk"

echo "📁 Создание необходимых директорий..."

# Создаем основные директории
mkdir -p "$APP_PATH"
mkdir -p "$BACKUP_PATH"
mkdir -p "$LOG_PATH"

echo "✅ Директории созданы"

echo "👤 Настройка пользователя и групп..."

# Добавляем пользователя deploy в группу www-data
usermod -a -G "$WEB_GROUP" "$DEPLOY_USER"

# Проверяем группы пользователя
echo "📋 Группы пользователя $DEPLOY_USER:"
groups "$DEPLOY_USER"

echo "🔐 Настройка прав доступа..."

# Устанавливаем владельца и права для основной директории приложения
chown -R "$DEPLOY_USER:$WEB_GROUP" "$APP_PATH"
chmod -R 755 "$APP_PATH"
chmod -R g+w "$APP_PATH"

# Устанавливаем права для директории бэкапов
chown -R "$DEPLOY_USER:$WEB_GROUP" "$BACKUP_PATH"
chmod -R 755 "$BACKUP_PATH"
chmod -R g+w "$BACKUP_PATH"

# Устанавливаем права для директории логов
chown -R "$DEPLOY_USER:$WEB_GROUP" "$LOG_PATH"
chmod -R 755 "$LOG_PATH"
chmod -R g+w "$LOG_PATH"

echo "🔒 Настройка ACL (расширенных прав доступа)..."

# Проверяем поддержку ACL
if command -v setfacl &> /dev/null; then
    # Устанавливаем ACL для гарантированного доступа
    setfacl -R -m u:"$DEPLOY_USER":rwx "$APP_PATH"
    setfacl -R -m g:"$WEB_GROUP":rwx "$APP_PATH"
    setfacl -R -d -m u:"$DEPLOY_USER":rwx "$APP_PATH"
    setfacl -R -d -m g:"$WEB_GROUP":rwx "$APP_PATH"

    setfacl -R -m u:"$DEPLOY_USER":rwx "$BACKUP_PATH"
    setfacl -R -m g:"$WEB_GROUP":rwx "$BACKUP_PATH"

    setfacl -R -m u:"$DEPLOY_USER":rwx "$LOG_PATH"
    setfacl -R -m g:"$WEB_GROUP":rwx "$LOG_PATH"

    echo "✅ ACL настроены"
else
    echo "⚠️ ACL не поддерживается, используем стандартные права"
fi

echo "🧪 Тестирование прав доступа..."

# Тестируем запись от имени пользователя deploy
TEST_FILE="$APP_PATH/test_deploy_access.tmp"

# Создаем тестовый файл от имени deploy
if sudo -u "$DEPLOY_USER" touch "$TEST_FILE" 2>/dev/null; then
    echo "✅ Пользователь $DEPLOY_USER может создавать файлы в $APP_PATH"
    # Удаляем тестовый файл
    rm -f "$TEST_FILE"
else
    echo "❌ Пользователь $DEPLOY_USER НЕ может создавать файлы в $APP_PATH"
    echo "🔧 Попытка исправления..."

    # Дополнительное исправление прав
    chmod 775 "$APP_PATH"
    chown "$DEPLOY_USER:$WEB_GROUP" "$APP_PATH"

    # Повторное тестирование
    if sudo -u "$DEPLOY_USER" touch "$TEST_FILE" 2>/dev/null; then
        echo "✅ Права исправлены успешно"
        rm -f "$TEST_FILE"
    else
        echo "❌ Не удалось исправить права автоматически"
        echo "Требуется ручная настройка"
        exit 1
    fi
fi

echo "📊 Итоговые права доступа:"
echo "========================="
ls -la "$APP_PATH" | head -5
echo ""
ls -ld "$APP_PATH" "$BACKUP_PATH" "$LOG_PATH"

echo ""
echo "✅ Исправление прав доступа завершено успешно!"
echo ""
echo "📋 Результат:"
echo "  • Пользователь: $DEPLOY_USER"
echo "  • Группа: $WEB_GROUP"
echo "  • Директория приложения: $APP_PATH"
echo "  • Директория бэкапов: $BACKUP_PATH"
echo "  • Директория логов: $LOG_PATH"
echo "  • Права: 755 (rwxr-xr-x) с групповой записью"
echo ""
echo "🚀 Теперь можно запускать GitLab CI/CD pipeline!"
