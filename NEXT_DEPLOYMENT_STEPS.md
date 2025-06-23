# 🚀 ПЛАН ПРОДОЛЖЕНИЯ ДЕПЛОЯ - ПОСЛЕ ВОССТАНОВЛЕНИЯ СЕРВИСА

## ✅ **ТЕКУЩИЙ СТАТУС:**
- Flask Helpdesk сервис восстановлен и работает
- Виртуальное окружение создано: `/var/www/flask_helpdesk/venv/`
- Сервис активен: `sudo systemctl status flask-helpdesk` показывает `active (running)`
- Логи показывают нормальную работу приложения

## 🎯 **СЛЕДУЮЩИЕ ШАГИ ДЛЯ АВТОМАТИЗАЦИИ ДЕПЛОЯ:**

### 1️⃣ **НЕМЕДЛЕННО - Настройка GitLab переменных**

Перейдите в GitLab проект → Settings → CI/CD → Variables и добавьте:

```bash
# SSH подключение к серверу
SSH_PRIVATE_KEY    # Содержимое файла ~/.ssh/id_rsa
DEPLOY_HOST        # IP вашего Ubuntu сервера
DEPLOY_USER        # yvarslavan (или deployer)
DEPLOY_PORT        # 22 (или ваш SSH порт)

# Пути на сервере
DEPLOY_PATH        # /var/www/flask_helpdesk

# База данных (если используется)
DB_HOST           # localhost или IP MySQL сервера
DB_USER           # ваш пользователь MySQL
DB_PASSWORD       # пароль MySQL
DB_NAME           # название базы данных

# Flask настройки
FLASK_ENV         # production
SECRET_KEY        # случайная строка для Flask
```

### 2️⃣ **ТЕСТИРОВАНИЕ - Запуск первого pipeline**

```bash
# В локальном проекте:
git add .
git commit -m "🚀 Ready for automated deployment - service restored"
git push origin main

# Затем в GitLab:
# 1. Перейдите в CI/CD → Pipelines
# 2. Найдите новый pipeline
# 3. Следите за выполнением этапов:
#    ✅ validate_project
#    ✅ test_dependencies
#    ✅ build_application
#    🟡 deploy_to_server (manual - запускается вручную)
```

### 3️⃣ **ДЕПЛОЙ - Запуск автоматического обновления**

После успешного build_application:

1. **В GitLab Pipeline нажмите кнопку "Play" на этапе `deploy_to_server`**
2. **Следите за логами деплоя** - они покажут каждый шаг
3. **После завершения выполните на сервере:**

```bash
# Финальные команды на Ubuntu сервере:
sudo systemctl daemon-reload
sudo systemctl restart flask-helpdesk
sudo chown -R www-data:www-data /var/www/flask_helpdesk/flask_session
sudo chown -R www-data:www-data /var/www/flask_helpdesk/logs

# Проверка работы:
sudo systemctl status flask-helpdesk
sudo journalctl -u flask-helpdesk -f
```

### 4️⃣ **ПРОВЕРКА - Тестирование работы**

```bash
# На сервере:
curl http://localhost:5000/health || curl http://localhost:5000/
systemctl status flask-helpdesk
journalctl -u flask-helpdesk --lines=20

# Проверка веб-интерфейса:
# Откройте браузер: http://ваш-ip:5000
```

## 🔧 **ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ:**

### ❌ **Проблема: SSH ключ не работает**
```bash
# Решение:
# 1. Проверьте формат ключа в GitLab переменных
# 2. Убедитесь, что публичный ключ добавлен на сервер:
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

### ❌ **Проблема: Pipeline падает на test_dependencies**
```bash
# Решение:
# 1. Проверьте requirements.txt на корректность
# 2. Возможно нужно обновить версии пакетов
```

### ❌ **Проблема: Деплой не может перезаписать файлы**
```bash
# Решение на сервере:
sudo systemctl stop flask-helpdesk
sudo chown -R yvarslavan:yvarslavan /var/www/flask_helpdesk
# Затем повторите деплой
```

### ❌ **Проблема: Сервис не запускается после деплоя**
```bash
# Диагностика:
sudo systemctl status flask-helpdesk
sudo journalctl -u flask-helpdesk --lines=50

# Частые причины:
# 1. Отсутствуют зависимости - переустановите venv
# 2. Неправильные права доступа - исправьте chown
# 3. Конфликт портов - проверьте netstat -tlnp | grep :5000
```

## 📊 **МОНИТОРИНГ ДЕПЛОЯ:**

### Во время деплоя следите за:
1. **GitLab Pipeline логи** - показывают прогресс
2. **SSH подключение** - должно работать без ошибок
3. **Disk space** - pipeline проверяет свободное место
4. **Service status** - сервис должен остаться активным

### После деплоя проверьте:
1. **Статус сервиса:** `sudo systemctl status flask-helpdesk`
2. **Логи приложения:** `sudo journalctl -u flask-helpdesk -f`
3. **Веб-интерфейс:** откройте в браузере
4. **База данных:** проверьте подключение

## 🎉 **ПОСЛЕ УСПЕШНОГО ДЕПЛОЯ:**

1. **Настройте регулярные деплои** - каждый push в main будет автоматически деплоиться
2. **Создайте staging окружение** - для тестирования перед продакшеном
3. **Настройте уведомления** - в Slack/Teams о статусе деплоев
4. **Документируйте процесс** - для команды разработки

## 🆘 **ЭКСТРЕННЫЙ ОТКАТ:**

Если что-то пошло не так:

```bash
# На сервере:
cd /var/www
sudo systemctl stop flask-helpdesk

# Если есть backup:
sudo rm -rf flask_helpdesk
sudo mv flask_helpdesk_backup flask_helpdesk
sudo systemctl start flask-helpdesk

# Или восстановите из Git:
sudo rm -rf flask_helpdesk
git clone https://your-repo-url.git flask_helpdesk
cd flask_helpdesk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start flask-helpdesk
```

---

**🚀 ГОТОВЫ К ЗАПУСКУ АВТОМАТИЧЕСКОГО ДЕПЛОЯ!**

Следующий шаг: настройте переменные в GitLab и запустите первый pipeline.
