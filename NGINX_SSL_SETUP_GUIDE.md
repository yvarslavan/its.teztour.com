# Настройка Nginx с SSL для Flask Helpdesk на Red Hat

## Проблемы, которые нужно исправить:
1. SSL сертификаты не существуют
2. Deprecated директива `http2` в listen
3. Нужно сначала настроить HTTP, потом добавить SSL

## Шаг 1: Временная HTTP конфигурация

```bash
# Создаём временную HTTP конфигурацию без SSL
sudo tee /etc/nginx/conf.d/flask-helpdesk.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name its.tez-tour.com;

    # Основные настройки
    client_max_body_size 20M;
    keepalive_timeout 65;

    # Проксирование к Flask приложению
    location / {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы
    location /static/ {
        alias /opt/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Локация для проверки Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri $uri/ =404;
    }

    # Логи
    access_log /var/log/nginx/flask-helpdesk-access.log;
    error_log /var/log/nginx/flask-helpdesk-error.log;
}
EOF

# Создаём директорию для Let's Encrypt
sudo mkdir -p /var/www/html/.well-known/acme-challenge/

# Проверяем конфигурацию
sudo nginx -t

# Если конфигурация корректна, перезагружаем Nginx
sudo systemctl reload nginx
```

## Шаг 2: Настройка Firewall

```bash
# Проверяем статус firewall
sudo firewall-cmd --state

# Открываем HTTP и HTTPS порты
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Проверяем открытые порты
sudo firewall-cmd --list-services
```

## Шаг 3: Установка Certbot для Let's Encrypt

```bash
# Устанавливаем Certbot для Red Hat
sudo dnf install -y certbot python3-certbot-nginx

# Получаем SSL сертификат
sudo certbot --nginx -d its.tez-tour.com

# При запросе введите:
# - Email для уведомлений
# - Согласитесь с условиями (Y)
# - Выберите опцию redirect (рекомендуется)
```

## Шаг 4: Итоговая конфигурация Nginx с SSL

После успешного получения сертификата, Certbot автоматически обновит конфигурацию.
Но можно также создать оптимизированную версию:

```bash
# Создаём оптимизированную конфигурацию с SSL
sudo tee /etc/nginx/conf.d/flask-helpdesk.conf > /dev/null << 'EOF'
# HTTP редирект на HTTPS
server {
    listen 80;
    server_name its.tez-tour.com;

    # Разрешаем Let's Encrypt проверки
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri $uri/ =404;
    }

    # Все остальное редиректим на HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS сервер
server {
    listen 443 ssl;
    http2 on;  # Новый синтаксис вместо deprecated "listen ... http2"
    server_name its.tez-tour.com;

    # SSL настройки (пути будут обновлены Certbot)
    ssl_certificate /etc/letsencrypt/live/its.tez-tour.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/its.tez-tour.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Дополнительные заголовки безопасности
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Основные настройки
    client_max_body_size 20M;
    keepalive_timeout 65;

    # Проксирование к Flask приложению
    location / {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Статические файлы
    location /static/ {
        alias /opt/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;

        # Сжатие для статических файлов
        gzip on;
        gzip_types text/css application/javascript text/javascript application/json;
    }

    # Favicon
    location /favicon.ico {
        alias /opt/www/static/favicon.ico;
        expires 1y;
        access_log off;
    }

    # Логи
    access_log /var/log/nginx/flask-helpdesk-access.log;
    error_log /var/log/nginx/flask-helpdesk-error.log;
}
EOF

# Проверяем конфигурацию
sudo nginx -t

# Перезагружаем Nginx
sudo systemctl reload nginx
```

## Шаг 5: Автообновление SSL сертификатов

```bash
# Проверяем автообновление
sudo certbot renew --dry-run

# Настраиваем cron для автообновления (если не настроен автоматически)
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## Шаг 6: Создание директории приложения

```bash
# Создаём целевую директорию для приложения
sudo mkdir -p /opt/www
sudo mkdir -p /opt/www/static
sudo mkdir -p /run/gunicorn

# Настраиваем права доступа
sudo chown -R deploy:deploy /opt/www
sudo chmod -R 755 /opt/www

# Создаём директорию для сокета Gunicorn
sudo chown deploy:deploy /run/gunicorn
sudo chmod 755 /run/gunicorn
```

## Команды для исправления текущей ситуации

```bash
# 1. Удаляем некорректную конфигурацию
sudo rm -f /etc/nginx/conf.d/flask-helpdesk.conf

# 2. Создаём временную HTTP конфигурацию
sudo tee /etc/nginx/conf.d/flask-helpdesk.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name its.tez-tour.com;

    location / {
        return 200 "Flask Helpdesk Server Ready!\n";
        add_header Content-Type text/plain;
    }

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF

# 3. Проверяем и запускаем Nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx

# 4. Проверяем статус
sudo systemctl status nginx
```

## Проверка работы

```bash
# Проверяем, что Nginx работает
sudo systemctl status nginx

# Проверяем порты
sudo ss -tlnp | grep :80
sudo ss -tlnp | grep :443

# Тестируем HTTP доступ
curl -I http://its.tez-tour.com

# Проверяем логи
sudo tail -f /var/log/nginx/error.log
```

## Следующие шаги

1. **Исправить текущую конфигурацию Nginx** (команды выше)
2. **Настроить DNS** для домена `its.tez-tour.com`
3. **Получить SSL сертификат** через Let's Encrypt
4. **Настроить приложение** в `/opt/www`
5. **Запустить GitLab CI/CD pipeline**
