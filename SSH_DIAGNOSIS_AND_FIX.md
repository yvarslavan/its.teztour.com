# Диагностика и исправление проблем SSH для пользователя deploy

## Проблема
```bash
[yvarslavan@its ~]$ ls -la /home/deploy/.ssh/
ls: cannot access '/home/deploy/.ssh/': Permission denied
```

## Пошаговая диагностика и исправление

### Шаг 1: Проверка существования пользователя deploy
```bash
# Проверяем, существует ли пользователь deploy
id deploy

# Если пользователь не существует, создаём его
sudo useradd -m -s /bin/bash deploy
sudo passwd deploy  # Устанавливаем пароль (необязательно для SSH ключей)
```

### Шаг 2: Проверка домашней директории
```bash
# Проверяем права доступа к домашней директории
ls -la /home/ | grep deploy

# Если директория не существует или права неправильные
sudo mkdir -p /home/deploy
sudo chown deploy:deploy /home/deploy
sudo chmod 755 /home/deploy
```

### Шаг 3: Создание SSH директории с правильными правами
```bash
# Создаём .ssh директорию от имени пользователя deploy
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh

# Альтернативно, если предыдущая команда не работает:
sudo mkdir -p /home/deploy/.ssh
sudo chown deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
```

### Шаг 4: Проверка SELinux (специфично для Red Hat)
```bash
# Проверяем статус SELinux
getenforce

# Если SELinux включён, исправляем контекст
sudo restorecon -R /home/deploy/
sudo restorecon -R /home/deploy/.ssh/

# Проверяем SELinux контекст
ls -laZ /home/deploy/.ssh/
```

### Шаг 5: Создание authorized_keys файла
```bash
# Создаём файл authorized_keys от имени пользователя deploy
sudo -u deploy touch /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

# Исправляем SELinux контекст для SSH файлов
sudo restorecon -R /home/deploy/.ssh/
```

### Шаг 6: Добавление публичного ключа
```bash
# Получите публичный ключ из GitLab или создайте новый
# Например, если у вас есть публичный ключ в файле:
sudo -u deploy sh -c 'cat >> /home/deploy/.ssh/authorized_keys' << 'EOF'
# Вставьте здесь ваш публичный SSH ключ
# ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB... your-key-here
EOF
```

### Шаг 7: Проверка SSH конфигурации сервера
```bash
# Проверяем конфигурацию sshd
sudo grep -E "PubkeyAuthentication|AuthorizedKeysFile" /etc/ssh/sshd_config

# Убедитесь, что эти параметры включены:
# PubkeyAuthentication yes
# AuthorizedKeysFile .ssh/authorized_keys

# Если нужно изменить конфигурацию:
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
sudo nano /etc/ssh/sshd_config

# После изменений перезапустите sshd:
sudo systemctl restart sshd
```

### Шаг 8: Полная проверка прав доступа
```bash
# Проверяем все права доступа
ls -la /home/deploy/
ls -la /home/deploy/.ssh/

# Правильные права должны быть:
# drwx------. 2 deploy deploy  4096 дата .ssh
# -rw-------. 1 deploy deploy   xxx дата authorized_keys
```

### Шаг 9: Тестирование SSH подключения
```bash
# Локальное тестирование (с сервера на себя)
ssh -o PreferredAuthentications=publickey deploy@localhost

# Удалённое тестирование (из GitLab CI/CD)
# Добавьте в .gitlab-ci.yml тестовый этап:
```

## Скрипт автоматического исправления

```bash
#!/bin/bash
# fix_deploy_ssh.sh

echo "🔧 Исправление SSH настроек для пользователя deploy..."

# Создаём пользователя если не существует
if ! id deploy &>/dev/null; then
    echo "👤 Создание пользователя deploy..."
    sudo useradd -m -s /bin/bash deploy
fi

# Создаём домашнюю директорию если не существует
sudo mkdir -p /home/deploy
sudo chown deploy:deploy /home/deploy
sudo chmod 755 /home/deploy

# Создаём SSH директорию
sudo rm -rf /home/deploy/.ssh
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh

# Создаём authorized_keys файл
sudo -u deploy touch /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys

# Исправляем SELinux контекст
if command -v getenforce &>/dev/null && [ "$(getenforce)" != "Disabled" ]; then
    echo "🔒 Исправление SELinux контекста..."
    sudo restorecon -R /home/deploy/
fi

# Добавляем deploy в sudoers для управления сервисами
if [ ! -f /etc/sudoers.d/flask-helpdesk ]; then
    echo "⚙️ Настройка sudo прав для deploy..."
    sudo tee /etc/sudoers.d/flask-helpdesk > /dev/null << 'EOF'
deploy ALL=(ALL) NOPASSWD: /bin/systemctl start flask-helpdesk
deploy ALL=(ALL) NOPASSWD: /bin/systemctl stop flask-helpdesk
deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart flask-helpdesk
deploy ALL=(ALL) NOPASSWD: /bin/systemctl reload flask-helpdesk
deploy ALL=(ALL) NOPASSWD: /bin/systemctl status flask-helpdesk
deploy ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
deploy ALL=(ALL) NOPASSWD: /bin/journalctl -u flask-helpdesk*
deploy ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
deploy ALL=(ALL) NOPASSWD: /bin/nginx -t
deploy ALL=(ALL) NOPASSWD: /bin/chown -R www-data:www-data /opt/www*
deploy ALL=(ALL) NOPASSWD: /bin/chmod -R * /opt/www*
deploy ALL=(ALL) NOPASSWD: /bin/mkdir -p /opt/www*
deploy ALL=(ALL) NOPASSWD: /bin/rm -rf /var/backups/flask_helpdesk/backup_*
deploy ALL=(ALL) NOPASSWD: /bin/cp -r * /var/backups/flask_helpdesk/*
deploy ALL=(ALL) NOPASSWD: /bin/rsync -a* /opt/www*
deploy ALL=(ALL) NOPASSWD: /usr/bin/dnf install *
deploy ALL=(ALL) NOPASSWD: /usr/bin/dnf update *
EOF
fi

echo "✅ SSH настройки исправлены!"
echo "📋 Проверка результата:"
ls -la /home/deploy/.ssh/

echo ""
echo "📝 Теперь добавьте публичный ключ в /home/deploy/.ssh/authorized_keys"
echo "💡 Команда для добавления ключа:"
echo "sudo -u deploy nano /home/deploy/.ssh/authorized_keys"
```

## Быстрое исправление одной командой

```bash
# Запустите эту команду для быстрого исправления:
curl -s https://raw.githubusercontent.com/your-repo/scripts/fix_deploy_ssh.sh | sudo bash

# Или создайте локальный скрипт:
sudo tee fix_deploy_ssh.sh > /dev/null << 'EOF'
#!/bin/bash
echo "🔧 Исправление SSH настроек для пользователя deploy..."
if ! id deploy &>/dev/null; then
    sudo useradd -m -s /bin/bash deploy
fi
sudo mkdir -p /home/deploy
sudo chown deploy:deploy /home/deploy
sudo chmod 755 /home/deploy
sudo rm -rf /home/deploy/.ssh
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy chmod 700 /home/deploy/.ssh
sudo -u deploy touch /home/deploy/.ssh/authorized_keys
sudo -u deploy chmod 600 /home/deploy/.ssh/authorized_keys
if command -v getenforce &>/dev/null && [ "$(getenforce)" != "Disabled" ]; then
    sudo restorecon -R /home/deploy/
fi
echo "✅ SSH настройки исправлены!"
ls -la /home/deploy/.ssh/
EOF

chmod +x fix_deploy_ssh.sh
sudo ./fix_deploy_ssh.sh
```

## Следующие шаги после исправления

1. **Добавьте публичный ключ** в `/home/deploy/.ssh/authorized_keys`
2. **Обновите GitLab CI/CD переменные** с приватным ключом
3. **Протестируйте SSH подключение** из GitLab
4. **Запустите деплой pipeline**

## Проверка успешности исправления

```bash
# Эти команды должны работать без ошибок:
ls -la /home/deploy/.ssh/
sudo -u deploy ls -la /home/deploy/.ssh/
ssh-keygen -l -f /home/deploy/.ssh/authorized_keys  # после добавления ключа
```
