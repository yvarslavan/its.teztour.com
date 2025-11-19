$port = 1521
$remoteHost = "10.7.23.4"
$remotePort = 1521

Write-Host "🚀 Starting PowerShell TCP Proxy: 0.0.0.0:$port -> $remoteHost:$remotePort"

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
$listener.Start()

try {
    while ($true) {
        if ($listener.Pending()) {
            $client = $listener.AcceptTcpClient()
            Write-Host "✅ New connection from $($client.Client.RemoteEndPoint)"
            
            # Запускаем обработку в фоновом задании (Job) или просто в отдельном потоке, 
            # но PowerShell однопоточный по умолчанию. Для простоты делаем последовательно (плохо) 
            # или используем Runspace (сложно).
            # Для теста Oracle (одно соединение) последовательная обработка пойдет, 
            # но если приложение открывает много соединений - зависнет.
            
            # Используем простой подход: создаем фоновый процесс powershell для обработки
            $code = {
                param($client, $remoteHost, $remotePort)
                try {
                    $remote = [System.Net.Sockets.TcpClient]::new($remoteHost, $remotePort)
                    $stream1 = $client.GetStream()
                    $stream2 = $remote.GetStream()
                    $buffer = [byte[]]::new(4096)
                    
                    # Простой цикл пересылки (блокирующий, не работает дуплекс в одном потоке)
                    # Нам нужны асинхронные операции или два потока.
                    # В PowerShell это боль.
                    
                    # Проще использовать `netsh`, но он не работает.
                } catch {
                    Write-Host "Error: $_"
                }
            }
            # PowerShell proxy слишком сложен для on-the-fly написания без ошибок.
        }
        Start-Sleep -Milliseconds 100
    }
} finally {
    $listener.Stop()
}

