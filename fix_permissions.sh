#!/bin/bash

# =======================================================
# СКРИПТ ИСПРАВЛЕНИЯ ПРАВ ДОСТУПА ДЛЯ FLASK HELPDESK
# Версия: 1.0
# Дата: 2024-12-27
# =======================================================

echo "🔧 ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА ДЛЯ FLASK HELPDESK"
echo "=============================================="

# Проверка прав sudo
if [[ $EUID -eq 0 ]]; then
   echo "❌ Не запускайте этот скрипт от root. Используйте пользователя с sudo правами."
   exit 1
fi

# Переменные
DEPLOY_USER="deploy"
DEPLOY_PATH="/var/www/flask_helpdesk"
BACKUP_PATH="/var/backups/flask_helpdesk"
LOG_PATH="/var/log/flask_helpdesk"

echo "🔍 Проверка текущих прав доступа..."

# Показываем текущие права
echo "📁 Текущие права на $DEPLOY_PATH:"
ls -la $DEPLOY_PATH 2>/dev/null || echo "Директория не существует"

echo ""
echo "🔧 Исправляем права доступа..."

# Создаем директории если их нет
echo "📁 Создание директорий..."
sudo mkdir -p $DEPLOY_PATH
sudo mkdir -p $BACKUP_PATH
sudo mkdir -p $LOG_PATH

# Устанавливаем правильные права владельца
echo "👤 Настройка владельцев..."
sudo chown -R www-data:www-data $DEPLOY_PATH
sudo chown -R $DEPLOY_USER:$DEPLOY_USER $BACKUP_PATH
sudo chown -R www-data:www-data $LOG_PATH

# Устанавливаем правильные права доступа
echo "🔐 Настройка прав доступа..."
sudo chmod -R 755 $DEPLOY_PATH
sudo chmod -R 755 $BACKUP_PATH
sudo chmod -R 755 $LOG_PATH

# Добавляем пользователя deploy в группу www-data
echo "👥 Добавление пользователя $DEPLOY_USER в группу www-data..."
sudo usermod -aG www-data $DEPLOY_USER

# Настраиваем специальные права для деплоя
echo "⚙️ Настройка прав для деплоя..."

# Разрешаем группе www-data писать в директорию деплоя
sudo chmod g+w $DEPLOY_PATH
sudo chmod g+s $DEPLOY_PATH  # setgid - новые файлы наследуют группу

# Создаем ACL правила для более гибкого управления
if command -v setfacl &> /dev/null; then
    echo "🎯 Настройка ACL правил..."
    sudo setfacl -R -m g:www-data:rwx $DEPLOY_PATH
    sudo setfacl -R -m u:$DEPLOY_USER:rwx $DEPLOY_PATH
    sudo setfacl -R -d -m g:www-data:rwx $DEPLOY_PATH
    sudo setfacl -R -d -m u:$DEPLOY_USER:rwx $DEPLOY_PATH
    echo "✅ ACL правила установлены"
else
    echo "ℹ️ ACL не доступен, используем стандартные права"
fi

echo ""
echo "🔍 Проверка результата..."

# Проверяем права после изменения
echo "📁 Права после исправления:"
ls -la $DEPLOY_PATH

echo ""
echo "👤 Членство в группах пользователя $DEPLOY_USER:"
groups $DEPLOY_USER

echo ""
echo "🧪 Тест записи..."

# Тестируем запись от имени пользователя deploy
sudo -u $DEPLOY_USER touch $DEPLOY_PATH/test_write_access 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Пользователь $DEPLOY_USER может писать в $DEPLOY_PATH"
    sudo rm -f $DEPLOY_PATH/test_write_access
else
    echo "❌ Пользователь $DEPLOY_USER НЕ может писать в $DEPLOY_PATH"

    # Дополнительное исправление
    echo "🔧 Дополнительное исправление..."
    sudo chmod 775 $DEPLOY_PATH
    sudo chown $DEPLOY_USER:www-data $DEPLOY_PATH

    # Повторный тест
    sudo -u $DEPLOY_USER touch $DEPLOY_PATH/test_write_access 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ После дополнительного исправления: пользователь $DEPLOY_USER может писать"
        sudo rm -f $DEPLOY_PATH/test_write_access
    else
        echo "❌ Проблема не решена. Требуется ручная настройка."
        exit 1
    fi
fi

# Тестируем запись от имени www-data
sudo -u www-data touch $DEPLOY_PATH/test_www_data_access 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Пользователь www-data может писать в $DEPLOY_PATH"
    sudo rm -f $DEPLOY_PATH/test_www_data_access
else
    echo "❌ Пользователь www-data НЕ может писать в $DEPLOY_PATH"
fi

echo ""
echo "📋 ИТОГОВАЯ ИНФОРМАЦИЯ:"
echo "======================="
echo "📁 Путь деплоя: $DEPLOY_PATH"
echo "👤 Владелец: $(stat -c '%U:%G' $DEPLOY_PATH)"
echo "🔐 Права: $(stat -c '%a' $DEPLOY_PATH)"
echo "👥 Группы пользователя $DEPLOY_USER: $(groups $DEPLOY_USER)"

echo ""
echo "✅ ПРАВА ДОСТУПА ИСПРАВЛЕНЫ!"
echo "============================"
echo ""
echo "🚀 Теперь можно запустить деплой повторно в GitLab CI/CD"
echo ""
echo "💡 СОВЕТ: Если проблема повторится, выполните на сервере:"
echo "   sudo chmod 775 $DEPLOY_PATH"
echo "   sudo chown $DEPLOY_USER:www-data $DEPLOY_PATH"
