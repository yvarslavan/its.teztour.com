#!/bin/bash

# 🗑️ Скрипт удаления GitHub Self-Hosted Runner
# Использование: ./remove_runner.sh [GITHUB_TOKEN]

set -e

echo "🗑️ Удаление GitHub Self-Hosted Runner"
echo "======================================"

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "⚠️ Использование: $0 <GITHUB_TOKEN>"
    echo "💡 Получите токен: GitHub → Settings → Developer settings → Personal access tokens"
    exit 1
fi

GITHUB_TOKEN=$1
RUNNER_NAME="HelpDesk_runner"

echo "🔍 Поиск runner сервисов..."
SERVICES=$(sudo systemctl list-units --type=service | grep -i actions.runner | awk '{print $1}' || true)

if [ -n "$SERVICES" ]; then
    echo "📋 Найденные сервисы:"
    echo "$SERVICES"

    for service in $SERVICES; do
        echo "🛑 Остановка сервиса: $service"
        sudo systemctl stop "$service" || true

        echo "❌ Отключение автозапуска: $service"
        sudo systemctl disable "$service" || true

        echo "🗑️ Удаление файла сервиса: $service"
        sudo rm -f "/etc/systemd/system/$service" || true
    done

    echo "🔄 Обновление systemd..."
    sudo systemctl daemon-reload
else
    echo "✅ Сервисы runner не найдены"
fi

echo ""
echo "🔍 Поиск папок runner..."
RUNNER_PATHS=$(find /home /opt -name "actions-runner" -type d 2>/dev/null || true)

if [ -n "$RUNNER_PATHS" ]; then
    echo "📁 Найденные папки:"
    echo "$RUNNER_PATHS"

    for path in $RUNNER_PATHS; do
        echo "📂 Обработка папки: $path"

        if [ -f "$path/config.sh" ]; then
            echo "🔧 Удаление конфигурации runner..."
            cd "$path"

            # Остановка runner
            if [ -f "./svc.sh" ]; then
                sudo ./svc.sh stop || true
                sudo ./svc.sh uninstall || true
            fi

            # Удаление конфигурации
            if [ -f "./config.sh" ]; then
                ./config.sh remove --token "$GITHUB_TOKEN" || echo "⚠️ Не удалось удалить конфигурацию"
            fi
        fi

        echo "🗑️ Удаление папки: $path"
        sudo rm -rf "$path"
    done
else
    echo "✅ Папки runner не найдены"
fi

echo ""
echo "🔍 Завершение процессов runner..."
RUNNER_PROCESSES=$(ps aux | grep -i runner | grep -v grep | awk '{print $2}' || true)

if [ -n "$RUNNER_PROCESSES" ]; then
    echo "📋 Найденные процессы:"
    ps aux | grep -i runner | grep -v grep || true

    echo "🛑 Завершение процессов..."
    for pid in $RUNNER_PROCESSES; do
        sudo kill -9 "$pid" 2>/dev/null || true
    done
else
    echo "✅ Процессы runner не найдены"
fi

echo ""
echo "🧹 Очистка системы..."

# Удаление пользователя github-runner
if id "github-runner" &>/dev/null; then
    echo "👤 Удаление пользователя github-runner..."
    sudo userdel -r github-runner 2>/dev/null || true
fi

# Очистка логов
echo "📝 Очистка логов..."
sudo journalctl --vacuum-time=1d >/dev/null 2>&1 || true
sudo rm -f /var/log/actions-runner* 2>/dev/null || true

# Очистка временных файлов
echo "🗑️ Очистка временных файлов..."
sudo find /tmp -name "*runner*" -delete 2>/dev/null || true

echo ""
echo "✅ Удаление завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте GitHub Settings → Actions → Runners"
echo "2. Убедитесь, что '$RUNNER_NAME' удален из списка"
echo "3. Создайте новый runner по инструкции"
echo ""
echo "🔍 Проверка статуса:"
echo "   sudo systemctl list-units --type=service | grep actions.runner"
echo "   ps aux | grep -i runner | grep -v grep"
echo ""
