# Инструкция по обновлению systemd сервиса для Flask

## Проблема
Systemd сервис не загружает переменные окружения из .env.production файла, что вызывает проблемы с CSRF.

## Решение

### 1. Запустите скрипт исправления
На сервере выполните:
```bash
cd /opt/www/its.teztour.com/
source venv/bin/activate
python3 fix_server_csrf.py
```

### 2. Обновите файл systemd сервиса

Отредактируйте файл сервиса:
```bash
sudo nano /etc/systemd/system/flask-helpdesk.service
```

Добавьте строку для загрузки переменных окружения:
```ini
[Unit]
Description=Flask Helpdesk Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/www/its.teztour.com
Environment=PATH=/opt/www/its.teztour.com/venv/bin
EnvironmentFile=/opt/www/its.teztour.com/flask-helpdesk.env
ExecStart=/opt/www/its.teztour.com/venv/bin/gunicorn --workers 3 --bind unix:flask-helpdesk.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Перезагрузите systemd и перезапустите сервис

```bash
sudo systemctl daemon-reload
sudo systemctl restart flask-helpdesk
sudo systemctl status flask-helpdesk
```

### 4. Проверьте работу

```bash
curl -I https://its.tez-tour.com/login
```

## Альтернативный вариант (если первый не сработал)

Если EnvironmentFile не работает, можно указать переменные прямо в файле сервиса:

```ini
[Unit]
Description=Flask Helpdesk Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/www/its.teztour.com
Environment=PATH=/opt/www/its.teztour.com/venv/bin
Environment=FLASK_ENV=production
Environment=SECRET_KEY=production-secret-key-change-this-in-real-deployment-2024
Environment=DEBUG=False
Environment=WTF_CSRF_ENABLED=True
Environment=SESSION_TYPE=filesystem
Environment=SESSION_FILE_DIR=/tmp/flask_sessions
Environment=SESSION_COOKIE_SECURE=True
Environment=SESSION_COOKIE_HTTPONLY=True
Environment=SESSION_COOKIE_SAMESITE=Lax
Environment=SESSION_COOKIE_DOMAIN=its.tez-tour.com
Environment=PERMANENT_SESSION_LIFETIME=86400
ExecStart=/opt/www/its.teztour.com/venv/bin/gunicorn --workers 3 --bind unix:flask-helpdesk.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Проверка

После внесения изменений проверьте:
1. Статус сервиса: `sudo systemctl status flask-helpdesk`
2. Логи сервиса: `sudo journalctl -u flask-helpdesk -f`
3. Доступность сайта: `curl -I https://its.tez-tour.com/login`

## Диагностика

Если проблема осталась, запустите отладочный скрипт:
```bash
cd /opt/www/its.teztour.com/
source venv/bin/activate
python3 debug_csrf_server.py
