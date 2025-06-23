# 🚨 Руководство по устранению проблем с деплоем

## 📋 Анализ текущей ошибки

### Проблема
```
❌ Port 22 is not accessible
🔍 Testing server connectivity...
Server host: vpn-130.msk.tez-tour.com
SSH port: 22
⚠️ Server doesn't respond to ping (may be blocked by firewall)
```

### 🎯 Основные причины

1. **Сервер за VPN** - Hostname содержит `vpn-130`, что указывает на внутреннюю сеть
2. **Нестандартный SSH порт** - Возможно SSH работает не на порту 22
3. **Firewall блокирует GitHub Actions** - Внешние подключения заблокированы
4. **SSH служба неактивна** - Сервис может быть остановлен

## 🛠️ Методы решения

### 1️⃣ **Проверка SSH порта (Быстрое решение)**

#### Проверьте GitHub Secrets:
```bash
# В настройках репозитория -> Settings -> Secrets and variables -> Actions
SSH_HOST=vpn-130.msk.tez-tour.com
SSH_PORT=22  # ← Возможно нужно изменить
SSH_USER=ваш_пользователь
SSH_PRIVATE_KEY=ваш_приватный_ключ
```

#### Распространенные SSH порты:
- `22` (стандартный)
- `2222` (альтернативный)
- `2022`, `22022`, `22222`
- `2020`, `2021`, `2023`

### 2️⃣ **Диагностика подключения**

#### Запустите тестовый workflow:
1. Перейдите в **Actions** → **SSH Connection Test**
2. Нажмите **Run workflow**
3. Включите опцию **"Test all common SSH ports"**
4. Анализируйте результаты

### 3️⃣ **Решения для VPN-сервера**

#### А) GitHub Self-Hosted Runner (Рекомендуется)
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: self-hosted  # Вместо ubuntu-latest
    # ... остальная конфигурация
```

**Установка runner внутри сети:**
1. Settings → Actions → Runners → New self-hosted runner
2. Следуйте инструкциям для установки на сервер
3. Runner будет иметь доступ к внутренней сети

#### Б) VPN-подключение в workflow
```yaml
- name: Connect to VPN
  uses: "kota65535/github-openvpn-connect-action@v2"
  with:
    config_file: ${{ secrets.OPENVPN_CONFIG }}
    username: ${{ secrets.OPENVPN_USERNAME }}
    password: ${{ secrets.OPENVPN_PASSWORD }}
```

#### В) SSH через Bastion Host
```yaml
- name: Deploy via bastion
  run: |
    ssh -o StrictHostKeyChecking=no \
        -o ProxyCommand="ssh -W %h:%p bastion-host" \
        user@internal-server 'deployment-script.sh'
```

### 4️⃣ **Конфигурация Firewall**

#### На сервере (Ubuntu/Debian):
```bash
# Разрешить SSH с GitHub Actions IP ranges
sudo ufw allow from 140.82.112.0/20 to any port 22
sudo ufw allow from 143.55.64.0/20 to any port 22
sudo ufw allow from 185.199.108.0/22 to any port 22
sudo ufw allow from 192.30.252.0/22 to any port 22

# Проверить статус SSH
sudo systemctl status ssh
sudo systemctl restart ssh
```

#### Проверка SSH конфигурации:
```bash
# /etc/ssh/sshd_config
Port 22                    # ← Убедитесь в правильности порта
PermitRootLogin no         # Рекомендуется
PasswordAuthentication no  # Только ключи
PubkeyAuthentication yes
```

### 5️⃣ **Альтернативные методы деплоя**

#### А) Webhook-based деплой
```python
# webhook_deploy.py на сервере
from flask import Flask, request
import subprocess
import hmac
import hashlib

app = Flask(__name__)

@app.route('/deploy', methods=['POST'])
def deploy():
    # Проверка GitHub webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if verify_signature(request.data, signature):
        subprocess.run(['./deploy.sh'])
        return 'Deployed successfully'
    return 'Unauthorized', 403
```

#### Б) Pull-based деплой (cron)
```bash
# На сервере: crontab -e
*/5 * * * * cd /var/www/flask_helpdesk && git pull origin main && ./auto-deploy.sh
```

## 🔧 Немедленные действия

### 1. Проверьте SSH порт
```bash
# С вашего локального компьютера (если есть доступ к сети):
ssh -p 22 пользователь@vpn-130.msk.tez-tour.com
ssh -p 2222 пользователь@vpn-130.msk.tez-tour.com  # Попробуйте разные порты
```

### 2. Обратитесь к системному администратору
**Вопросы для админа:**
- На каком порту работает SSH?
- Можно ли разрешить доступ с GitHub Actions IP?
- Есть ли возможность установить self-hosted runner?
- Какая сетевая архитектура используется?

### 3. Временное решение
Пока не настроен автодеплой, используйте ручной деплой:
```bash
# Локально после push в main:
ssh пользователь@сервер "cd /var/www/flask_helpdesk && git pull && systemctl restart app"
```

## 📞 Контакты для решения

1. **IT отдел** - конфигурация сети и firewall
2. **DevOps** - настройка CI/CD и runner'ов
3. **Системный администратор** - SSH и сервисы

## 🎯 Рекомендуемое решение

**Для корпоративной среды лучший вариант:**
1. Установить **GitHub Self-Hosted Runner** на сервер внутри сети
2. Настроить его как сервис
3. Использовать локальные ресурсы для деплоя

Это решает проблемы с VPN, firewall и обеспечивает безопасность.

# Устранение проблем развертывания Flask Helpdesk

## Обзор проблем

При развертывании через GitLab CI/CD возникают следующие основные проблемы:

1. **Проблемы с правами доступа** - файлы flask_session и __pycache__ принадлежат www-data
2. **Проблемы с sudo** - CI/CD не может выполнять команды sudo без пароля
3. **Переполнение диска** - множественные бэкапы занимают все место
4. **SSH ключи в after_script** - ключи не доступны в секции after_script

## Решения проблем

### 1. Проблемы с правами доступа

#### Проблема
```
cp: cannot open 'flask_helpdesk/flask_session/xxx' for reading: Permission denied
rm: cannot remove '/var/www/flask_helpdesk/flask_session/xxx': Permission denied
```

#### Причина
Файлы сессий создаются веб-сервером (www-data), а развертывание выполняется от пользователя yvarslavan.

#### Решения

**A. Автоматическое решение в CI/CD:**
```yaml
# В .gitlab-ci.yml добавлено безопасное удаление
- echo "Safely cleaning up old deployment files..."
- ssh $DEPLOY_USER@$DEPLOY_HOST "find /var/www/flask_helpdesk/flask_session -type f -delete 2>/dev/null || echo 'Some flask_session files could not be removed'"
```

**B. Ручное решение на сервере:**
```bash
# Запуск скрипта очистки
cd /var/www/flask_helpdesk
python3 scripts/server_cleanup.py sessions

# Или изменение прав доступа (требует sudo)
sudo chown -R yvarslavan:yvarslavan /var/www/flask_helpdesk/flask_session
sudo chmod -R u+w /var/www/flask_helpdesk/flask_session
```

### 2. Проблемы с sudo

#### Проблема
```
sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
```

#### Причина
CI/CD пытается выполнить sudo команды, но не может предоставить пароль.

#### Решение
Убраны все sudo команды из CI/CD. Вместо этого:
- Удаление файлов без sudo (с обработкой ошибок)
- Инструкции для ручного выполнения sudo команд после развертывания

```yaml
# Вместо sudo rm -rf используется
- ssh $DEPLOY_USER@$DEPLOY_HOST "rm -rf /tmp/flask* || true"

# И выводятся инструкции
- echo "⚠️  MANUAL ACTION REQUIRED:"
- echo "   sudo systemctl restart flask-helpdesk"
- echo "   sudo chown -R www-data:www-data /var/www/flask_helpdesk/flask_session"
```

### 3. Переполнение диска

#### Проблема
Диск 25GB заполнен на 100% из-за множественных бэкапов.

#### Диагностика
```bash
df -h                                    # Проверка места на диске
du -sh /var/www/flask_helpdesk_backup_*  # Размер бэкапов
```

#### Решение
```bash
# Удаление всех старых бэкапов
sudo rm -rf /var/www/flask_helpdesk_backup_*

# Или использование скрипта очистки
cd /var/www/flask_helpdesk
python3 scripts/server_cleanup.py disk
```

### 4. SSH ключи в after_script

#### Проблема
```
Permission denied (publickey,password)
```

#### Причина
SSH ключи не доступны в секции after_script.

#### Решение
Добавлена повторная инициализация SSH в after_script:

```yaml
after_script:
  - echo "Running after_script cleanup..."
  - eval $(ssh-agent -s) || true
  - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add - || true
  - |
    if [ "$CI_JOB_STATUS" == "failed" ]; then
      # ... rollback logic
    fi
```

## Инструменты для устранения проблем

### 1. Скрипт очистки сервера

Создан `scripts/server_cleanup.py` для решения проблем с правами доступа:

```bash
# Полная очистка
python3 scripts/server_cleanup.py

# Отдельные команды
python3 scripts/server_cleanup.py check      # Проверка прав доступа
python3 scripts/server_cleanup.py sessions  # Очистка flask_session
python3 scripts/server_cleanup.py cache     # Очистка __pycache__
python3 scripts/server_cleanup.py disk      # Проверка диска
```

### 2. Обновленный CI/CD pipeline

Исправленный `.gitlab-ci.yml`:
- Убраны команды sudo
- Добавлена безопасная очистка файлов
- Исправлен after_script с SSH ключами
- Добавлены проверки диска

## Пошаговое решение текущих проблем

### Шаг 1: Очистка диска на сервере
```bash
# Подключение к серверу
ssh yvarslavan@10.7.74.252

# Проверка места
df -h

# Удаление старых бэкапов (ВНИМАНИЕ: это удалит все бэкапы!)
sudo rm -rf /var/www/flask_helpdesk_backup_*

# Очистка временных файлов
rm -rf /tmp/flask*

# Проверка результата
df -h
```

### Шаг 2: Очистка проблемных файлов
```bash
# Переход в директорию приложения
cd /var/www/flask_helpdesk

# Запуск скрипта очистки
python3 scripts/server_cleanup.py

# Или ручная очистка
sudo rm -rf flask_session/*
sudo rm -rf __pycache__/
find . -name "*.pyc" -delete
```

### Шаг 3: Настройка прав доступа
```bash
# Создание директорий с правильными правами
mkdir -p flask_session logs
chmod 755 flask_session logs

# Установка владельца для веб-сервера
sudo chown -R www-data:www-data flask_session logs
```

### Шаг 4: Повторный запуск развертывания
После очистки диска можно повторно запустить развертывание через GitLab CI/CD.

## Мониторинг и предотвращение проблем

### 1. Регулярная очистка
```bash
# Добавить в cron для еженедельной очистки
0 2 * * 0 cd /var/www/flask_helpdesk && python3 scripts/server_cleanup.py
```

### 2. Мониторинг диска
```bash
# Проверка места на диске
df -h | grep -E "(Filesystem|/dev/mapper)"

# Поиск больших файлов
du -sh /var/www/* | sort -hr | head -10
```

### 3. Проверка логов
```bash
# Проверка логов развертывания
journalctl -u flask-helpdesk -f

# Проверка логов приложения
tail -f /var/www/flask_helpdesk/logs/app.log
```

## Контрольный список перед развертыванием

- [ ] Проверить свободное место на диске (должно быть >2GB)
- [ ] Убедиться в отсутствии старых бэкапов
- [ ] Проверить права доступа к flask_session
- [ ] Убедиться в работоспособности SSH ключей
- [ ] Проверить статус systemd сервиса

## Экстренное восстановление

Если развертывание полностью сломало приложение:

```bash
# 1. Остановить сервис
sudo systemctl stop flask-helpdesk

# 2. Восстановить из бэкапа (если есть)
cd /var/www
sudo mv flask_helpdesk flask_helpdesk_broken
sudo mv flask_helpdesk_backup flask_helpdesk

# 3. Запустить сервис
sudo systemctl start flask-helpdesk

# 4. Проверить статус
sudo systemctl status flask-helpdesk
```

## Контакты для поддержки

При возникновении критических проблем:
1. Проверить логи GitLab CI/CD
2. Проверить логи сервера: `journalctl -u flask-helpdesk -f`
3. Запустить диагностику: `python3 scripts/server_cleanup.py check`
4. При необходимости выполнить откат к предыдущей версии
