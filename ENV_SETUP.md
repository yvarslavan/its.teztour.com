# Настройка окружений разработки и продакшена

## Структура файлов

- `.env.development` - конфигурация для локальной разработки (через порт-прокси Windows)
- `.env.production` - конфигурация для продакшена (сервер в корпоративной сети)
- `.env` - активная конфигурация (создаётся автоматически из одного из файлов выше)
- **WSL с VPN** - используйте `python3 setup_wsl_config.py` (см. WSL_VPN_SETUP.md)

## Быстрая настройка

### Для WSL с VPN (рекомендуется):

```bash
python3 setup_wsl_config.py
```

Это создаст `.env` с прямым подключением к серверам через VPN.

**Требования:**
- Cisco Secure Client подключен в Windows
- Выполнена настройка метрики WSL (см. WSL_VPN_SETUP.md)
- Доступны хосты: `helpdesk.teztour.com`, `quality.teztour.com`

### Для разработки в Windows (локально через порт-прокси):

```bash
python3 setup_env.py development
```

Это скопирует `.env.development` в `.env`.

**Требования:**
- Cisco Secure Client подключен в Windows
- Порт-прокси настроен в PowerShell:
  ```powershell
  netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3306 connectaddress=helpdesk.teztour.com connectport=3306
  netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=3307 connectaddress=quality.teztour.com connectport=3306
  ```

### Для продакшена (сервер в корпоративной сети):

```bash
python3 setup_env.py production
```

Это скопирует `.env.production` в `.env`.

**Требования:**
- Сервер уже находится в корпоративной сети
- Прямой доступ к `helpdesk.teztour.com` и `quality.teztour.com`

## Создание файлов конфигурации

### .env.development

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-flask-helpdesk-2024-change-in-production

# MySQL Redmine Database (через порт-прокси Windows)
MYSQL_HOST=127.0.0.1
MYSQL_DATABASE=redmine
MYSQL_USER=redmine_user
MYSQL_PASSWORD=replace_with_real_password

# MySQL Quality Database (через порт-прокси Windows на порт 3307)
MYSQL_QUALITY_HOST=127.0.0.1:3307
MYSQL_QUALITY_DATABASE=redmine
MYSQL_QUALITY_USER=quality_user
MYSQL_QUALITY_PASSWORD=replace_with_real_password

# Redmine API Configuration
REDMINE_URL=https://helpdesk.teztour.com
REDMINE_API_KEY=your_redmine_api_key_here

# Session Configuration
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400
```

### .env.production

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=production-secret-key-change-this-in-real-deployment-2024

# MySQL Redmine Database (прямое подключение в корпоративной сети)
MYSQL_HOST=redmine-db.example.internal
MYSQL_DATABASE=redmine
MYSQL_USER=redmine_user
MYSQL_PASSWORD=replace_with_real_password

# MySQL Quality Database (прямое подключение в корпоративной сети)
MYSQL_QUALITY_HOST=quality-db.example.internal
MYSQL_QUALITY_DATABASE=redmine
MYSQL_QUALITY_USER=quality_user
MYSQL_QUALITY_PASSWORD=replace_with_real_password

# Redmine API Configuration
REDMINE_URL=https://helpdesk.teztour.com
REDMINE_API_KEY=your_redmine_api_key_here

# Session Configuration
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## Автоматический выбор окружения

`app.py` автоматически выбирает нужный файл:
- Если `FLASK_ENV=production` → использует `.env.production`
- Иначе → использует `.env.development`
- Если нужный файл не найден → fallback на `.env`

## Проверка текущего окружения

```bash
# Проверка какой файл используется
python3 -c "from dotenv import load_dotenv; from pathlib import Path; import os; print('Используется:', Path('.env').read_text()[:100] if Path('.env').exists() else 'не найден')"
```
