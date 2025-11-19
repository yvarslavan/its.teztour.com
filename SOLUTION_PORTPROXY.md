# Решение через Port Proxy (Windows)

## Проблема

Диагностика показала:
- ✅ VPN подключен
- ✅ DNS работает (`helpdesk.teztour.com` → `10.7.74.72`)
- ❌ **Ping не проходит** к серверам
- ❌ **Порт 3306 недоступен** из WSL

## Причина

Скорее всего **firewall на серверах MySQL** не разрешает прямое подключение с интерфейса WSL.

## Решение: Port Proxy через Windows

Используем Windows как прокси-сервер:
- Windows подключается к MySQL серверам через VPN ✅
- WSL подключается к Windows через localhost ✅
- Windows пробрасывает подключения к MySQL серверам ✅

### Архитектура решения:

```
WSL                Windows                 VPN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Python App         Port Proxy           MySQL Servers
    ↓                  ↓                     ↓
127.0.0.1:3306  →  Windows  →  helpdesk.teztour.com:3306
127.0.0.1:3307  →  Windows  →  quality.teztour.com:3306
```

## Пошаговое решение

### Шаг 1: Проверить доступность из Windows

В **Windows PowerShell** (можно не от администратора):

```powershell
# Проверить доступность MySQL серверов из Windows
.\check_windows_connectivity.ps1
```

Если серверы **доступны из Windows** - переходим к Шагу 2.

### Шаг 2: Настроить Port Proxy в Windows

В **Windows PowerShell от администратора**:

```powershell
# Настроить порт-прокси
.\setup_portproxy.ps1
```

Скрипт:
1. Удалит старые правила (если были)
2. Создаст новые правила:
   - `127.0.0.1:3306` → `helpdesk.teztour.com:3306`
   - `127.0.0.1:3307` → `quality.teztour.com:3306`
3. Покажет текущие правила

### Шаг 3: Настроить .env в WSL

В **WSL**:

```bash
# Обновить конфигурацию для порт-прокси
bash setup_portproxy_env.sh
```

Скрипт:
1. Определит IP адрес Windows хоста
2. Создаст резервную копию `.env`
3. Обновит `.env` для использования порт-прокси
4. Проверит доступность портов

### Шаг 4: Запустить приложение

```bash
# Остановить старый процесс
bash kill_port_5000.sh

# Запустить приложение
python3 app.py
```

## Проверка что всё работает

После запуска приложения проверьте логи:

```bash
# В WSL
tail -f app_err.log | grep -E "(ERROR|MySQL)"
```

**Не должно быть:**
- ❌ `No route to host`
- ❌ `Lost connection to MySQL server`
- ❌ `Can't connect to MySQL server`

## Ручная настройка (если скрипты не работают)

### В Windows PowerShell от администратора:

```powershell
# Удалить старые правила
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307

# Добавить новые правила
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306

# Проверить правила
netsh interface portproxy show all
```

### В WSL:

```bash
# Получить IP Windows хоста
WSL_HOST_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo $WSL_HOST_IP

# Отредактировать .env вручную
nano .env

# Изменить:
MYSQL_HOST=<WSL_HOST_IP>
MYSQL_PORT=3306

MYSQL_QUALITY_HOST=<WSL_HOST_IP>
MYSQL_QUALITY_PORT=3307

# Проверить доступность
timeout 2 bash -c "</dev/tcp/$WSL_HOST_IP/3306" && echo "Port 3306 OK"
timeout 2 bash -c "</dev/tcp/$WSL_HOST_IP/3307" && echo "Port 3307 OK"
```

## Удаление Port Proxy (если нужно вернуться)

### В Windows PowerShell от администратора:

```powershell
# Удалить правила порт-прокси
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3306
netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=3307

# Проверить что удалено
netsh interface portproxy show all
```

### В WSL:

```bash
# Вернуть прямое подключение
bash setup_wsl_config.sh
```

## Преимущества Port Proxy

✅ **Надежность:** Работает всегда, если Windows может подключиться  
✅ **Простота:** Не требует сложной настройки сети  
✅ **Производительность:** Минимальные накладные расходы  
✅ **Универсальность:** Работает с любыми портами и протоколами  

## Недостатки Port Proxy

❌ **Зависимость от Windows:** Если Windows спит - WSL теряет подключение  
❌ **Дополнительный hop:** Небольшая дополнительная задержка  
❌ **Настройка:** Требует прав администратора  

## Автоматизация

Создайте bat-файл для быстрой настройки:

```batch
@echo off
REM setup_vpn.bat

echo Настройка VPN и Port Proxy...

REM Запустить PowerShell скрипт от администратора
powershell -ExecutionPolicy Bypass -File "%~dp0setup_portproxy.ps1"

echo.
echo Настройка завершена!
echo Теперь в WSL выполните: bash setup_portproxy_env.sh
pause
```

## Мониторинг Port Proxy

Проверить что Port Proxy работает:

```powershell
# Показать все правила
netsh interface portproxy show all

# Проверить подключение
Test-NetConnection -ComputerName 127.0.0.1 -Port 3306
Test-NetConnection -ComputerName 127.0.0.1 -Port 3307
```

## Устранение проблем

### Проблема: "Connection refused" на 127.0.0.1

**Причина:** Port Proxy не настроен или отключен

**Решение:**
```powershell
# Перезапустить службу Port Proxy
Restart-Service iphlpsvc

# Проверить правила
netsh interface portproxy show all
```

### Проблема: Port Proxy правила есть, но не работают

**Причина:** Firewall блокирует подключения

**Решение:**
```powershell
# Добавить правило в firewall
New-NetFirewallRule -DisplayName "MySQL Port Proxy" -Direction Inbound -LocalPort 3306,3307 -Protocol TCP -Action Allow
```

### Проблема: После перезагрузки Windows правила исчезают

**Причина:** Редкий баг Windows

**Решение:** Добавить правила в автозапуск:
```
1. Создать .bat файл с командами netsh
2. Добавить в Task Scheduler (Планировщик заданий)
3. Запускать при старте Windows с правами администратора
```

## Проверка что всё работает

### Финальная проверка:

```bash
# 1. В Windows проверить правила
netsh interface portproxy show all

# 2. В WSL проверить доступность
bash diagnose_vpn.sh

# 3. Проверить конфигурацию
grep -E "MYSQL.*HOST" .env

# 4. Запустить приложение
bash kill_port_5000.sh
python3 app.py

# 5. Проверить логи
tail -100 app_err.log | grep -i mysql
```

Если всё правильно:
- ✅ Port Proxy правила показываются
- ✅ Порты 3306 и 3307 доступны на Windows IP
- ✅ `.env` содержит Windows IP и правильные порты
- ✅ Приложение запускается без ошибок MySQL
- ✅ Логи не содержат ошибок подключения

