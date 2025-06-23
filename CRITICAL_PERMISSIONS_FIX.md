# 🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА

## Проблема
Развертывание GitLab CI/CD не может выполняться из-за проблем с правами доступа:
- Файлы flask_session принадлежат www-data
- Директория /var/www/flask_helpdesk недоступна для записи
- Невозможно скопировать новые файлы
- Откат не работает

## НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ

### 1. Скопировать скрипт на сервер
```bash
scp emergency_fix_permissions.py ubuntu@10.7.74.252:~/
```

### 2. Подключиться к серверу
```bash
ssh ubuntu@10.7.74.252
```

### 3. Запустить экстренное исправление
```bash
python3 ~/emergency_fix_permissions.py
```

### 4. Проверить результат
```bash
ls -la /var/www/flask_helpdesk/
whoami
```

### 5. После исправления - запустить развертывание
Вернуться в GitLab и запустить pipeline заново.

## Что делает скрипт

1. **Проверяет текущие права доступа**
   - Показывает владельца директории
   - Выводит текущие права

2. **Исправляет права доступа**
   - Меняет владельца на текущего пользователя
   - Устанавливает права 755

3. **Очищает проблемные файлы**
   - Удаляет все файлы flask_session
   - Очищает кэш Python
   - Удаляет старое виртуальное окружение

4. **Настраивает права для сервиса**
   - Останавливает Flask сервис
   - Устанавливает правильные права для всех директорий

## После исправления

1. **Запустить GitLab CI/CD pipeline**
2. **После успешного развертывания выполнить:**
   ```bash
   sudo systemctl restart flask-helpdesk
   sudo systemctl status flask-helpdesk
   ```

## Если скрипт не работает

### Ручное исправление:
```bash
# 1. Остановить сервис
sudo systemctl stop flask-helpdesk

# 2. Изменить владельца (директория уже существует)
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk

# 3. Установить права
sudo chmod -R 755 /var/www/flask_helpdesk

# 4. Очистить проблемные файлы
sudo rm -rf /var/www/flask_helpdesk/flask_session/*
sudo rm -rf /var/www/flask_helpdesk/__pycache__
sudo find /var/www/flask_helpdesk -name "*.pyc" -delete

# 5. Пересоздать только служебные директории (НЕ ТРОГАЕМ ДАННЫЕ!)
sudo mkdir -p /var/www/flask_helpdesk/flask_session
sudo mkdir -p /var/www/flask_helpdesk/logs
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk

# 6. Запустить сервис обратно
sudo systemctl start flask-helpdesk
```

## Проверка успешности
```bash
# Проверить права
ls -la /var/www/flask_helpdesk/

# Проверить возможность записи
touch /var/www/flask_helpdesk/test_write && rm /var/www/flask_helpdesk/test_write && echo "Запись работает"
```

## Контакты для экстренной помощи
- Если проблемы продолжаются, обратитесь к системному администратору
- Проверьте, что пользователь ubuntu имеет sudo права
