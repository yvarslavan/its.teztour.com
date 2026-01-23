# Настройка порт-прокси для WSL
# Запускать в PowerShell от администратора

Write-Host "=========================================="
Write-Host "  Настройка порт-прокси для WSL"
Write-Host "=========================================="
Write-Host ""

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ Требуются права администратора!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Запустите PowerShell от имени администратора и повторите."
    exit 1
}

Write-Host "✅ Права администратора подтверждены"
Write-Host ""

# Удаление старых правил
Write-Host "🧹 Удаление старых правил порт-прокси..."
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306 2>$null
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307 2>$null
Write-Host "   ✅ Старые правила удалены (если были)"
Write-Host ""

# Добавление новых правил
Write-Host "➕ Добавление новых правил порт-прокси..."

# Правило для helpdesk (порт 3306)
Write-Host "   Настройка helpdesk.teztour.com -> 127.0.0.1:3306..."
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306

# Правило для quality (порт 3307)
Write-Host "   Настройка quality.teztour.com -> 127.0.0.1:3307..."
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306

Write-Host ""
Write-Host "✅ Порт-прокси настроен!"
Write-Host ""

# Показать текущие правила
Write-Host "📋 Текущие правила порт-прокси:"
Write-Host ""
netsh interface portproxy show all

Write-Host ""
Write-Host "=========================================="
Write-Host "  Настройка завершена"
Write-Host "=========================================="
Write-Host ""
Write-Host "Теперь в WSL нужно изменить конфигурацию:"
Write-Host ""
Write-Host "bash setup_portproxy_env.sh"
Write-Host ""

