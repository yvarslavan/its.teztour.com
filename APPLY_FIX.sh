#!/bin/bash
# Скрипт для автоматического применения исправлений конфигурации WSL

set -e  # Прервать выполнение при ошибке

echo "=========================================="
echo "  Исправление конфигурации WSL для VPN"
echo "=========================================="
echo ""

# Проверка что мы в WSL
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "⚠️  Этот скрипт предназначен для WSL"
    echo "    Для Windows используйте: python3 setup_env.py development"
    exit 1
fi

echo "✅ Обнаружена WSL"
echo ""

# Проверка доступности VPN
echo "🔍 Проверка доступности VPN серверов..."
echo ""

if ping -c 3 -W 2 vpn.teztour.com > /dev/null 2>&1; then
    echo "✅ VPN доступен (vpn.teztour.com)"
else
    echo "❌ VPN недоступен!"
    echo ""
    echo "Пожалуйста, подключите Cisco Secure Client в Windows"
    echo "и убедитесь что выполнена команда в PowerShell:"
    echo ""
    echo "Get-NetIPInterface | Where-Object {\$_.InterfaceAlias -Match \"vEthernet (WSL)\"} | Set-NetIPInterface -InterfaceMetric 6000"
    echo ""
    exit 1
fi

echo ""
echo "🔍 Проверка доступности MySQL серверов..."
echo ""

# Проверка helpdesk
if ping -c 2 -W 2 helpdesk.teztour.com > /dev/null 2>&1; then
    echo "✅ helpdesk.teztour.com доступен"
else
    echo "⚠️  helpdesk.teztour.com недоступен (но продолжаем)"
fi

# Проверка quality
if ping -c 2 -W 2 quality.teztour.com > /dev/null 2>&1; then
    echo "✅ quality.teztour.com доступен"
else
    echo "⚠️  quality.teztour.com недоступен (но продолжаем)"
fi

echo ""
echo "🔧 Создание конфигурации для WSL..."
echo ""

# Запуск скрипта настройки
python3 setup_wsl_config.py

echo ""
echo "=========================================="
echo "  ✅ Конфигурация создана успешно!"
echo "=========================================="
echo ""
echo "🚀 Теперь можно запустить приложение:"
echo "   python3 app.py"
echo ""
echo "📋 Проверка конфигурации:"
echo "   grep -E 'MYSQL.*HOST' .env"
echo ""

