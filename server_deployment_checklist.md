# Чеклист и инструкция по подготовке и развертыванию Python web-приложения на новой виртуальной машине

---

## 1. Подготовка виртуальной машины (до получения IP)

### 1.1. Базовые действия
- Получить доступ к VM (через консоль/панель управления провайдера).
- Установить минимальную ОС (рекомендуется Ubuntu Server LTS, например, 22.04).
- Обновить систему:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

### 1.2. Создание пользователя для деплоя
- Создать отдельного пользователя (например, `deploy`):
  ```bash
  sudo adduser deploy
  sudo usermod -aG sudo deploy
  ```
- Запретить root-доступ по SSH (после настройки ключей).

### 1.3. Настройка SSH
- Сгенерировать SSH-ключи на локальной машине:
  ```bash
  ssh-keygen -t ed25519 -C "deploy@yourdomain"
  ```
- Добавить публичный ключ в `~deploy/.ssh/authorized_keys` на сервере.
- Настроить права:
  ```bash
  sudo chown -R deploy:deploy /home/deploy/.ssh
  sudo chmod 700 /home/deploy/.ssh
  sudo chmod 600 /home/deploy/.ssh/authorized_keys
  ```
- Отключить вход по паролю:
  - В `/etc/ssh/sshd_config`:
    ```
    PermitRootLogin no
    PasswordAuthentication no
    ```
  - Перезапустить SSH:
    ```bash
    sudo systemctl restart sshd
    ```

---

## 2. Установка необходимых сервисов

### 2.1. Python и инструменты
```bash
sudo apt install -y python3 python3-venv python3-pip
```

### 2.2. Git
```bash
sudo apt install -y git
```

### 2.3. Nginx (веб-сервер)
```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2.4. Gunicorn (WSGI-сервер)
- Устанавливается в виртуальном окружении проекта:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install gunicorn
  ```

### 2.5. Certbot (SSL)
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2.6. База данных (пример: PostgreSQL или MySQL)
- **PostgreSQL:**
  ```bash
  sudo apt install -y postgresql postgresql-contrib
  sudo systemctl enable postgresql
  sudo systemctl start postgresql
  ```
- **MySQL:**
  ```bash
  sudo apt install -y mysql-server
  sudo systemctl enable mysql
  sudo systemctl start mysql
  ```

### 2.7. Supervisor (альтернатива systemd для управления процессами)
```bash
sudo apt install -y supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### 2.8. Мониторинг и логирование
- **htop, iftop, iotop, net-tools:**
  ```bash
  sudo apt install -y htop iftop iotop net-tools
  ```
- **fail2ban (защита от брутфорса):**
  ```bash
  sudo apt install -y fail2ban
  sudo systemctl enable fail2ban
  sudo systemctl start fail2ban
  ```
- **logrotate (ротация логов):**
  ```bash
  sudo apt install -y logrotate
  ```

### 2.9. Firewall (ufw)
```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 2.10. Swap (если мало RAM)
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. Настройка сервисов и безопасности

### 3.1. Права пользователей и каталогов
- Каталог приложения должен принадлежать пользователю `deploy` (или www-data, если используется systemd):
  ```bash
  sudo chown -R deploy:www-data /var/www/flask_helpdesk
  sudo chmod -R 755 /var/www/flask_helpdesk
  ```

### 3.2. Systemd unit для Gunicorn
- Пример файла `/etc/systemd/system/flask-helpdesk.service`:
  ```ini
  [Unit]
  Description=Gunicorn instance to serve Flask Helpdesk
  After=network.target

  [Service]
  User=deploy
  Group=www-data
  WorkingDirectory=/var/www/flask_helpdesk
  Environment="PATH=/var/www/flask_helpdesk/venv/bin"
  ExecStart=/var/www/flask_helpdesk/venv/bin/gunicorn --workers 3 --bind unix:/run/gunicorn/gunicorn.sock wsgi:app

  [Install]
  WantedBy=multi-user.target
  ```
- Активировать:
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable flask-helpdesk
  sudo systemctl start flask-helpdesk
  ```

### 3.3. Настройка Nginx
- Пример конфига `/etc/nginx/sites-available/flask_helpdesk`:
  ```nginx
  server {
      listen 80;
      server_name yourdomain.com;

      location / {
          proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
- Активировать сайт:
  ```bash
  sudo ln -s /etc/nginx/sites-available/flask_helpdesk /etc/nginx/sites-enabled
  sudo nginx -t
  sudo systemctl reload nginx
  ```

### 3.4. Настройка SSL (после получения домена и IP)
```bash
sudo certbot --nginx -d yourdomain.com
```

### 3.5. fail2ban
- Проверить `/etc/fail2ban/jail.local` и активировать нужные фильтры (например, для sshd и nginx).

---

## 4. Автоматизация деплоймента

- **CI/CD:** Настроить пайплайн (например, GitLab CI, как в вашем `.gitlab-ci.yml`).
- **SSH-ключи:** Добавить приватный ключ в CI/CD переменные.
- **Права:** Убедиться, что пользователь деплоя может перезапускать сервисы через `sudo` без пароля (только нужные команды!).
- **systemd/supervisor:** Использовать для автоматического рестарта приложения при сбоях.

---

## 5. Базовые тесты после переноса

### 5.1. Проверка статуса сервисов
```bash
sudo systemctl status flask-helpdesk
sudo systemctl status nginx
sudo systemctl status postgresql  # или mysql
```

### 5.2. Проверка портов и firewall
```bash
sudo ss -tuln
sudo ufw status
```

### 5.3. Проверка логов
```bash
sudo journalctl -u flask-helpdesk -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 5.4. Проверка доступности приложения
- Открыть в браузере: `http://yourdomain.com` или `http://<ip>`
- Проверить ответ через curl:
  ```bash
  curl -I http://localhost/
  ```

### 5.5. Проверка SSL (после настройки)
```bash
curl -I https://yourdomain.com
```

### 5.6. Проверка работы базы данных
- Зайти в psql/mysql и выполнить простой SELECT.

### 5.7. Проверка автоматического старта сервисов
- Перезагрузить сервер:
  ```bash
  sudo reboot
  ```
- Проверить, что все сервисы стартовали автоматически.

### 5.8. Проверка логирования и ротации логов
- Убедиться, что логи пишутся и ротация работает (`logrotate`).

### 5.9. Проверка swap
```bash
free -h
swapon --show
```

### 5.10. Проверка fail2ban
```bash
sudo fail2ban-client status
```

---

## 6. Рекомендации по безопасности
- Отключить root-доступ по SSH.
- Использовать только ключевую аутентификацию.
- Открывать только необходимые порты.
- Регулярно обновлять систему и пакеты.
- Использовать fail2ban и firewall.
- Хранить секреты (пароли, ключи) только в защищённых переменных CI/CD или .env с ограниченным доступом.

---

## 7. Пример команд для быстрой установки всех основных сервисов
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx supervisor certbot python3-certbot-nginx postgresql postgresql-contrib htop iftop iotop net-tools ufw fail2ban logrotate
```

---

**Если потребуется подробная инструкция по настройке любого из сервисов — дай знать!**
