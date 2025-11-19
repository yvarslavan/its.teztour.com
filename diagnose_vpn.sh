#!/bin/bash
# Диагностика VPN подключения в WSL

echo "=========================================="
echo "  🔍 Диагностика VPN в WSL"
echo "=========================================="
echo ""

# Проверка что мы в WSL
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "⚠️  Не обнаружена WSL"
    exit 1
fi

echo "✅ WSL обнаружена"
echo ""

# 1. Проверка VPN сервера
echo "1️⃣ Проверка VPN сервера (vpn.teztour.com)..."
if ping -c 3 -W 2 vpn.teztour.com > /dev/null 2>&1; then
    echo "   ✅ VPN сервер доступен"
else
    echo "   ❌ VPN сервер НЕдоступен!"
    echo "   Подключите Cisco Secure Client в Windows"
    exit 1
fi

echo ""

# 2. Проверка helpdesk.teztour.com
echo "2️⃣ Проверка helpdesk.teztour.com..."
if ping -c 3 -W 2 helpdesk.teztour.com > /dev/null 2>&1; then
    echo "   ✅ helpdesk.teztour.com доступен"
    # Получить IP
    IP=$(ping -c 1 helpdesk.teztour.com | grep -oP '\(\K[0-9.]+(?=\))')
    echo "   📍 IP: $IP"
else
    echo "   ❌ helpdesk.teztour.com НЕдоступен!"
    echo ""
    echo "   Проверьте DNS:"
    nslookup helpdesk.teztour.com 2>&1 | head -10
fi

echo ""

# 3. Проверка quality.teztour.com
echo "3️⃣ Проверка quality.teztour.com..."
if ping -c 3 -W 2 quality.teztour.com > /dev/null 2>&1; then
    echo "   ✅ quality.teztour.com доступен"
    IP=$(ping -c 1 quality.teztour.com | grep -oP '\(\K[0-9.]+(?=\))')
    echo "   📍 IP: $IP"
else
    echo "   ❌ quality.teztour.com НЕдоступен!"
    echo ""
    echo "   Проверьте DNS:"
    nslookup quality.teztour.com 2>&1 | head -10
fi

echo ""

# 4. Проверка портов MySQL
echo "4️⃣ Проверка портов MySQL (3306)..."

# helpdesk
if timeout 3 bash -c "</dev/tcp/helpdesk.teztour.com/3306" 2>/dev/null; then
    echo "   ✅ helpdesk.teztour.com:3306 доступен"
else
    echo "   ❌ helpdesk.teztour.com:3306 НЕдоступен!"
    echo "   Проверьте firewall или VPN маршруты"
fi

# quality
if timeout 3 bash -c "</dev/tcp/quality.teztour.com/3306" 2>/dev/null; then
    echo "   ✅ quality.teztour.com:3306 доступен"
else
    echo "   ❌ quality.teztour.com:3306 НЕдоступен!"
    echo "   Проверьте firewall или VPN маршруты"
fi

echo ""

# 5. Проверка маршрутов
echo "5️⃣ Проверка маршрутов к серверам..."
echo ""
echo "   Маршрут к helpdesk.teztour.com:"
ip route get $(ping -c 1 helpdesk.teztour.com 2>/dev/null | grep -oP '\(\K[0-9.]+(?=\))' | head -1) 2>/dev/null || echo "   ❌ Не удалось получить маршрут"

echo ""

# 6. Проверка DNS
echo "6️⃣ Проверка DNS настроек..."
echo "   /etc/resolv.conf:"
cat /etc/resolv.conf | grep -v "^#" | grep -v "^$"

echo ""

# 7. Проверка метрики WSL
echo "7️⃣ Рекомендация: проверить метрику WSL в Windows PowerShell (от администратора):"
echo ""
echo "   Get-NetIPInterface | Where-Object {\$_.InterfaceAlias -Match \"vEthernet (WSL)\"}"
echo ""
echo "   Если метрика не 6000, выполните:"
echo "   Get-NetIPInterface | Where-Object {\$_.InterfaceAlias -Match \"vEthernet (WSL)\"} | Set-NetIPInterface -InterfaceMetric 6000"

echo ""
echo "=========================================="
echo "  Диагностика завершена"
echo "=========================================="

