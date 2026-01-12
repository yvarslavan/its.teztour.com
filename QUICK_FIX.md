# Быстрое исправление настроек MySQL

## Данные для подключения

```
Host: 10.0.0.172 (helpdesk.teztour.com)
Port: 3306
User: easyredmine
Pass: QhAKtwCLGW
Database: ? (нужно уточнить)
```

## Способ 1: Автоматическое обновление (рекомендуется)

Запустите скрипт в терминале WSL:

```bash
python3 update_mysql_config.py
```

Скрипт обновит файл `.env` с новыми настройками.

**⚠️ ВАЖНО**: После запуска проверьте имя базы данных в `.env`. 
Если база называется не `easyredmine`, откройте `.env` и исправьте `MYSQL_DATABASE`.

## Способ 2: Ручное обновление

Откройте файл `.env` и найдите/обновите следующие строки:

```env
MYSQL_HOST=10.0.0.172
MYSQL_DATABASE=redmine
MYSQL_USER=easyredmine
MYSQL_PASSWORD=QhAKtwCLGW
```

## Проверка подключения

После обновления проверьте подключение:

```bash
python3 test_mysql_connection.py
```

Если всё правильно, запустите приложение:

```bash
source venv/bin/activate
python3 app.py
```

## Если IP 10.0.0.172 недоступен

Если IP `10.0.0.172` недоступен с вашей машины (это внутренний IP компании), используйте один из вариантов:

1. **SSH туннель** (см. LOCAL_DEVELOPMENT_SETUP.md)
2. **VPN подключение** к корпоративной сети
3. Используйте хост `helpdesk.teztour.com` если он доступен через VPN

