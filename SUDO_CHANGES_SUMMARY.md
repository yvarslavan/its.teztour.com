# Изменения для работы через sudo вместо root

## ✅ Что изменилось

### До (требовал root):
```bash
ssh root@server
dnf update -y
systemctl start nginx
```

### После (работает через sudo):
```bash
ssh your_user@server
sudo dnf update -y
sudo systemctl start nginx
```

## 🔧 Основные изменения в setup-redhat-server.sh

1. **Убрана проверка root**: `if [[ $EUID -ne 0 ]]`
2. **Добавлена проверка sudo**: `sudo -n true`
3. **Все административные команды**: теперь с `sudo`
4. **Добавлены права в sudoers**: для удобного управления сервисами
5. **Улучшена безопасность**: пользователь deploy получает NOPASSWD права

## 🚀 Как запустить

### Подключение к серверу:
```bash
# Подключаемся под своим пользователем
ssh your_username@server_ip

# Скачиваем и запускаем скрипт
wget https://your-repo/setup-redhat-server.sh
chmod +x setup-redhat-server.sh
./setup-redhat-server.sh
```

### Добавление SSH ключа:
```bash
# Теперь так (через sudo):
sudo nano /home/deploy/.ssh/authorized_keys
```

## 🔐 Дополнительные права

Скрипт автоматически настроит sudoers файл:
```bash
# Файл: /etc/sudoers.d/flask-helpdesk
your_user ALL=(ALL) NOPASSWD: /bin/systemctl start flask-helpdesk
your_user ALL=(ALL) NOPASSWD: /bin/systemctl stop flask-helpdesk
your_user ALL=(ALL) NOPASSWD: /bin/systemctl restart flask-helpdesk
your_user ALL=(ALL) NOPASSWD: /bin/systemctl status flask-helpdesk
your_user ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
your_user ALL=(ALL) NOPASSWD: /bin/journalctl -u flask-helpdesk *
deploy ALL=(ALL) NOPASSWD: ALL
```

## 📋 Команды для мониторинга

```bash
# Статус сервиса (теперь можно без sudo)
systemctl status flask-helpdesk

# Логи (можно без sudo)
journalctl -u flask-helpdesk -f

# Перезапуск (можно без sudo)
systemctl restart flask-helpdesk

# Остальные команды все еще требуют sudo
sudo nginx -t
sudo certbot --nginx -d its.tez-tour.com
```

## ⚡ Преимущества

1. **Безопасность**: Не нужен root пароль
2. **Удобство**: Работа под обычным пользователем
3. **Гибкость**: Можно настроить индивидуальные права
4. **Логирование**: Все действия привязаны к конкретному пользователю
5. **Совместимость**: Работает в корпоративных средах

## ⚠️ Требования

- Пользователь должен быть в группе `wheel` или иметь sudo права
- Первый запуск скрипта потребует ввод пароля для sudo
- После настройки основные команды сервиса будут работать без пароля
