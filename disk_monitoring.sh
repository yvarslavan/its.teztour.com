#!/bin/bash

# 📊 Мониторинг и защита диска для GitHub Actions

# Проверка свободного места
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
FREE_SPACE=$(df -h / | tail -1 | awk '{print $4}')

echo "💾 Disk usage: ${DISK_USAGE}% (${FREE_SPACE} free)"

# Аварийная остановка при критическом заполнении
if [ "$DISK_USAGE" -gt 95 ]; then
    echo "🚨 CRITICAL: Disk usage > 95% - stopping runner"
    pkill -f Runner.Listener

    # Экстренная очистка
    rm -rf /home/github-actions/actions-runner/_work/* 2>/dev/null
    rm -rf /home/github-actions/actions-runner/_diag/*.log 2>/dev/null
    rm -rf /home/github-actions/.cache/* 2>/dev/null

    # Очистка логов приложения если они большие
    find /var/www -name "*.log" -size +50M -exec truncate -s 0 {} \; 2>/dev/null

    echo "🧹 Emergency cleanup completed"
    exit 1
fi

# Предупреждение при высоком заполнении
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️ WARNING: Disk usage > 90% - running cleanup"

    # Плановая очистка
    rm -rf /home/github-actions/actions-runner/_work/* 2>/dev/null
    rm -rf /home/github-actions/.cache/* 2>/dev/null

    # Очистка старых логов
    find /var/www -name "*.log" -size +100M -exec truncate -s 10M {} \; 2>/dev/null

    echo "🧹 Preventive cleanup completed"
fi

# Мониторинг больших файлов
echo "📁 Large files check:"
find /home/github-actions -size +100M -ls 2>/dev/null | head -3
find /var/www -name "*.log" -size +50M -ls 2>/dev/null | head -3

echo "✅ Monitoring completed"
