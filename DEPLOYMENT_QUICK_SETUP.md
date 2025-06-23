# 🚀 Быстрая настройка после создания пользователя deploy

## ✅ Статус
- [x] Пользователь `deploy` создан
- [ ] SSH ключи настроены
- [ ] Права доступа настроены
- [ ] Первый деплой выполнен

## 📋 Следующие шаги

### 1. Настройка SSH ключей для пользователя deploy

```bash
# Переключаемся на пользователя deploy
sudo su - deploy

# Создаем директорию для SSH ключей
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавляем публичный SSH ключ из GitLab
echo "ВАSH_ПУБЛИЧНЫЙ_КЛЮЧ_ИЗ_GITLAB" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Выходим из пользователя deploy
exit
```

### 2. Настройка прав доступа

```bash
# Выполняем скрипт исправления прав
sudo bash fix_permissions.sh

# Или вручную:
sudo chown -R deploy:www-data /var/www/flask_helpdesk
sudo chmod -R 755 /var/www/flask_helpdesk
sudo chmod -R g+w /var/www/flask_helpdesk

# Добавляем deploy в группу www-data
sudo usermod -a -G www-data deploy

# Создаем директории для бэкапов и логов
sudo mkdir -p /var/backups/flask_helpdesk /var/log/flask_helpdesk
sudo chown -R deploy:www-data /var/backups/flask_helpdesk /var/log/flask_helpdesk
sudo chmod -R 755 /var/backups/flask_helpdesk /var/log/flask_helpdesk
```

### 3. Проверка настроек GitLab CI/CD

Убедитесь, что в GitLab настроены переменные:

| Переменная | Значение | Тип |
|------------|----------|-----|
| `SSH_PRIVATE_KEY` | Приватный SSH ключ | File |
| `DEPLOY_SERVER` | IP адрес сервера | Variable |
| `DEPLOY_USER` | deploy | Variable |
| `DEPLOY_PATH` | /var/www/flask_helpdesk | Variable |
| `BACKUP_PATH` | /var/backups/flask_helpdesk | Variable |
| `SERVICE_NAME` | flask-helpdesk | Variable |

### 4. Тестирование SSH подключения

```bash
# На локальной машине или в GitLab Runner
ssh deploy@ВАШ_СЕРВЕР "echo 'SSH работает!'"
```

### 5. Запуск первого деплоя

После настройки всех переменных:

1. Сделайте коммит в репозиторий
2. Pipeline автоматически запустится
3. Следите за логами в GitLab CI/CD

### 6. Проверка после деплоя

```bash
# Проверяем статус сервиса
sudo systemctl status flask-helpdesk

# Проверяем логи
sudo journalctl -u flask-helpdesk -f

# Проверяем веб-интерфейс
curl -I http://localhost
```

## 🔧 Возможные проблемы и решения

### Проблема: SSH ключ не работает
```bash
# Проверяем права на SSH ключи
ls -la /home/deploy/.ssh/
# Должно быть: authorized_keys (600), .ssh (700)
```

### Проблема: Нет прав на запись
```bash
# Исправляем права
sudo chown -R deploy:www-data /var/www/flask_helpdesk
sudo chmod -R g+w /var/www/flask_helpdesk
```

### Проблема: Сервис не запускается
```bash
# Проверяем конфигурацию
sudo systemctl status flask-helpdesk
sudo journalctl -u flask-helpdesk --no-pager
```

## 📞 Поддержка

Если возникают проблемы:
1. Проверьте логи GitLab CI/CD
2. Проверьте системные логи: `sudo journalctl -f`
3. Проверьте права доступа: `ls -la /var/www/flask_helpdesk`

## 🎯 Следующий коммит

После настройки сделайте тестовый коммит для проверки деплоя:

```bash
git add .
git commit -m "test: проверка автоматического деплоя"
git push origin main
```

Pipeline должен пройти все этапы:
- ✅ pre_deploy_checks
- ✅ deploy_to_server
- ✅ post_deploy_verification
