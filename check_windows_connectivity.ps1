# Проверка подключения к MySQL серверам из Windows

Write-Host "=========================================="
Write-Host "  Проверка подключения из Windows"
Write-Host "=========================================="
Write-Host ""

# Проверка helpdesk
Write-Host "1. Проверка helpdesk.teztour.com..."
$helpdesk = Test-NetConnection -ComputerName helpdesk.teztour.com -Port 3306 -WarningAction SilentlyContinue

if ($helpdesk.TcpTestSucceeded) {
    Write-Host "   ✅ helpdesk.teztour.com:3306 доступен из Windows" -ForegroundColor Green
    Write-Host "   📍 IP: $($helpdesk.RemoteAddress)"
} else {
    Write-Host "   ❌ helpdesk.teztour.com:3306 НЕдоступен из Windows" -ForegroundColor Red
}

Write-Host ""

# Проверка quality
Write-Host "2. Проверка quality.teztour.com..."
$quality = Test-NetConnection -ComputerName quality.teztour.com -Port 3306 -WarningAction SilentlyContinue

if ($quality.TcpTestSucceeded) {
    Write-Host "   ✅ quality.teztour.com:3306 доступен из Windows" -ForegroundColor Green
    Write-Host "   📍 IP: $($quality.RemoteAddress)"
} else {
    Write-Host "   ❌ quality.teztour.com:3306 НЕдоступен из Windows" -ForegroundColor Red
}

Write-Host ""
Write-Host "=========================================="

# Если оба доступны из Windows, предложить настроить порт-прокси
if ($helpdesk.TcpTestSucceeded -and $quality.TcpTestSucceeded) {
    Write-Host ""
    Write-Host "✅ Серверы доступны из Windows!"
    Write-Host ""
    Write-Host "РЕКОМЕНДАЦИЯ: Настроить порт-прокси для WSL:"
    Write-Host ""
    Write-Host "# Удалить старые правила (если есть):"
    Write-Host "netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306"
    Write-Host "netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307"
    Write-Host ""
    Write-Host "# Добавить новые правила:"
    Write-Host "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306"
    Write-Host "netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306"
    Write-Host ""
    Write-Host "# Проверить правила:"
    Write-Host "netsh interface portproxy show all"
}

