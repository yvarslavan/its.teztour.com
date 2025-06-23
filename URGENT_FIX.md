# 🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ - Flask Helpdesk Deployment

## Проблема
Развертывание через GitLab CI/CD не работает из-за:
1. **Переполнение диска** (25GB заполнен на 100%)
2. **Проблемы с правами доступа** flask_session файлов
3. **Команды sudo в CI/CD** не работают

## ⚡ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ

### 1. КРИТИЧНО: Очистка диска сервера
```bash
# Подключение к серверу
ssh yvarslavan@10.7.74.252

# Проверка текущего состояния
df -h

# УДАЛЕНИЕ СТАРЫХ БЭКАПОВ (освободит ~4.5GB)
sudo rm -rf /var/www/flask_helpdesk_backup_*

# Очистка временных файлов
rm -rf /tmp/flask*
sudo rm -rf /var/log/*.log.*

# Проверка результата
df -h
```

### 2. Очистка проблемных файлов
```bash
# Переход в приложение
cd /var/www/flask_helpdesk

# Очистка flask_session (проблемные файлы)
sudo rm -rf flask_session/*
sudo rm -rf __pycache__/

# Создание директорий с правильными правами
mkdir -p flask_session logs
sudo chown -R www-data:www-data flask_session logs
chmod 755 flask_session logs
```

### 3. Проверка статуса сервиса
```bash
# Проверка текущего статуса
sudo systemctl status flask-helpdesk

# При необходимости перезапуск
sudo systemctl restart flask-helpdesk
```

## 🔄 ПОСЛЕ ОЧИСТКИ: Повторный деплой

1. Убедиться что свободно >2GB места: `df -h`
2. Запустить развертывание в GitLab CI/CD
3. После успешного развертывания выполнить команды:

```bash
# На сервере после деплоя
sudo systemctl restart flask-helpdesk
sudo chown -R www-data:www-data /var/www/flask_helpdesk/flask_session
sudo chown -R www-data:www-data /var/www/flask_helpdesk/logs
```

## 📊 Проверка результата

```bash
# Проверка места на диске
df -h

# Проверка статуса приложения
sudo systemctl status flask-helpdesk

# Проверка логов
sudo journalctl -u flask-helpdesk -f --lines=20

# Тест приложения
curl -I https://its.tez-tour.com
```

## 🛠️ Что исправлено в коде

1. **`.gitlab-ci.yml`** - убраны sudo команды, добавлена безопасная очистка
2. **`scripts/server_cleanup.py`** - новый скрипт для очистки проблемных файлов
3. **Документация** - `DEPLOYMENT_TROUBLESHOOTING.md` с полным руководством

## 📞 Экстренные контакты

При критических проблемах:
- Откат: `sudo mv flask_helpdesk_backup flask_helpdesk` (если есть бэкап)
- Проверка логов: `sudo journalctl -u flask-helpdesk -f`
- Статус сервиса: `sudo systemctl status flask-helpdesk`

---
**Время выполнения:** ~5-10 минут
**Критичность:** ВЫСОКАЯ - блокирует все развертывания
**Результат:** Рабочий CI/CD pipeline и освобожденное место на диске
