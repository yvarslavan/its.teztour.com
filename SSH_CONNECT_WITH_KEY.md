# 🔑 SSH подключение с приватным ключом

## 🚨 Проблема
SSH подключение по паролю не работает:
```
deploy@its.tez-tour.com: Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password)
```

## ✅ Решение: Используем SSH ключ

### 1. Создаем файл с приватным ключом

**На вашем локальном компьютере:**

```bash
# Создаем SSH ключ файл
mkdir -p ~/.ssh
nano ~/.ssh/flask_deploy_key
```

**Скопируйте в файл следующий приватный ключ:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

### 2. Настраиваем права доступа к ключу

```bash
# Устанавливаем правильные права
chmod 600 ~/.ssh/flask_deploy_key
```

### 3. Подключаемся с использованием ключа

```bash
# SSH подключение с указанием ключа
ssh -i ~/.ssh/flask_deploy_key deploy@its.tez-tour.com

# Или с IP адресом
ssh -i ~/.ssh/flask_deploy_key deploy@10.7.74.252
```

### 4. Альтернативный способ - добавить ключ в SSH agent

```bash
# Добавляем ключ в SSH agent
ssh-add ~/.ssh/flask_deploy_key

# Теперь можно подключаться без указания ключа
ssh deploy@its.tez-tour.com
```

## 🔧 Для Windows пользователей

### Через WSL/Linux subsystem:
Используйте команды выше в WSL

### Через PuTTY:
1. Установите **PuTTYgen**
2. Импортируйте приватный ключ
3. Сохраните в формате .ppk
4. Используйте в PuTTY

### Через Git Bash:
```bash
# В Git Bash выполните команды выше
ssh -i ~/.ssh/flask_deploy_key deploy@its.tez-tour.com
```

## ✅ Проверка подключения

После успешного подключения вы должны увидеть:

```bash
[deploy@its ~]$
```

Теперь можете проверить:

```bash
# Проверить текущие сервисы
sudo systemctl status nginx
sudo systemctl status flask-helpdesk

# Проверить права доступа
ls -la /opt/www/

# Проверить SSH ключи
ls -la ~/.ssh/
```

## 🚀 После успешного подключения

1. **Установите GitLab Runner** (если планируете локальный runner)
2. **Настройте GitLab CI/CD переменные**
3. **Запустите deployment pipeline**

## 📝 Важные команды для диагностики

```bash
# Проверка SSH подключения
ssh -v -i ~/.ssh/flask_deploy_key deploy@its.tez-tour.com

# Проверка DNS
nslookup its.tez-tour.com

# Проверка порта SSH
telnet its.tez-tour.com 22
```

---

**Теперь SSH подключение должно работать!** 🎉
