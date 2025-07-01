# 🚀 Ручной деплой Flask Helpdesk на Red Hat сервер

**Используйте это руководство, если GitLab CI/CD не работает.**

## 📋 **Предварительные требования**

✅ Сервер настроен: `10.7.74.252`
✅ Пользователь: `deploy`
✅ SSH ключи настроены
✅ Nginx работает

## 🔧 **Шаг 1: Подготовка файлов локально**

### На вашем компьютере:

```bash
# Перейдите в директорию проекта
cd C:\Users\VARSLAVAN.DESKTOP-MNJ5CKG\PythonProjects\flask_helpdesk

# Создайте папку для деплоя
mkdir deployment_manual

# Скопируйте основные файлы
copy app.py deployment_manual\
copy requirements.txt deployment_manual\
copy config.ini deployment_manual\
copy *.py deployment_manual\

# Скопируйте директории (если есть)
xcopy /E /I blog deployment_manual\blog
xcopy /E /I static deployment_manual\static
xcopy /E /I templates deployment_manual\templates
xcopy /E /I migrations deployment_manual\migrations

# Скопируйте конфигурационные файлы
copy flask-helpdesk.service.redhat deployment_manual\flask-helpdesk.service
copy flask-helpdesk.nginx.conf deployment_manual\
```

### Создайте архив:

```bash
# С помощью 7-Zip или WinRAR создайте архив
# deployment_manual.tar.gz содержащий всё из папки deployment_manual
```

## 🔧 **Шаг 2: Передача файлов на сервер**

### Вариант A: SCP (рекомендуется)

```bash
# Передайте архив на сервер
scp deployment_manual.tar.gz deploy@10.7.74.252:/tmp/

# Подключитесь к серверу
ssh deploy@10.7.74.252
```

### Вариант B: Через WinSCP
1. Откройте **WinSCP**
2. Подключитесь к `10.7.74.252` под пользователем `deploy`
3. Загрузите `deployment_manual.tar.gz` в папку `/tmp/`

## 🔧 **Шаг 3: Деплой на сервере**

### Подключитесь к серверу:

```bash
ssh deploy@10.7.74.252
```

### Выполните деплой:

```bash
# 1. Остановите сервис
sudo systemctl stop flask-helpdesk

# 2. Создайте бэкап (необязательно)
sudo mkdir -p /opt/backups/flask_helpdesk
sudo cp -r /opt/www /opt/backups/flask_helpdesk/backup_$(date +%Y%m%d_%H%M%S)

# 3. Перейдите в рабочую директорию
cd /opt/www

# 4. Распакуйте новые файлы
sudo tar -xzf /tmp/deployment_manual.tar.gz

# 5. Установите права доступа
sudo chown -R deploy:deploy /opt/www
sudo chmod -R 755 /opt/www

# 6. Установите Python зависимости (если нужно)
sudo python3 -m pip install -r requirements.txt

# 7. Запустите сервис
sudo systemctl start flask-helpdesk
sudo systemctl enable flask-helpdesk

# 8. Проверьте статус
sudo systemctl status flask-helpdesk
```

## 🔧 **Шаг 4: Проверка деплоя**

### На сервере:

```bash
# Проверьте статус сервиса
sudo systemctl status flask-helpdesk

# Проверьте логи
sudo journalctl -u flask-helpdesk -f

# Проверьте файлы
ls -la /opt/www/

# Проверьте порты
sudo netstat -tlnp | grep :5000
```

### С вашего компьютера:

```bash
# Проверьте HTTP ответ
curl -I http://its.tez-tour.com

# Или откройте в браузере
http://its.tez-tour.com
```

## 🚨 **Устранение проблем**

### Если сервис не запускается:

```bash
# Проверьте логи
sudo journalctl -u flask-helpdesk --no-pager -l

# Проверьте конфигурацию
sudo systemctl daemon-reload
sudo systemctl restart flask-helpdesk
```

### Если нет доступа к сайту:

```bash
# Проверьте Nginx
sudo systemctl status nginx
sudo nginx -t

# Проверьте firewall
sudo firewall-cmd --list-all
```

### Проверьте права доступа:

```bash
# Права на файлы
sudo ls -la /opt/www/
sudo chown -R deploy:deploy /opt/www
sudo chmod -R 755 /opt/www
```

## 📋 **Полный скрипт автоматического деплоя**

Создайте файл `deploy.sh`:

```bash
#!/bin/bash
echo "🚀 Ручной деплой Flask Helpdesk..."

# Остановить сервис
sudo systemctl stop flask-helpdesk

# Бэкап
sudo mkdir -p /opt/backups/flask_helpdesk
sudo cp -r /opt/www /opt/backups/flask_helpdesk/backup_$(date +%Y%m%d_%H%M%S)

# Деплой
cd /opt/www
sudo tar -xzf /tmp/deployment_manual.tar.gz
sudo chown -R deploy:deploy /opt/www
sudo chmod -R 755 /opt/www

# Запуск
sudo systemctl start flask-helpdesk
sudo systemctl enable flask-helpdesk

# Проверка
echo "✅ Деплой завершен"
echo "🔍 Статус сервиса:"
sudo systemctl status flask-helpdesk
```

Выполните:

```bash
chmod +x deploy.sh
./deploy.sh
```

## 🎯 **Контрольный список успешного деплоя**

- [ ] ✅ Файлы переданы на сервер
- [ ] ✅ Архив распакован в `/opt/www`
- [ ] ✅ Права доступа установлены
- [ ] ✅ Сервис `flask-helpdesk` запущен
- [ ] ✅ Сайт доступен по адресу `http://its.tez-tour.com`
- [ ] ✅ Логи сервиса без ошибок

---

**💡 Этот способ гарантированно работает даже если GitLab CI/CD недоступен!**
