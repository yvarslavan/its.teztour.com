# Краткая инструкция по деплою Flask проекта на Red Hat сервер

## 🎯 Что было создано

1. **REDHAT_DEPLOYMENT_GUIDE.md** - Подробное руководство по настройке
2. **.gitlab-ci-redhat.yml** - Обновленный CI/CD pipeline для Red Hat
3. **flask-helpdesk.service.redhat** - Systemd сервис для Red Hat
4. **flask-helpdesk.nginx.conf** - Nginx конфигурация для its.tez-tour.com
5. **setup-redhat-server.sh** - Автоматический скрипт настройки сервера

## 🚀 Быстрый старт (5 шагов)

### Шаг 1: Подготовка SSH ключей
```bash
# На локальной машине
ssh-keygen -t rsa -b 4096 -C "gitlab-ci-deploy" -f ~/.ssh/flask_helpdesk_deploy
```

### Шаг 2: Настройка Red Hat сервера
```bash
# На Red Hat сервере (от пользователя с sudo правами)
wget https://your-repo/setup-redhat-server.sh
chmod +x setup-redhat-server.sh
./setup-redhat-server.sh
```

### Шаг 3: Добавление SSH ключа на сервер
```bash
# На сервере
cat >> /home/deploy/.ssh/authorized_keys << 'EOF'
# Вставьте содержимое ~/.ssh/flask_helpdesk_deploy.pub
EOF
```

### Шаг 4: Настройка GitLab CI/CD переменных
В GitLab: `Проект -> Settings -> CI/CD -> Variables`

| Переменная | Значение |
|------------|----------|
| `SSH_PRIVATE_KEY` | Содержимое `~/.ssh/flask_helpdesk_deploy` |
| `DEPLOY_SERVER` | IP адрес Red Hat сервера |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_DOMAIN` | `its.tez-tour.com` |

### Шаг 5: Обновление файлов проекта
```bash
# В корне проекта
cp .gitlab-ci-redhat.yml .gitlab-ci.yml
# Файлы flask-helpdesk.service.redhat и flask-helpdesk.nginx.conf уже готовы
```

## 📋 Что изменилось для нового сервера

### Пути
- **Старый**: `/var/www/flask_helpdesk`
- **Новый**: `/opt/www`

### Пользователь
- **Старый**: `www-data`
- **Новый**: `deploy`

### Домен
- **Старый**: не указан
- **Новый**: `its.tez-tour.com`

### Система
- **Старая**: Ubuntu/Debian (apt)
- **Новая**: Red Hat (dnf)

## 🔧 Специальные настройки Red Hat

1. **SELinux** - автоматически настраивается
2. **Firewall** - открыты порты 80, 443, 22
3. **Systemd** - обновленные ExecStartPre директивы
4. **Nginx** - современная SSL конфигурация

## 🚨 Важные моменты

1. **SSL сертификаты** будут получены автоматически через Let's Encrypt
2. **DNS запись** для `its.tez-tour.com` должна указывать на новый сервер
3. **Бэкапы** создаются автоматически в `/opt/backups/flask_helpdesk`
4. **Логи** доступны через `journalctl -u flask-helpdesk -f`

## 🧪 Тестирование деплоя

После первого деплоя проверьте:
```bash
# На сервере
systemctl status flask-helpdesk
systemctl status nginx
curl -I http://localhost/
curl -I https://its.tez-tour.com/
```

## 🆘 Возможные проблемы и решения

### Problem: SELinux блокирует соединения
```bash
sudo setsebool -P httpd_can_network_connect on
sudo setsebool -P httpd_execmem on
```

### Problem: Права доступа к сокету
```bash
sudo chown deploy:nginx /run/gunicorn/
sudo chmod 775 /run/gunicorn/
```

### Problem: SSL сертификат не работает
```bash
sudo certbot --nginx -d its.tez-tour.com
```

### Problem: Нужно добавить SSH ключ
```bash
sudo nano /home/deploy/.ssh/authorized_keys
# Вставьте содержимое публичного ключа
```

## 📞 Контакты и поддержка

- Логи pipeline: GitLab CI/CD -> Pipelines
- Логи сервера: `journalctl -u flask-helpdesk -f`
- Статус: `systemctl status flask-helpdesk nginx`

## ✅ Чеклист финальной проверки

- [ ] SSH ключи созданы и добавлены
- [ ] Сервер настроен скриптом setup-redhat-server.sh
- [ ] DNS запись для its.tez-tour.com настроена
- [ ] Переменные GitLab CI/CD настроены
- [ ] Файл .gitlab-ci.yml обновлен
- [ ] Pipeline запущен и прошел успешно
- [ ] Сайт доступен по https://its.tez-tour.com/
- [ ] SSL сертификат работает
- [ ] Логи не содержат ошибок

---

**Время выполнения**: ~30-60 минут
**Сложность**: Средняя
**Требования**: Sudo доступ к Red Hat серверу, GitLab репозиторий
