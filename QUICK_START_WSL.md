# Быстрый старт в WSL с VPN

## Проблема решена ✅

Ошибка `(2013, 'Lost connection to MySQL server during query')` возникает из-за неправильной конфигурации хостов MySQL в WSL.

## Решение за 3 шага

### 1. Настройте метрику WSL (ОБЯЗАТЕЛЬНО, один раз!)

⚠️ **КРИТИЧЕСКИ ВАЖНО!** Без этого WSL не будет работать с VPN.

В **Windows PowerShell от администратора**:

```powershell
# Настроить метрику
Get-NetIPInterface | Where-Object {$_.InterfaceAlias -Match "vEthernet (WSL)"} | Set-NetIPInterface -InterfaceMetric 6000

# Перезапустить WSL
wsl --shutdown
```

Затем снова откройте WSL.

### 2. Создайте правильную конфигурацию

В **WSL терминале**:

```bash
cd ~/projects/its.teztour.com
python3 setup_wsl_config.py
```

### 3. Остановите старый процесс (если запущен)

```bash
# Остановить все процессы Flask
pkill -f "python.*app.py"
```

### 4. Запустите приложение

```bash
python3 app.py
```

Теперь вы должны увидеть:
```
✅ Загружены переменные окружения из .env (режим: development) [WSL detected]
```

## Что делает скрипт

Скрипт `setup_wsl_config.py`:
- Создает резервную копию `.env` → `.env.backup`
- Создает новый `.env` с правильными хостами:
  - `MYSQL_HOST=helpdesk.teztour.com`
  - `MYSQL_QUALITY_HOST=quality.teztour.com`

## Проверка перед запуском

```bash
# Убедитесь что VPN подключен и серверы доступны
ping -c 3 helpdesk.teztour.com
ping -c 3 quality.teztour.com

# Проверьте что порты MySQL доступны
nc -zv helpdesk.teztour.com 3306
nc -zv quality.teztour.com 3306
```

Если пинг работает (как у вас работал `ping vpn.teztour.com`), всё готово!

## Подробная документация

- Полная инструкция: [WSL_VPN_SETUP.md](WSL_VPN_SETUP.md)
- Общая настройка окружений: [ENV_SETUP.md](ENV_SETUP.md)

## Откат изменений

Если нужно вернуть старую конфигурацию:

```bash
cp .env.backup .env
```

