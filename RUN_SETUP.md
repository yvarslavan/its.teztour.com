# Запуск PowerShell скриптов

## Проблема

PowerShell блокирует выполнение неподписанных скриптов:
```
cannot be loaded. The file is not digitally signed.
```

## Решение

### Вариант 1: Временно разрешить выполнение (рекомендуется)

В **Windows PowerShell от администратора**:

```powershell
# Разрешить выполнение скриптов в текущей сессии
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Теперь можно запускать скрипты
.\check_windows_connectivity.ps1
.\setup_portproxy.ps1
```

После закрытия PowerShell политика вернется к исходной (безопасно).

### Вариант 2: Запустить напрямую с параметром

```powershell
# Запустить с обходом политики
powershell -ExecutionPolicy Bypass -File .\check_windows_connectivity.ps1
powershell -ExecutionPolicy Bypass -File .\setup_portproxy.ps1
```

### Вариант 3: Выполнить команды вручную (без скриптов)

Если не хотите менять политику, используйте команды напрямую:

#### Проверка доступности из Windows:

```powershell
# Проверить helpdesk
Test-NetConnection -ComputerName helpdesk.teztour.com -Port 3306

# Проверить quality
Test-NetConnection -ComputerName quality.teztour.com -Port 3306
```

Если оба показывают `TcpTestSucceeded : True`, переходите к настройке порт-прокси.

#### Настройка порт-прокси:

```powershell
# Удалить старые правила (если есть)
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307

# Добавить новые правила
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306

# Проверить правила
netsh interface portproxy show all
```

## Пошаговая инструкция

### Шаг 1: Откройте PowerShell от администратора

1. Нажмите Win + X
2. Выберите "Windows PowerShell (Администратор)" или "Terminal (Admin)"

### Шаг 2: Перейдите в директорию проекта

```powershell
cd \\wsl.localhost\Ubuntu-22.04\home\yvarslavan\projects\its.teztour.com
```

### Шаг 3: Разрешите выполнение скриптов

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Или используйте команды вручную (см. Вариант 3).

### Шаг 4: Проверьте доступность MySQL серверов

```powershell
# Используя скрипт:
.\check_windows_connectivity.ps1

# Или вручную:
Test-NetConnection -ComputerName helpdesk.teztour.com -Port 3306
Test-NetConnection -ComputerName quality.teztour.com -Port 3306
```

**Ожидаемый результат:**
```
TcpTestSucceeded : True
```

Если `False` - значит серверы недоступны даже из Windows. Проверьте VPN подключение.

### Шаг 5: Настройте порт-прокси

```powershell
# Используя скрипт:
.\setup_portproxy.ps1

# Или вручную (команды выше в Варианте 3)
```

**Ожидаемый результат:**
```
Listen on ipv4:             Connect to ipv4:

Address         Port        Address         Port
--------------- ----------  --------------- ----------
127.0.0.1       3306        helpdesk.teztour.com 3306
127.0.0.1       3307        quality.teztour.com 3306
```

### Шаг 6: Настройте WSL

В **WSL терминале**:

```bash
cd ~/projects/its.teztour.com
bash setup_portproxy_env.sh
```

### Шаг 7: Запустите приложение

```bash
bash kill_port_5000.sh
python3 app.py
```

## Проверка результата

### В PowerShell:

```powershell
# Проверить что порт-прокси настроен
netsh interface portproxy show all

# Проверить что порты слушаются
netstat -an | findstr "127.0.0.1:3306"
netstat -an | findstr "127.0.0.1:3307"
```

### В WSL:

```bash
# Проверить что Windows хост доступен
WSL_HOST=$(ip route show | grep default | awk '{print $3}')
echo "Windows host: $WSL_HOST"

# Проверить порты
timeout 2 bash -c "</dev/tcp/$WSL_HOST/3306" && echo "✅ Port 3306 OK" || echo "❌ Port 3306 FAIL"
timeout 2 bash -c "</dev/tcp/$WSL_HOST/3307" && echo "✅ Port 3307 OK" || echo "❌ Port 3307 FAIL"

# Проверить конфигурацию
grep -E "MYSQL.*HOST" .env
```

## Устранение проблем

### Проблема: "Access is denied" при выполнении Set-ExecutionPolicy

**Причина:** PowerShell запущен не от администратора

**Решение:** Закройте PowerShell и откройте снова от имени администратора (Win + X → "Windows PowerShell (Администратор)")

### Проблема: TcpTestSucceeded : False

**Причина:** MySQL серверы недоступны даже из Windows

**Решение:**
1. Проверьте что VPN подключен
2. Попробуйте пинг: `ping helpdesk.teztour.com`
3. Проверьте firewall Windows

### Проблема: Порт-прокси настроен, но WSL не подключается

**Причина:** Windows Firewall блокирует подключения

**Решение:**
```powershell
# Добавить правило в firewall
New-NetFirewallRule -DisplayName "MySQL Port Proxy 3306" -Direction Inbound -LocalPort 3306 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "MySQL Port Proxy 3307" -Direction Inbound -LocalPort 3307 -Protocol TCP -Action Allow
```

### Проблема: После перезагрузки правила исчезают

**Причина:** Редкий баг или служба не запущена

**Решение:**
```powershell
# Проверить службу IP Helper
Get-Service iphlpsvc

# Если остановлена - запустить
Start-Service iphlpsvc
Set-Service iphlpsvc -StartupType Automatic

# Добавить правила заново
.\setup_portproxy.ps1
```

## Полная последовательность команд

Скопируйте и вставьте в **PowerShell от администратора**:

```powershell
# 1. Перейти в проект
cd \\wsl.localhost\Ubuntu-22.04\home\yvarslavan\projects\its.teztour.com

# 2. Разрешить выполнение скриптов (для текущей сессии)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 3. Проверить доступность (опционально)
Test-NetConnection -ComputerName helpdesk.teztour.com -Port 3306
Test-NetConnection -ComputerName quality.teztour.com -Port 3306

# 4. Настроить порт-прокси
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306

# 5. Проверить результат
netsh interface portproxy show all
```

Затем в **WSL**:

```bash
# Настроить конфигурацию
cd ~/projects/its.teztour.com
bash setup_portproxy_env.sh

# Запустить приложение
bash kill_port_5000.sh
python3 app.py
```

## Автоматизация (для будущего)

Создайте `.bat` файл для одноразового запуска:

```batch
@echo off
REM quick_setup.bat

echo Настройка Port Proxy для WSL...
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Требуются права администратора!
    echo Запустите этот файл от имени администратора.
    pause
    exit /b 1
)

REM Настройка порт-прокси
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306 >nul 2>&1
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307 >nul 2>&1
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306

echo.
echo Готово! Порт-прокси настроен:
echo.
netsh interface portproxy show all
echo.
echo Теперь в WSL выполните: bash setup_portproxy_env.sh
pause
```

Запуск: Правый клик → "Запустить от имени администратора"

