# Исправление проблем с правами SSH на Red Hat

## 🚨 Проблема
```bash
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys
chmod: changing permissions of '/home/deploy/.ssh/authorized_keys': Operation not permitted
```

## 🔍 Диагностика

### Шаг 1: Проверяем SELinux
```bash
# Проверяем статус SELinux
getenforce

# Проверяем контекст файла
ls -lZ /home/deploy/.ssh/authorized_keys

# Проверяем контекст директории
ls -ldZ /home/deploy/.ssh/
```

### Шаг 2: Проверяем атрибуты файла
```bash
# Проверяем специальные атрибуты
lsattr /home/deploy/.ssh/authorized_keys

# Проверяем права на директорию
ls -la /home/deploy/.ssh/
```

### Шаг 3: Проверяем владельца и группу
```bash
# Проверяем кто владелец файла
ls -la /home/deploy/.ssh/authorized_keys

# Проверяем существует ли пользователь deploy
id deploy
```

## 🔧 Решения

### Решение 1: Исправление SELinux контекста
```bash
# Если проблема в SELinux, восстанавливаем правильный контекст
sudo restorecon -R /home/deploy/.ssh/

# Или устанавливаем правильный контекст вручную
sudo semanage fcontext -a -t ssh_home_t "/home/deploy/.ssh(/.*)?"
sudo restorecon -R /home/deploy/.ssh/
```

### Решение 2: Удаление специальных атрибутов
```bash
# Если файл имеет атрибут 'i' (immutable), убираем его
sudo chattr -i /home/deploy/.ssh/authorized_keys

# Проверяем что атрибуты убраны
lsattr /home/deploy/.ssh/authorized_keys
```

### Решение 3: Полное пересоздание SSH структуры
```bash
# Удаляем проблемную структуру
sudo rm -rf /home/deploy/.ssh

# Создаем заново с правильными правами
sudo mkdir -p /home/deploy/.ssh
sudo chown deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

# Создаем файл authorized_keys
sudo touch /home/deploy/.ssh/authorized_keys
sudo chown deploy:deploy /home/deploy/.ssh/authorized_keys
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# Устанавливаем правильный SELinux контекст
sudo restorecon -R /home/deploy/.ssh/
```

### Решение 4: Альтернативный способ добавления ключа
```bash
# Создаем ключ напрямую от пользователя deploy
sudo -u deploy bash -c 'mkdir -p /home/deploy/.ssh'
sudo -u deploy bash -c 'chmod 700 /home/deploy/.ssh'
sudo -u deploy bash -c 'touch /home/deploy/.ssh/authorized_keys'
sudo -u deploy bash -c 'chmod 600 /home/deploy/.ssh/authorized_keys'

# Добавляем ключ
echo "ваш_публичный_ключ" | sudo -u deploy tee -a /home/deploy/.ssh/authorized_keys
```

## 🔒 Проверка SELinux (Red Hat специфично)

### Если SELinux в режиме Enforcing:
```bash
# Проверяем SELinux логи
sudo ausearch -m avc -ts recent

# Временно переводим в Permissive (только для диагностики!)
sudo setenforce 0

# Пробуем изменить права
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# Возвращаем Enforcing
sudo setenforce 1

# Если сработало, значит проблема в SELinux контексте
```

### Правильная настройка SELinux для SSH:
```bash
# Устанавливаем правильные контексты
sudo semanage fcontext -a -t ssh_home_t "/home/deploy/.ssh(/.*)?"
sudo restorecon -R /home/deploy/

# Проверяем результат
ls -lZ /home/deploy/.ssh/authorized_keys
```

## 🛠️ Автоматический скрипт исправления

```bash
#!/bin/bash
# fix_ssh_deploy.sh

echo "🔧 Исправляем SSH для пользователя deploy..."

# Удаляем проблемную структуру
sudo rm -rf /home/deploy/.ssh

# Создаем правильную структуру
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh
sudo -u deploy touch /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

# Исправляем SELinux
if command -v restorecon >/dev/null 2>&1; then
    sudo restorecon -R /home/deploy/.ssh/
    echo "✅ SELinux контекст восстановлен"
fi

# Проверяем результат
echo "📋 Результат:"
ls -la /home/deploy/.ssh/
ls -lZ /home/deploy/.ssh/authorized_keys 2>/dev/null || ls -la /home/deploy/.ssh/authorized_keys

echo "✅ SSH структура создана. Теперь добавьте ваш ключ:"
echo "sudo nano /home/deploy/.ssh/authorized_keys"
```

## 🎯 Быстрое решение (рекомендуемое)

Выполните эти команды по порядку:

```bash
# 1. Удаляем проблемную структуру
sudo rm -rf /home/deploy/.ssh

# 2. Создаем правильную структуру от пользователя deploy
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh
sudo -u deploy touch /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

# 3. Исправляем SELinux (если есть)
sudo restorecon -R /home/deploy/.ssh/ 2>/dev/null || true

# 4. Добавляем ваш SSH ключ
sudo nano /home/deploy/.ssh/authorized_keys
```

## ✅ Проверка

После исправления проверьте:
```bash
# Права файлов
ls -la /home/deploy/.ssh/

# SELinux контекст (если применимо)
ls -lZ /home/deploy/.ssh/authorized_keys

# Тест SSH подключения
ssh -i ~/.ssh/your_key deploy@server_ip
```

Попробуйте **Быстрое решение** - оно должно решить проблему в 99% случаев!
