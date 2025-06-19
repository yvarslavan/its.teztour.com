# 🏃‍♂️ Настройка GitHub Self-Hosted Runner

## ✅ **Преимущества self-hosted runner:**

- 🌐 **Прямой доступ к внутренней сети** - обход VPN/firewall проблем
- 🚀 **Быстрее деплой** - нет загрузки зависимостей
- 🔧 **Полный контроль** - настройка окружения под свои нужды
- 💰 **Экономия** - не тратятся GitHub Actions minutes

## 📋 **Шаги настройки:**

### 1️⃣ **Добавление runner в GitHub**

1. Перейдите в настройки репозитория: **Settings** → **Actions** → **Runners**
2. Нажмите **"New self-hosted runner"**
3. Выберите операционную систему (Linux/Windows/macOS)
4. Скопируйте команды для установки

### 2️⃣ **Установка на сервер**

#### **Linux (Ubuntu/Debian):**
```bash
# Создание пользователя для runner (рекомендуется)
sudo useradd -m -s /bin/bash github-runner
sudo usermod -aG docker github-runner  # Если нужен Docker

# Переключение на пользователя runner
sudo su - github-runner

# Создание папки для runner
mkdir actions-runner && cd actions-runner

# Скачивание runner (команды из GitHub)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Конфигурация (используйте токен из GitHub)
./config.sh --url https://github.com/ваш-username/flask_helpdesk --token ВАШИ_ТОКЕН

# Установка как сервис
sudo ./svc.sh install
sudo ./svc.sh start
```

#### **Windows:**
```powershell
# Запустить PowerShell как Администратор
mkdir c:\actions-runner ; cd c:\actions-runner

# Скачать runner
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner-win-x64-2.311.0.zip
Expand-Archive -Path actions-runner-win-x64-2.311.0.zip -DestinationPath .

# Конфигурация
.\config.cmd --url https://github.com/ваш-username/flask_helpdesk --token ВАШИ_ТОКЕН

# Установка как сервис
.\svc.sh install
.\svc.sh start
```

### 3️⃣ **Настройка окружения**

#### **Установка Python и зависимостей:**
```bash
# Python и pip
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y

# Если нужен Node.js для фронтенда
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Проверка установки
python3 --version
pip3 --version
git --version
```

#### **Права доступа:**
```bash
# Добавление runner в группы (если нужно)
sudo usermod -aG www-data github-runner  # Для доступа к веб-папкам
sudo usermod -aG sudo github-runner      # Для sudo (осторожно!)

# Настройка SSH ключей (если нужно деплоить на другие сервера)
sudo su - github-runner
ssh-keygen -t ed25519 -C "github-runner@$(hostname)"
# Добавить публичный ключ на целевые servers
```

### 4️⃣ **Проверка работы**

#### **Тест runner:**
```bash
# Проверить статус
sudo systemctl status actions.runner.ваш-username-flask_helpdesk.service

# Просмотр логов
sudo journalctl -u actions.runner.ваш-username-flask_helpdesk.service -f

# Перезапуск при необходимости
sudo systemctl restart actions.runner.ваш-username-flask_helpdesk.service
```

## 🔧 **Конфигурация workflow**

### **Изменения в .github/workflows/deploy.yml:**
```yaml
jobs:
  test:
    runs-on: self-hosted  # ✅ Уже настроено
    # ...

  deploy:
    runs-on: self-hosted  # ✅ Уже настроено
    # ...
```

### **Дополнительные настройки:**
```yaml
# Если нужны определенные labels для runner
jobs:
  deploy:
    runs-on: [self-hosted, linux, production]  # С labels
```

## 🛡️ **Безопасность**

### **Рекомендации:**
1. **Отдельный пользователь** - не запускайте runner от root
2. **Ограниченные права** - минимально необходимые permissions
3. **Firewall** - закройте ненужные порты
4. **Обновления** - регулярно обновляйте runner
5. **Мониторинг** - следите за логами

### **Секреты и переменные:**
```bash
# Переменные окружения для runner
# Можно настроить в systemd service или .env файле
FLASK_ENV=production
DATABASE_URL=sqlite:///site.db
SECRET_KEY=ваш-секретный-ключ
```

## 🔍 **Диагностика проблем**

### **Типичные ошибки:**
```bash
# Runner не подключается
sudo systemctl status actions.runner.*
sudo journalctl -u actions.runner.* -n 50

# Проблемы с правами
ls -la /home/github-runner/actions-runner/
sudo chown -R github-runner:github-runner /home/github-runner/

# Проблемы с Python/зависимостями
which python3
pip3 list
```

### **Полезные команды:**
```bash
# Информация о системе
uname -a
cat /etc/os-release
df -h
free -h

# Сетевые подключения
ss -tulpn | grep :80
curl -I http://localhost:5000
```

## 🚀 **Готово!**

После настройки self-hosted runner:
1. ✅ Workflow будет выполняться на вашем сервере
2. ✅ Прямой доступ к внутренней сети
3. ✅ Быстрое выполнение без загрузки зависимостей
4. ✅ Возможность деплоя без SSH (прямо на том же сервере)

**Commit изменения и проверьте работу workflow!**
