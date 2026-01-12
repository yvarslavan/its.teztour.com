# ITS TezTour - Internal Task System

Flask-приложение для управления задачами и интеграции с Redmine.

## 🚀 Быстрый старт

### WSL с VPN (рекомендуется)

Если вы работаете в WSL с Cisco Secure Client:

```bash
# 1. Настройте метрику WSL в Windows PowerShell (от администратора, один раз):
Get-NetIPInterface | Where-Object {$_.InterfaceAlias -Match "vEthernet (WSL)"} | Set-NetIPInterface -InterfaceMetric 6000

# 2. Создайте конфигурацию для WSL
python3 setup_wsl_config.py

# 3. Запустите приложение
python3 app.py
```

📖 Подробнее: [QUICK_START_WSL.md](QUICK_START_WSL.md)

### Windows (через порт-прокси)

```bash
python3 setup_env.py development
python3 app.py
```

### Production (сервер в корпоративной сети)

```bash
python3 setup_env.py production
python3 app.py
```

## 📋 Структура проекта

```
its.teztour.com/
├── app/                    # Flask приложение
│   ├── models/            # Модели данных
│   ├── routes/            # Маршруты
│   ├── static/            # Статические файлы
│   └── templates/         # HTML шаблоны
├── blog/                  # Модули приложения
│   ├── main/             # Основные маршруты
│   ├── tasks/            # Управление задачами
│   └── user/             # Управление пользователями
├── config.py             # Конфигурация
├── secure_config.py      # Безопасная конфигурация (переменные окружения)
└── app.py               # Точка входа

```

## 🔧 Настройка окружений

Приложение поддерживает несколько окружений:

| Окружение | Файл | Использование |
|-----------|------|---------------|
| **WSL с VPN** | создается `setup_wsl_config.py` | WSL + Cisco Secure Client |
| Development | `.env.development` | Windows с порт-прокси |
| Production | `.env.production` | Сервер в корпоративной сети |

📖 Подробнее: [ENV_SETUP.md](ENV_SETUP.md)

## 🐛 Устранение проблем

### Ошибка: "Address already in use" (Порт 5000 занят)

**Решение:**
```bash
bash kill_port_5000.sh
python3 app.py
```

📖 Подробнее: [START_APP.md](START_APP.md)

### Ошибка: "Lost connection to MySQL server"

Эта ошибка означает неправильную конфигурацию хостов MySQL.

**Решение для WSL:**
```bash
python3 setup_wsl_config.py
bash kill_port_5000.sh
python3 app.py
```

**Решение для Windows:**
```bash
python3 setup_env.py development
```

📖 Подробнее: [WSL_VPN_SETUP.md](WSL_VPN_SETUP.md)

### Ошибка: "No route to host" ⚠️

Критическая ошибка - WSL не может достучаться до MySQL серверов через VPN.

**Быстрая диагностика:**
```bash
bash diagnose_vpn.sh
```

**Решение 1: Настроить метрику WSL** (в Windows PowerShell от администратора):
```powershell
Get-NetIPInterface | Where-Object {$_.InterfaceAlias -Match "vEthernet (WSL)"} | Set-NetIPInterface -InterfaceMetric 6000
wsl --shutdown
```

**Решение 2: Использовать Port Proxy** (рекомендуется, если Решение 1 не помогло):
```powershell
# В Windows PowerShell от администратора
.\setup_portproxy.ps1

# Затем в WSL
bash setup_portproxy_env.sh
bash kill_port_5000.sh && python3 app.py
```

📖 Подробнее: 
- [FIX_NO_ROUTE_TO_HOST.md](FIX_NO_ROUTE_TO_HOST.md)
- [SOLUTION_PORTPROXY.md](SOLUTION_PORTPROXY.md) ⭐

### Проверка доступности серверов

```bash
# Проверка DNS и пинга
ping -c 3 helpdesk.teztour.com
ping -c 3 quality.teztour.com

# Проверка портов MySQL
nc -zv helpdesk.teztour.com 3306
nc -zv quality.teztour.com 3306
```

## 📦 Зависимости

Установка зависимостей через `uv`:

```bash
uv pip install -r requirements.txt
```

## 🔐 Конфигурация

Приложение использует переменные окружения из файла `.env`.

Основные параметры:
- `MYSQL_HOST` - хост MySQL Redmine
- `MYSQL_QUALITY_HOST` - хост MySQL Quality
- `REDMINE_URL` - URL Redmine API
- `REDMINE_API_KEY` - API ключ Redmine

Полный список: см. `secure_config.py`

## 🏗️ Технологии

- **Python 3.12**
- **Flask** - веб-фреймворк
- **Flask-SQLAlchemy** - ORM
- **Flask-WTF** - формы
- **PyMySQL** - MySQL драйвер
- **Bootstrap 5** - UI фреймворк

## 📚 Документация

- [QUICK_START_WSL.md](QUICK_START_WSL.md) - Быстрый старт в WSL
- [WSL_VPN_SETUP.md](WSL_VPN_SETUP.md) - Подробная настройка WSL с VPN
- [ENV_SETUP.md](ENV_SETUP.md) - Настройка окружений
- [QUICK_FIX.md](QUICK_FIX.md) - Быстрые исправления MySQL

## 🤝 Разработка

### Структура папок

```
memory-bank/          # Memory Bank (задачи, прогресс, архив)
.cursor/rules/        # Правила для Cursor AI
```

### Стиль кода

- Используйте классы вместо функций
- Python 3.12+
- Следуйте PEP 8

## 📝 Лицензия

Internal use only - TezTour Company


