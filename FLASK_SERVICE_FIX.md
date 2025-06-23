# 🔧 Исправление проблемы Flask Helpdesk сервиса

## Проблема
Сервис `flask-helpdesk.service` не может запуститься из-за отсутствующего виртуального окружения:
```
Failed to locate executable /var/www/flask_helpdesk/venv/bin/python: No such file or directory
```

## Решение

### Вариант 1: Автоматическое исправление
1. Скопируйте файл `fix_flask_service.sh` на Ubuntu сервер
2. Выполните команды:
```bash
chmod +x fix_flask_service.sh
./fix_flask_service.sh
```

### Вариант 2: Быстрое исправление
1. Скопируйте файл `quick_fix_flask.sh` на Ubuntu сервер
2. Выполните команды:
```bash
chmod +x quick_fix_flask.sh
./quick_fix_flask.sh
```

### Вариант 3: Ручное исправление
Выполните команды на Ubuntu сервере:

```bash
# 1. Остановка сервиса
sudo systemctl stop flask-helpdesk.service

# 2. Переход в директорию проекта
cd /var/www/flask_helpdesk

# 3. Создание виртуального окружения
python3 -m venv venv

# 4. Установка зависимостей
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# 5. Настройка прав доступа
sudo chown -R www-data:www-data /var/www/flask_helpdesk
sudo chmod +x venv/bin/python

# 6. Перезапуск сервиса
sudo systemctl daemon-reload
sudo systemctl start flask-helpdesk.service

# 7. Проверка статуса
sudo systemctl status flask-helpdesk.service
```

## Проверка работы

После исправления проверьте:

```bash
# Статус сервиса
sudo systemctl status flask-helpdesk.service

# Логи в реальном времени
sudo journalctl -u flask-helpdesk.service -f

# Проверка виртуального окружения
ls -la /var/www/flask_helpdesk/venv/bin/python
```

## Дополнительные команды для управления сервисом

```bash
# Остановка
sudo systemctl stop flask-helpdesk.service

# Запуск
sudo systemctl start flask-helpdesk.service

# Перезапуск
sudo systemctl restart flask-helpdesk.service

# Автозапуск при загрузке
sudo systemctl enable flask-helpdesk.service

# Отключение автозапуска
sudo systemctl disable flask-helpdesk.service
```

## Возможные проблемы

### 1. Ошибки установки пакетов
```bash
# Обновите pip
venv/bin/pip install --upgrade pip

# Установите системные зависимости
sudo apt update
sudo apt install python3-dev build-essential
```

### 2. Проблемы с правами доступа
```bash
# Исправьте права на всю директорию
sudo chown -R www-data:www-data /var/www/flask_helpdesk
sudo chmod -R 755 /var/www/flask_helpdesk
```

### 3. Проблемы с портами
```bash
# Проверьте занятые порты
sudo netstat -tlnp | grep :5000

# Убейте процесс, если нужно
sudo kill -9 <PID>
```
