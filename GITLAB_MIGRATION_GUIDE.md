# 🚀 Руководство по деплою Flask Helpdesk в корпоративный GitLab

## 📋 Подготовка к миграции

### 1️⃣ **Анализ текущего проекта**

**Структура проекта:**
```
flask_helpdesk/
├── blog/                    # Основное Flask приложение
├── .github/workflows/       # GitHub Actions (будет заменено на .gitlab-ci.yml)
├── requirements.txt         # Python зависимости
├── config.py               # Конфигурация
├── wsgi.py                 # WSGI entry point
├── app.py                  # Главный файл приложения
├── mysql_db.py             # Работа с MySQL
├── redmine.py              # Интеграция с Redmine
├── erp_oracle.py           # Интеграция с Oracle ERP
└── migrations/             # Миграции БД
```

**Ключевые зависимости:**
- Flask 2.3.3
- SQLAlchemy 2.0.21
- MySQL Connector
- Oracle cx_Oracle
- LDAP3 для аутентификации
- APScheduler для задач

## 🔧 Пошаговая настройка GitLab CI/CD

### 2️⃣ **Создание .gitlab-ci.yml**

Скопируйте содержимое файла `GITLAB_DEPLOYMENT_GUIDE.md` в `.gitlab-ci.yml` в корне проекта.

### 3️⃣ **Настройка переменных окружения в GitLab**

В GitLab перейдите в **Settings → CI/CD → Variables** и добавьте:

#### **🔐 Секреты деплоя:**
```bash
# SSH ключи и доступы
SSH_PRIVATE_KEY          # Приватный SSH ключ для деплоя
DEPLOY_HOST             # IP или домен production сервера
DEPLOY_USER             # Пользователь для деплоя (например: deployer)
DEPLOY_PATH             # Путь к приложению (/var/www/flask_helpdesk)
DEPLOY_PORT             # Порт приложения (например: 5000)

# Staging окружение
STAGING_HOST            # IP или домен staging сервера
STAGING_USER            # Пользователь для staging
STAGING_PATH            # Путь к staging (/var/www/flask_helpdesk_staging)
STAGING_PORT            # Порт staging (например: 5001)
```

#### **🗄️ База данных:**
```bash
# MySQL Production
DB_HOST                 # Хост БД
DB_USER                 # Пользователь БД
DB_PASSWORD             # Пароль БД
DB_NAME                 # Имя БД

# Oracle ERP
ORACLE_HOST             # Хост Oracle
ORACLE_USER             # Пользователь Oracle
ORACLE_PASSWORD         # Пароль Oracle
ORACLE_SERVICE          # Сервис Oracle
```

#### **🔑 Внешние интеграции:**
```bash
# Redmine
REDMINE_URL             # URL Redmine сервера
REDMINE_API_KEY         # API ключ Redmine

# LDAP
LDAP_SERVER             # LDAP сервер
LDAP_BIND_DN            # LDAP bind DN
LDAP_BIND_PASSWORD      # LDAP пароль

# OpenAI (если используется)
OPENAI_API_KEY          # API ключ OpenAI

# Firebase (для уведомлений)
FIREBASE_CREDENTIALS    # JSON содержимое файла credentials
```

#### **⚙️ Конфигурация приложения:**
```bash
FLASK_ENV               # production
SECRET_KEY              # Секретный ключ Flask
FLASK_DEBUG             # False для production
```

### 4️⃣ **Настройка GitLab Runner**

#### **Для корпоративного GitLab нужен Runner:**

**Вариант A: Shared Runner (если доступен)**
- Используйте общие runners корпорации
- Убедитесь что есть доступ к Docker

**Вариант B: Dedicated Runner (рекомендуется)**
```bash
# Установка GitLab Runner на сервере
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Регистрация runner
sudo gitlab-runner register \
  --url "https://your-gitlab.company.com/" \
  --registration-token "YOUR_REGISTRATION_TOKEN" \
  --executor "docker" \
  --docker-image "python:3.11-slim" \
  --description "Flask Helpdesk Runner" \
  --tag-list "flask,python,deploy"
```

### 5️⃣ **Подготовка сервера деплоя**

#### **Создание пользователя деплоя:**
```bash
# На production сервере
sudo adduser deployer
sudo usermod -aG sudo deployer
sudo usermod -aG www-data deployer

# Настройка SSH ключей
sudo mkdir -p /home/deployer/.ssh
sudo chown deployer:deployer /home/deployer/.ssh
sudo chmod 700 /home/deployer/.ssh

# Добавьте публичный ключ в authorized_keys
echo "ssh-rsa YOUR_PUBLIC_KEY" | sudo tee /home/deployer/.ssh/authorized_keys
sudo chown deployer:deployer /home/deployer/.ssh/authorized_keys
sudo chmod 600 /home/deployer/.ssh/authorized_keys
```

#### **Настройка systemd сервиса:**
```bash
# Создание файла сервиса
sudo tee /etc/systemd/system/flask-helpdesk.service << EOF
[Unit]
Description=Flask Helpdesk Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/flask_helpdesk
Environment=PATH=/var/www/flask_helpdesk/venv/bin
ExecStart=/var/www/flask_helpdesk/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable flask-helpdesk
```

#### **Настройка Nginx (опционально):**
```bash
# Конфигурация Nginx
sudo tee /etc/nginx/sites-available/flask-helpdesk << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/flask_helpdesk/blog/static;
        expires 30d;
    }
}
EOF

# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/flask-helpdesk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Процесс миграции

### 6️⃣ **Перенос кода в GitLab**

#### **Создание нового репозитория в GitLab:**
1. Войдите в корпоративный GitLab
2. Создайте новый проект: **"Flask Helpdesk"**
3. Выберите **Private** для корпоративного проекта

#### **Клонирование и настройка:**
```bash
# Клонирование текущего GitHub репозитория
git clone https://github.com/yvarslavan/Tez_its_helpdesk.git flask-helpdesk-gitlab
cd flask-helpdesk-gitlab

# Добавление GitLab remote
git remote add gitlab https://your-gitlab.company.com/your-group/flask-helpdesk.git

# Создание .gitlab-ci.yml
cp GITLAB_DEPLOYMENT_GUIDE.md .gitlab-ci.yml

# Удаление GitHub Actions
rm -rf .github/

# Коммит изменений
git add .
git commit -m "🚀 Миграция в GitLab CI/CD"

# Отправка в GitLab
git push gitlab main
```

### 7️⃣ **Настройка веток и политик**

#### **Создание веток:**
```bash
# Создание staging ветки
git checkout -b develop
git push gitlab develop

# Создание feature веток (пример)
git checkout -b feature/gitlab-migration
git push gitlab feature/gitlab-migration
```

#### **Настройка Branch Protection в GitLab:**
1. **Settings → Repository → Push Rules**
2. **Settings → Repository → Merge Request Settings**
3. Включите: **"Merge requests can only be merged when all discussions are resolved"**
4. Включите: **"Pipelines must succeed"**

### 8️⃣ **Тестирование pipeline**

#### **Первый запуск:**
1. Сделайте коммит в `develop` ветку
2. Создайте Merge Request в `main`
3. Проверьте выполнение pipeline:
   - ✅ **validate** - валидация проекта
   - ✅ **test** - тестирование зависимостей
   - ✅ **build** - сборка приложения
   - 🔄 **deploy_staging** - автоматический деплой в staging

#### **Production деплой:**
1. Merge Request в `main` ветку
2. Pipeline выполнится автоматически до этапа **build**
3. **deploy_production** запускается **вручную** для безопасности

## 🛡️ Безопасность и мониторинг

### 9️⃣ **Настройка мониторинга**

#### **Логирование в GitLab:**
```yaml
# Добавление в .gitlab-ci.yml
after_script:
  - echo "Pipeline completed at $(date)"
  - df -h  # Проверка дискового пространства
```

#### **Уведомления:**
1. **Settings → Integrations → Slack/Teams**
2. Настройте уведомления о:
   - Успешных деплоях
   - Ошибках pipeline
   - Merge Request статусах

### 🔟 **Backup и восстановление**

#### **Автоматические бэкапы:**
```bash
# Скрипт бэкапа (на сервере)
#!/bin/bash
BACKUP_DIR="/opt/backups/flask-helpdesk"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание бэкапа приложения
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /var/www/flask_helpdesk

# Бэкап базы данных
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

## 📈 Преимущества GitLab CI/CD

### ✅ **Что получаете:**

1. **🔄 Автоматизация:** Полный CI/CD pipeline
2. **🛡️ Безопасность:** Контролируемые деплои
3. **📊 Мониторинг:** Встроенная аналитика
4. **🔧 Гибкость:** Настройка под корпоративные требования
5. **📦 Артефакты:** Хранение билдов
6. **🌊 Environments:** Staging/Production окружения
7. **👥 Collaboration:** Code Review процесс
8. **📈 Metrics:** Детальная статистика деплоев

### 🎯 **Результат миграции:**

- **⚡ Быстрые деплои:** 3-5 минут вместо ручного процесса
- **🛡️ Безопасность:** Автоматические бэкапы и rollback
- **📊 Прозрачность:** Полная история изменений
- **🔄 Reliability:** Стабильные и предсказуемые деплои
- **👥 Team Work:** Улучшенная командная работа

## 🚀 Запуск в production

После настройки всех компонентов:

1. **Тестирование** на staging окружении
2. **Code Review** через Merge Requests
3. **Автоматические тесты** в pipeline
4. **Ручной деплой** в production
5. **Мониторинг** и **алерты**

**Ваш Flask Helpdesk готов к корпоративному использованию с GitLab CI/CD!** 🎉
