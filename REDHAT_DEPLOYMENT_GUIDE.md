# Полное руководство по настройке деплоя Flask проекта на новый сервер Red Hat

## Этап 1: Подготовка SSH ключей для GitLab CI/CD

### 1.1 Создание SSH ключей на локальной машине
```bash
# Создаем SSH ключ для деплоя
ssh-keygen -t rsa -b 4096 -C "gitlab-ci-deploy" -f ~/.ssh/flask_helpdesk_deploy

# Копируем публичный ключ (потребуется для сервера)
cat ~/.ssh/flask_helpdesk_deploy.pub

# Копируем приватный ключ (потребуется для GitLab)
cat ~/.ssh/flask_helpdesk_deploy
```

### 1.2 Настройка переменных в GitLab CI/CD
Перейдите в GitLab: `Проект -> Settings -> CI/CD -> Variables`

Добавьте следующие переменные:
- `SSH_PRIVATE_KEY`: Содержимое приватного ключа (весь текст из ~/.ssh/flask_helpdesk_deploy)
- `DEPLOY_SERVER`: IP адрес или домен нового сервера Red Hat
- `DEPLOY_USER`: Пользователь для деплоя (например: `deploy` или `flask`)
- `DEPLOY_DOMAIN`: `its.tez-tour.com` (новый домен)

## Этап 2: Настройка нового сервера Red Hat

### 2.1 Подключение к серверу и базовая настройка
```bash
# Подключаемся к серверу (под пользователем с sudo правами)
ssh YOUR_USER@YOUR_SERVER_IP

# Скачиваем и запускаем скрипт автоматической настройки
wget https://your-repo/setup-redhat-server.sh
chmod +x setup-redhat-server.sh
./setup-redhat-server.sh

# Или вручную:
# Обновляем систему
sudo dnf update -y

# Устанавливаем необходимые пакеты
sudo dnf install -y python3 python3-pip nginx git sqlite-devel \
    gcc python3-devel mysql-devel pkg-config openssl-devel \
    libffi-devel systemd-devel firewalld
```

### 2.2 Создание пользователя для деплоя
```bash
# Создаем пользователя для деплоя
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG wheel deploy

# Создаем директории для проекта
sudo mkdir -p /opt/www
sudo chown deploy:deploy /opt/www
sudo chmod 755 /opt/www

# Создаем SSH директорию для пользователя deploy
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh

# Добавляем публичный ключ (вставьте содержимое flask_helpdesk_deploy.pub)
sudo nano /home/deploy/.ssh/authorized_keys
# Вставьте содержимое вашего публичного ключа и сохраните

sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys
```

### 2.3 Настройка Nginx
```bash
# Создаем конфигурацию Nginx для проекта
sudo tee /etc/nginx/conf.d/flask-helpdesk.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name its.tez-tour.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name its.tez-tour.com;

    # SSL настройки (обновите пути к сертификатам)
    ssl_certificate /etc/ssl/certs/its.tez-tour.com.crt;
    ssl_certificate_key /etc/ssl/private/its.tez-tour.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

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

    # Логи
    access_log /var/log/nginx/flask-helpdesk-access.log;
    error_log /var/log/nginx/flask-helpdesk-error.log;
}
EOF

# Проверяем конфигурацию
sudo nginx -t

# Настраиваем автозапуск и запускаем Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2.4 Настройка Firewall
```bash
# Открываем порты для HTTP и HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2.5 Создание systemd сервиса для Flask приложения
```bash
sudo tee /etc/systemd/system/flask-helpdesk.service > /dev/null << 'EOF'
[Unit]
Description=Flask Helpdesk Application
After=network.target

[Service]
Type=exec
User=deploy
Group=deploy
WorkingDirectory=/opt/www
Environment=PATH=/opt/www/venv/bin
Environment=FLASK_ENV=production
Environment=PYTHONPATH=/opt/www
ExecStart=/opt/www/venv/bin/gunicorn \
          --workers 3 --threads 2 --timeout 120 \
          --bind unix:/run/gunicorn/gunicorn.sock \
          wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# Директория для сокета
RuntimeDirectory=gunicorn
RuntimeDirectoryMode=0755
RuntimeDirectoryPreserve=yes

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload
sudo systemctl enable flask-helpdesk
```

## Этап 3: Обновление конфигурационных файлов проекта

### 3.1 Обновление .gitlab-ci.yml будет создано отдельно
### 3.2 Создание нового flask-helpdesk.service для нового пути
### 3.3 Создание nginx конфигурации

## Этап 4: Подготовка SSL сертификатов

### 4.1 Получение SSL сертификата через Let's Encrypt
```bash
# Устанавливаем certbot
sudo dnf install -y certbot python3-certbot-nginx

# Получаем сертификат
sudo certbot --nginx -d its.tez-tour.com

# Настраиваем автообновление
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## Этап 5: Первый деплой

### 5.1 Тестирование SSH подключения
```bash
# С локальной машины тестируем подключение
ssh -i ~/.ssh/flask_helpdesk_deploy deploy@YOUR_SERVER_IP
```

### 5.2 Запуск pipeline в GitLab
1. Убедитесь, что все переменные настроены в GitLab CI/CD
2. Сделайте commit в main ветку
3. Проверьте выполнение pipeline
4. При необходимости выполните ручной откат

## Этап 6: Мониторинг и логи

### 6.1 Полезные команды для мониторинга
```bash
# Статус сервиса
sudo systemctl status flask-helpdesk

# Логи приложения
sudo journalctl -u flask-helpdesk -f

# Логи Nginx
sudo tail -f /var/log/nginx/flask-helpdesk-access.log
sudo tail -f /var/log/nginx/flask-helpdesk-error.log

# Проверка сокета
ls -la /run/gunicorn/

# Тест локального подключения
curl -I http://localhost/
```

### 6.2 Бэкапы
```bash
# Создаем директорию для бэкапов
mkdir -p /opt/backups/flask_helpdesk
chown deploy:deploy /opt/backups/flask_helpdesk

# Скрипт для автоматического бэкапа будет создан в pipeline
```

## Этап 7: Troubleshooting

### 7.1 Проблемы с правами доступа
```bash
# Исправление прав для директории проекта
chown -R deploy:deploy /opt/www
chmod -R 755 /opt/www

# Исправление прав для сокета
chown -R deploy:nginx /run/gunicorn/
```

### 7.2 Проблемы с базой данных
```bash
# Создание директории для БД
mkdir -p /opt/www/blog/db
chown -R deploy:deploy /opt/www/blog/db
chmod -R 755 /opt/www/blog/db
```

### 7.3 Проблемы с зависимостями
```bash
# Переустановка зависимостей
cd /opt/www
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Этап 8: Финальная проверка

После успешного деплоя проверьте:
1. ✅ Сайт доступен по адресу https://its.tez-tour.com/
2. ✅ SSL сертификат работает
3. ✅ Логи не содержат ошибок
4. ✅ Сервис автоматически запускается после перезагрузки
5. ✅ Бэкапы создаются корректно

## Контакты и поддержка

При возникновении проблем проверьте:
- Логи systemd: `journalctl -u flask-helpdesk -f`
- Логи Nginx: `/var/log/nginx/flask-helpdesk-*.log`
- Статус сервисов: `systemctl status flask-helpdesk nginx`
