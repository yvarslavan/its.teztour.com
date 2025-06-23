# 🚀 Flask Helpdesk - Автоматический деплой

## 📋 Статус проекта

- ✅ GitLab CI/CD pipeline настроен и оптимизирован
- ✅ Размер deployment пакета оптимизирован до <20MB
- ✅ Пользователь `deploy` создан на сервере
- 🔄 Требуется завершение настройки SSH и прав доступа

## 🎯 Быстрый старт

### 1. На сервере выполните:

```bash
# Исправление прав доступа
sudo bash fix_permissions.sh

# Проверка готовности к деплою
bash check_deploy_status.sh
```

### 2. Настройка SSH ключей

```bash
# Переключаемся на пользователя deploy
sudo su - deploy

# Создаем SSH директорию
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавляем публичный ключ из GitLab
echo "ВАШ_SSH_ПУБЛИЧНЫЙ_КЛЮЧ" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

exit
```

### 3. Настройка переменных GitLab CI/CD

В GitLab перейдите в **Settings → CI/CD → Variables** и добавьте:

| Переменная | Значение | Тип |
|------------|----------|-----|
| `SSH_PRIVATE_KEY` | Приватный SSH ключ | File |
| `DEPLOY_SERVER` | IP адрес вашего сервера | Variable |
| `DEPLOY_USER` | deploy | Variable |
| `DEPLOY_PATH` | /var/www/flask_helpdesk | Variable |
| `BACKUP_PATH` | /var/backups/flask_helpdesk | Variable |
| `SERVICE_NAME` | flask-helpdesk | Variable |

### 4. Запуск деплоя

Сделайте коммит и пуш - pipeline запустится автоматически:

```bash
git add .
git commit -m "deploy: настройка автоматического деплоя"
git push origin main
```

## 📊 Архитектура деплоя

### Pipeline этапы:

1. **pre_deploy_checks** - Проверка подключения и прав доступа
2. **deploy_to_server** - Основной деплой с бэкапом
3. **post_deploy_verification** - Проверка работоспособности
4. **rollback_deployment** - Откат (manual job)

### Структура на сервере:

```
/var/www/flask_helpdesk/          # Основное приложение
├── app.py                        # Точка входа
├── blog/                         # Flask приложение
├── requirements.txt              # Зависимости
└── .env                         # Конфигурация

/var/backups/flask_helpdesk/      # Бэкапы
├── backup_YYYYMMDD_HHMMSS/      # Автоматические бэкапы
└── manual_backup_*/             # Ручные бэкапы

/var/log/flask_helpdesk/          # Логи
├── app.log                      # Логи приложения
└── deploy.log                   # Логи деплоя
```

## 🔧 Управление сервисом

```bash
# Проверка статуса
sudo systemctl status flask-helpdesk

# Перезапуск
sudo systemctl restart flask-helpdesk

# Просмотр логов
sudo journalctl -u flask-helpdesk -f

# Остановка
sudo systemctl stop flask-helpdesk

# Запуск
sudo systemctl start flask-helpdesk
```

## 📈 Мониторинг

### Проверка работоспособности:

```bash
# Статус сервиса
systemctl is-active flask-helpdesk

# HTTP ответ
curl -I http://localhost

# Использование ресурсов
ps aux | grep flask
```

### Логи для отладки:

```bash
# Логи приложения
tail -f /var/log/flask_helpdesk/app.log

# Системные логи
sudo journalctl -u flask-helpdesk --since "1 hour ago"

# Логи Nginx (если используется)
sudo tail -f /var/log/nginx/access.log
```

## 🛠️ Полезные скрипты

### check_deploy_status.sh
Комплексная проверка готовности к деплою:
```bash
bash check_deploy_status.sh
```

### fix_permissions.sh
Исправление прав доступа:
```bash
sudo bash fix_permissions.sh
```

## 🚨 Устранение неисправностей

### Проблема: SSH подключение не работает
```bash
# Проверьте права на SSH ключи
ls -la /home/deploy/.ssh/
# Должно быть: authorized_keys (600), .ssh (700)

# Проверьте SSH подключение
ssh deploy@ВАШ_СЕРВЕР "echo 'SSH работает'"
```

### Проблема: Нет прав на запись
```bash
# Исправьте права
sudo bash fix_permissions.sh

# Или вручную:
sudo chown -R deploy:www-data /var/www/flask_helpdesk
sudo chmod -R g+w /var/www/flask_helpdesk
```

### Проблема: Сервис не запускается
```bash
# Проверьте конфигурацию
sudo systemctl status flask-helpdesk
sudo journalctl -u flask-helpdesk --no-pager

# Проверьте зависимости Python
cd /var/www/flask_helpdesk
python3 -m pip list
```

### Проблема: 413 Request Entity Too Large
Pipeline уже оптимизирован и исключает большие файлы. Если проблема повторится:

```bash
# Проверьте размер пакета
du -sh /tmp/deployment-package/

# Проверьте .gitignore
cat .gitignore
```

## 📚 Дополнительные ресурсы

- [DEPLOYMENT_SETUP_GUIDE.md](DEPLOYMENT_SETUP_GUIDE.md) - Подробное руководство
- [server_setup.sh](server_setup.sh) - Автоматическая настройка сервера
- [.gitlab-ci.yml](.gitlab-ci.yml) - Конфигурация CI/CD

## 🎉 Готово к продакшену!

После выполнения всех шагов ваш Flask Helpdesk будет:

- ✅ Автоматически деплоиться при каждом коммите
- ✅ Создавать бэкапы перед обновлением
- ✅ Проверять работоспособность после деплоя
- ✅ Поддерживать откат к предыдущей версии
- ✅ Логировать все операции

**Удачного деплоя! 🚀**
