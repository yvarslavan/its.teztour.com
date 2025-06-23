# 🚀 РУКОВОДСТВО ПО НАСТРОЙКЕ ДЕПЛОЯ FLASK HELPDESK

## 📋 ОБЗОР

Данное руководство поможет вам настроить автоматический деплой Flask Helpdesk приложения через GitLab CI/CD.

## ✅ СТАТУС PIPELINE

- ✅ **build_deployment_package**: Успешно (размер пакета оптимизирован с 127MB до <20MB)
- ✅ **pre_deploy_checks**: Готов к работе
- ✅ **deploy_to_server**: Готов к работе
- ✅ **post_deploy_verification**: Готов к работе
- ✅ **rollback_deployment**: Готов к работе (manual)

## 🔧 ШАГ 1: ПОДГОТОВКА СЕРВЕРА

### 1.1 Запуск скрипта подготовки

На вашем сервере выполните:

```bash
# Скачайте скрипт подготовки
wget https://your-gitlab.com/your-project/raw/main/server_setup.sh

# Сделайте его исполняемым
chmod +x server_setup.sh

# Запустите подготовку (НЕ от root!)
./server_setup.sh
```

### 1.2 Что делает скрипт

- ✅ Обновляет систему
- ✅ Устанавливает Python 3, Nginx, supervisor
- ✅ Создает пользователя `deploy`
- ✅ Настраивает директории проекта
- ✅ Конфигурирует firewall
- ✅ Создает systemd сервис
- ✅ Настраивает Nginx proxy
- ✅ Конфигурирует логирование

## 🔑 ШАГ 2: НАСТРОЙКА SSH КЛЮЧЕЙ

### 2.1 Создание SSH ключа для деплоя

На вашем локальном компьютере:

```bash
# Создайте SSH ключ
ssh-keygen -t rsa -b 4096 -f ~/.ssh/flask_helpdesk_deploy

# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/flask_helpdesk_deploy.pub deploy@YOUR_SERVER_IP
```

### 2.2 Проверка подключения

```bash
# Проверьте SSH подключение
ssh -i ~/.ssh/flask_helpdesk_deploy deploy@YOUR_SERVER_IP "echo 'SSH работает!'"
```

## ⚙️ ШАГ 3: НАСТРОЙКА GITLAB CI/CD ПЕРЕМЕННЫХ

### 3.1 Добавление переменных в GitLab

Перейдите в GitLab: `Project Settings` → `CI/CD` → `Variables` и добавьте:

| Переменная | Тип | Значение | Описание |
|------------|-----|----------|----------|
| `SSH_PRIVATE_KEY` | Variable | Содержимое файла `~/.ssh/flask_helpdesk_deploy` | SSH ключ для подключения |
| `DEPLOY_SERVER` | Variable | `your-server.com` или IP | Адрес сервера |
| `DEPLOY_USER` | Variable | `deploy` | Пользователь для SSH |
| `DEPLOY_PATH` | Variable | `/var/www/flask_helpdesk` | Путь установки |
| `BACKUP_PATH` | Variable | `/var/backups/flask_helpdesk` | Путь для бэкапов |
| `SERVICE_NAME` | Variable | `flask-helpdesk` | Имя systemd сервиса |

### 3.2 Получение SSH ключа

```bash
# Выведите приватный ключ для копирования
cat ~/.ssh/flask_helpdesk_deploy

# Скопируйте ВЕСЬ вывод включая заголовки
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

## 🚀 ШАГ 4: ПЕРВЫЙ ДЕПЛОЙ

### 4.1 Запуск pipeline

После настройки переменных:

1. Сделайте commit в ветку `main`
2. Pipeline автоматически запустится
3. Наблюдайте за процессом в GitLab CI/CD

### 4.2 Ожидаемый результат

```
✅ build_deployment_package   (2-3 минуты)
✅ pre_deploy_checks         (30 секунд)
✅ deploy_to_server          (3-5 минут)
✅ post_deploy_verification  (30 секунд)
🔄 rollback_deployment       (manual - по требованию)
```

## 🔍 ШАГ 5: ПРОВЕРКА ДЕПЛОЯ

### 5.1 Проверка сервиса

```bash
# Подключитесь к серверу
ssh -i ~/.ssh/flask_helpdesk_deploy deploy@YOUR_SERVER_IP

# Проверьте статус сервиса
sudo systemctl status flask-helpdesk

# Проверьте логи
sudo journalctl -u flask-helpdesk -f
```

### 5.2 Проверка веб-приложения

```bash
# Проверьте локальный ответ
curl http://localhost:5000

# Проверьте через Nginx
curl http://YOUR_SERVER_IP
```

### 5.3 Управление сервисом

```bash
# Перезапуск
sudo systemctl restart flask-helpdesk

# Остановка
sudo systemctl stop flask-helpdesk

# Запуск
sudo systemctl start flask-helpdesk

# Просмотр логов
sudo journalctl -u flask-helpdesk --no-pager -n 50
```

## 🛠️ TROUBLESHOOTING

### Проблема: SSH подключение не работает

```bash
# Проверьте SSH ключ
ssh-add ~/.ssh/flask_helpdesk_deploy
ssh -v deploy@YOUR_SERVER_IP
```

### Проблема: Сервис не запускается

```bash
# Проверьте логи сервиса
sudo journalctl -u flask-helpdesk --no-pager -n 20

# Проверьте права доступа
ls -la /var/www/flask_helpdesk/

# Проверьте Python окружение
sudo -u www-data /var/www/flask_helpdesk/venv/bin/python --version
```

### Проблема: Nginx не работает

```bash
# Проверьте конфигурацию Nginx
sudo nginx -t

# Проверьте статус Nginx
sudo systemctl status nginx

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/flask_helpdesk_error.log
```

## 🔄 ОТКАТ ВЕРСИИ

Если что-то пошло не так, используйте manual job `rollback_deployment`:

1. Перейдите в GitLab CI/CD → Pipelines
2. Найдите последний pipeline
3. Нажмите на manual job `rollback_deployment`
4. Подтвердите выполнение

## 📊 МОНИТОРИНГ

### Логи приложения

```bash
# Логи Flask приложения
sudo tail -f /var/log/flask_helpdesk/app.log

# Логи ошибок
sudo tail -f /var/log/flask_helpdesk/error.log

# Логи Nginx
sudo tail -f /var/log/nginx/flask_helpdesk_access.log
sudo tail -f /var/log/nginx/flask_helpdesk_error.log
```

### Системные ресурсы

```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Сетевые подключения
ss -tulpn | grep :5000
```

## 🔐 БЕЗОПАСНОСТЬ

### Рекомендации

1. **Используйте отдельного пользователя** для деплоя (не root)
2. **Ограничьте SSH доступ** только для ключей
3. **Настройте firewall** (UFW уже настроен скриптом)
4. **Регулярно обновляйте** систему
5. **Мониторьте логи** на подозрительную активность

### Дополнительная безопасность

```bash
# Отключите SSH по паролю
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl reload ssh

# Настройте fail2ban
sudo apt install fail2ban
```

## 📞 ПОДДЕРЖКА

При возникновении проблем:

1. Проверьте логи GitLab CI/CD
2. Проверьте логи сервера
3. Убедитесь, что все переменные настроены
4. Проверьте SSH подключение вручную

## 🎯 ГОТОВО!

После выполнения всех шагов у вас будет:

- ✅ Автоматический деплой через GitLab CI/CD
- ✅ Оптимизированный размер пакета (<20MB)
- ✅ Автоматические бэкапы
- ✅ Мониторинг и логирование
- ✅ Возможность отката
- ✅ Безопасная настройка

**Ваше Flask Helpdesk приложение готово к продакшену!** 🚀
