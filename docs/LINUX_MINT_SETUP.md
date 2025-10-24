# 🐧 Инструкция по развертыванию Flask Helpdesk на Linux Mint

## 📋 Содержание

- [Подготовка системы](#1-подготовка-системы)
- [Клонирование проекта](#2-клонирование-проекта)
- [Настройка виртуального окружения](#3-настройка-виртуального-окружения)
- [Установка зависимостей](#4-установка-зависимостей)
- [Настройка конфигурации](#5-настройка-конфигурации)
- [Инициализация базы данных](#6-инициализация-базы-данных)
- [Запуск приложения](#7-запуск-приложения)
- [Настройка IDE](#8-настройка-ide)
- [Проверка работы](#9-проверка-работы)
- [Полезные команды](#10-полезные-команды-для-разработки)
- [Решение проблем](#-возможные-проблемы-и-решения)

## 1. Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.12 python3.12-venv python3-pip git curl wget

# Установка Node.js (для тестов)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Установка MySQL (если нужна интеграция с Redmine)
sudo apt install -y mysql-server mysql-client
```

## 2. Клонирование проекта

```bash
# Клонирование репозитория
git clone https://github.com/your-username/its.teztour.com.git
cd its.teztour.com

# Проверка структуры проекта
ls -la
```

## 3. Настройка виртуального окружения

```bash
# Создание виртуального окружения с Python 3.12
python3.12 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

## 4. Установка зависимостей

```bash
# Установка зависимостей из requirements.txt
pip install -r requirements.txt

# Альтернативно, если используете UV (рекомендуется)
# curl -LsSf https://astral.sh/uv/install.sh | sh
# uv pip install -r requirements.txt
```

## 5. Настройка конфигурации

```bash
# Создание файла конфигурации
cp .env.example .env  # если есть пример
# или создайте .env файл вручную

# Редактирование конфигурации
nano .env
```

### Пример содержимого .env файла:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# База данных
DATABASE_URL=sqlite:///blog.db

# MySQL (для Redmine)
MYSQL_HOST=localhost
MYSQL_USER=redmine_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=redmine

# Redmine
REDMINE_URL=https://your-redmine.com
REDMINE_API_KEY=your-api-key

# Oracle ERP (если используется)
ORACLE_HOST=your-oracle-host
ORACLE_PORT=1521
ORACLE_SERVICE=your-service
ORACLE_USER=your-user
ORACLE_PASSWORD=your-password

# Уведомления
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
```

## 6. Инициализация базы данных

```bash
# Инициализация миграций (если используется Flask-Migrate)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Или создание базы данных вручную
python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## 7. Запуск приложения

```bash
# Запуск в режиме разработки
python app.py

# Или через Flask CLI
flask run --host=0.0.0.0 --port=5000
```

## 8. Настройка IDE

### VS Code (рекомендуется)

```bash
# Установка VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code

# Установка полезных расширений
code --install-extension ms-python.python
code --install-extension ms-python.flask
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-python.pylint
code --install-extension ms-python.black-formatter
```

### PyCharm Community

```bash
# Скачивание и установка PyCharm
wget https://download.jetbrains.com/python/pycharm-community-2024.1.tar.gz
tar -xzf pycharm-community-2024.1.tar.gz
sudo mv pycharm-community-2024.1 /opt/pycharm
sudo ln -s /opt/pycharm/bin/pycharm.sh /usr/local/bin/pycharm

# Запуск PyCharm
pycharm
```

### Настройка проекта в IDE

1. **Откройте папку проекта** в выбранной IDE
2. **Выберите интерпретатор Python** из виртуального окружения (`venv/bin/python`)
3. **Настройте переменные окружения** (если IDE поддерживает)
4. **Установите расширения** для Python и Flask

## 9. Проверка работы

```bash
# Проверка доступности приложения
curl http://localhost:5000

# Проверка логов
tail -f logs/app.log

# Проверка статуса базы данных
python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); print('База данных:', db.engine.url)"
```

## 10. Полезные команды для разработки

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск тестов
pytest tests/

# Проверка качества кода
flake8 blog/
black blog/
mypy blog/

# Запуск в продакшн режиме
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application

# Создание резервной копии базы данных
cp blog/db/blog.db backups/blog_backup_$(date +%Y%m%d_%H%M%S).db
```

## 🔧 Возможные проблемы и решения

### Ошибка с cx_Oracle
```bash
# Установка Oracle Instant Client
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.1.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-21.1.0.0.0dbru.zip
sudo mv instantclient_21_1 /opt/oracle
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Проблемы с MySQL
```bash
# Проверка статуса MySQL
sudo systemctl status mysql

# Запуск MySQL
sudo systemctl start mysql

# Настройка MySQL
sudo mysql_secure_installation
```

### Ошибки импорта
```bash
# Убедитесь, что виртуальное окружение активировано
which python
# Должно показать путь к venv/bin/python

# Переустановка зависимостей
pip install --force-reinstall -r requirements.txt
```

### Проблемы с правами доступа
```bash
# Установка правильных прав на файлы
chmod +x app.py
chmod -R 755 blog/
chmod -R 755 static/
```

## 📱 Доступ к приложению

После успешного запуска приложение будет доступно по адресам:

- **Локальный доступ**: http://localhost:5000
- **Внутренний доступ**: http://127.0.0.1:5000
- **Внешний доступ**: http://your-server-ip:5000

### Основные страницы:

- `/tasks/my-tasks` - управление задачами
- `/users/login` - авторизация пользователей
- `/admin` - административная панель
- `/issues` - система тикетов
- `/notifications` - уведомления

## 🚀 Быстрый старт (краткая версия)

```bash
# 1. Клонирование и настройка
git clone https://github.com/your-username/its.teztour.com.git
cd its.teztour.com

# 2. Виртуальное окружение
python3.12 -m venv venv
source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Конфигурация
cp .env.example .env  # отредактируйте файл

# 5. База данных
python -c "from blog import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 6. Запуск
python app.py
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи в папке `logs/`
2. Убедитесь, что все зависимости установлены
3. Проверьте настройки в файле `.env`
4. Создайте issue в репозитории проекта

---

**Версия инструкции**: 1.0
**Дата создания**: 2024
**Совместимость**: Linux Mint 20+, Python 3.12+
