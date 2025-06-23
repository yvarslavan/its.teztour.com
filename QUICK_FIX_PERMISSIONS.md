# 🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА

## 🚨 ПРОБЛЕМА
Pipeline остановился с ошибкой: `❌ Нет прав записи в /var/www/flask_helpdesk`

## ⚡ БЫСТРОЕ РЕШЕНИЕ

### Вариант 1: Автоматический скрипт (РЕКОМЕНДУЕТСЯ)

```bash
# На сервере выполните:
wget https://gitlab.teztour.com/y.varslavan/Tez_its_helpdesk/raw/main/fix_permissions.sh
chmod +x fix_permissions.sh
./fix_permissions.sh
```

### Вариант 2: Ручное исправление

```bash
# Подключитесь к серверу
ssh deploy@YOUR_SERVER_IP

# Исправьте права доступа
sudo mkdir -p /var/www/flask_helpdesk
sudo chown deploy:www-data /var/www/flask_helpdesk
sudo chmod 775 /var/www/flask_helpdesk
sudo usermod -aG www-data deploy

# Проверьте результат
ls -la /var/www/flask_helpdesk
groups deploy
```

### Вариант 3: Одна команда

```bash
ssh deploy@YOUR_SERVER_IP "sudo mkdir -p /var/www/flask_helpdesk && sudo chown deploy:www-data /var/www/flask_helpdesk && sudo chmod 775 /var/www/flask_helpdesk && sudo usermod -aG www-data deploy"
```

## 🔍 ПРОВЕРКА

После исправления проверьте:

```bash
# Тест записи
ssh deploy@YOUR_SERVER_IP "touch /var/www/flask_helpdesk/test_file && rm /var/www/flask_helpdesk/test_file && echo 'Права исправлены!'"
```

## 🚀 ПЕРЕЗАПУСК ДЕПЛОЯ

После исправления прав:

1. Перейдите в GitLab CI/CD → Pipelines
2. Найдите последний pipeline
3. Нажмите кнопку "Retry" для этапа `pre_deploy_checks`
4. Или сделайте новый commit для запуска полного pipeline

## 💡 ОБЪЯСНЕНИЕ

Проблема возникла потому что:
- Пользователь `deploy` не имел прав записи в `/var/www/flask_helpdesk`
- Директория принадлежала другому пользователю
- Или не была создана вовсе

После исправления:
- ✅ Пользователь `deploy` - владелец директории
- ✅ Группа `www-data` имеет права записи
- ✅ Права `775` разрешают запись владельцу и группе
