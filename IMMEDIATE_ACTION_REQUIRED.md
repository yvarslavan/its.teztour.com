# 🚨 НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ ТРЕБУЮТСЯ

## КРИТИЧЕСКАЯ ПРОБЛЕМА
GitLab CI/CD не может развернуть приложение из-за проблем с правами доступа на сервере.

## ⚠️ ВАЖНО: НЕ ТРОГАЕМ ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ!
- `blog/static/profile_pics` - содержит аватары пользователей
- `blog/db` - содержит базу данных со всеми данными
- Очищаем только временные файлы!

## РЕШЕНИЕ - 3 ПРОСТЫХ ШАГА

### ШАГ 1: Подключиться к серверу
```bash
ssh ubuntu@10.7.74.252
```

### ШАГ 2: Выполнить команды исправления
Скопируйте и выполните эти команды **ОДНУ ЗА ОДНОЙ**:

```bash
# Остановить сервис
sudo systemctl stop flask-helpdesk

# Изменить владельца (директория уже существует)
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk

# Установить права
sudo chmod -R 755 /var/www/flask_helpdesk

# Очистить проблемные файлы
sudo rm -rf /var/www/flask_helpdesk/flask_session/*
sudo rm -rf /var/www/flask_helpdesk/__pycache__
sudo find /var/www/flask_helpdesk -name "*.pyc" -delete
sudo rm -rf /var/www/flask_helpdesk/venv

# Пересоздать только пустые служебные директории
sudo mkdir -p /var/www/flask_helpdesk/flask_session
sudo mkdir -p /var/www/flask_helpdesk/logs

# Финальная настройка прав
sudo chown -R $(whoami):$(whoami) /var/www/flask_helpdesk
sudo chmod -R 755 /var/www/flask_helpdesk

# Запустить сервис обратно
sudo systemctl start flask-helpdesk
```

### ШАГ 3: Проверить что все работает
```bash
# Проверить права
ls -la /var/www/flask_helpdesk/

# Тест записи
touch /var/www/flask_helpdesk/test_write && rm /var/www/flask_helpdesk/test_write && echo "✅ Запись работает!"

# Проверить статус сервиса
sudo systemctl status flask-helpdesk
```

## ПОСЛЕ ИСПРАВЛЕНИЯ

1. **Запустить GitLab CI/CD pipeline заново**
2. **После успешного развертывания:**
   ```bash
   sudo systemctl restart flask-helpdesk
   sudo systemctl status flask-helpdesk
   ```

## АЛЬТЕРНАТИВНЫЙ СПОСОБ (если SSH не работает)

### Через GitLab Runner на сервере:
1. Зайти на сервер напрямую (консоль/VNC)
2. Выполнить команды из ШАГ 2 выше
3. Запустить pipeline в GitLab

## ПРОВЕРКА УСПЕШНОСТИ

После выполнения команд должно быть:
- ✅ Директория `/var/www/flask_helpdesk` принадлежит пользователю `ubuntu`
- ✅ Права доступа `755` на все файлы и директории
- ✅ Нет файлов `flask_session` принадлежащих `www-data`
- ✅ Возможность записи в директорию

## ЕСЛИ ПРОБЛЕМЫ ПРОДОЛЖАЮТСЯ

1. Проверить что пользователь `ubuntu` имеет sudo права:
   ```bash
   sudo -l
   ```

2. Проверить что GitLab Runner использует правильного пользователя:
   ```bash
   whoami
   id
   ```

3. При необходимости добавить пользователя в группу www-data:
   ```bash
   sudo usermod -a -G www-data $(whoami)
   ```

---

**⏰ ВРЕМЯ КРИТИЧНО - ВЫПОЛНИТЕ НЕМЕДЛЕННО!**
