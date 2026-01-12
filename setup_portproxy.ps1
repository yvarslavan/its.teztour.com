# Настройка порт-прокси для Windows -> VPN
# Запускать в PowerShell от администратора

Write-Host "=========================================="
Write-Host "  Настройка порт-прокси для HelpDesk (VPN)"
Write-Host "=========================================="
Write-Host ""

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Требуются права администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора и повторите."
    exit 1
}

Write-Host "✅ Права администратора подтверждены"

# Удаление всех старых правил для чистоты
Write-Host "🧹 Очистка старых правил..."
netsh interface portproxy reset
Write-Host "   ✅ Правила сброшены"

# Настройка правил согласно .env
Write-Host "➕ Добавление правил..."

# MySQL HelpDesk
Write-Host "   MySQL HelpDesk: 127.0.0.1:13306 -> helpdesk.teztour.com:3306"
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=13306 connectaddress=helpdesk.teztour.com connectport=3306

# MySQL Quality
Write-Host "   MySQL Quality:  127.0.0.1:13307 -> quality.teztour.com:3306"
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=13307 connectaddress=quality.teztour.com connectport=3306

# MySQL VoIP (Предполагаемый хост, если он в VPN)
Write-Host "   MySQL VoIP:     127.0.0.1:13308 -> 10.7.12.33:3306 (проверьте IP!)"
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=13308 connectaddress=10.7.12.33 connectport=3306

# Oracle CRM
Write-Host "   Oracle CRM:     127.0.0.1:11521 -> 10.7.23.4:1521"
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=11521 connectaddress=10.7.23.4 connectport=1521

Write-Host ""
Write-Host "📋 Текущая таблица перенаправления:"
netsh interface portproxy show all

Write-Host ""
Write-Host "🚀 ПРОВЕРКА: Попробуйте сейчас обновить страницу в браузере."
Write-Host "Если не работает, проверьте, что Cisco AnyConnect подключен."


