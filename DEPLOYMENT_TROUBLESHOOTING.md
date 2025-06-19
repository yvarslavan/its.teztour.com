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
