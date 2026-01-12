# Поиск сервера Oracle
# Запускать в Windows PowerShell

Write-Host "Поиск сервера Oracle (порт 1521)..." -ForegroundColor Yellow

$servers = @(
    "helpdesk.teztour.com",
    "quality.teztour.com",
    "10.7.74.72",
    "10.7.74.130",
    "oracle.teztour.com",
    "erp.teztour.com",
    "tez-erp.teztour.com"
)

foreach ($server in $servers) {
    Write-Host "Проверка $server..." -NoNewline
    try {
        $tcp = Test-NetConnection -ComputerName $server -Port 1521 -WarningAction SilentlyContinue
        if ($tcp.TcpTestSucceeded) {
            Write-Host " ✅ ДОСТУПЕН!" -ForegroundColor Green
            Write-Host "   Нашел Oracle сервер: $server" -ForegroundColor Green
            exit 0
        } else {
            Write-Host " ❌" -ForegroundColor Red
        }
    } catch {
        Write-Host " ❌ Ошибка" -ForegroundColor Red
    }
}

Write-Host "`nНе удалось найти сервер Oracle автоматически." -ForegroundColor Yellow

