# 🚀 Flask Helpdesk System

Современная система управления задачами и тикетами на базе Flask с интеграцией Redmine, Oracle ERP и расширенными возможностями уведомлений.

## 📋 Содержание

- [🚀 Быстрый старт](#-быстрый-старт)
- [✨ Ключевые возможности](#-ключевые-возможности)
- [🏗️ Архитектура](#️-архитектура)
- [🔧 Установка и настройка](#-установка-и-настройка)
- [📚 Документация](#-документация)
- [🧪 Тестирование](#-тестирование)
- [🚀 Развертывание](#-развертывание)
- [🤝 Участие в разработке](#-участие-в-разработке)

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- MySQL 5.7+ (для Redmine)
- SQLite (локальная БД)
- Node.js 14+ (для тестов)

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd flask_helpdesk

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Инициализация базы данных
flask db upgrade

# Запуск приложения
python app.py
```

### Первый запуск

1. Откройте http://localhost:5000
2. Создайте первого пользователя через админ-панель
3. Настройте интеграции с Redmine и Oracle ERP
4. Проверьте работу уведомлений

## ✨ Ключевые возможности

### 🎯 Управление задачами
- **Kanban-доска** с drag & drop
- **Система приоритетов** и статусов
- **Назначение исполнителей** с уведомлениями
- **Комментарии и история** изменений
- **Фильтрация и поиск** задач

### 🔔 Система уведомлений
- **Браузерные push-уведомления**
- **WebSocket в реальном времени**
- **Email уведомления**
- **Звуковые оповещения**
- **Настраиваемые предпочтения**

### 🔗 Интеграции
- **Redmine API** - синхронизация задач
- **Oracle ERP** - аутентификация пользователей
- **MySQL** - хранение данных Redmine
- **SQLite** - локальная база данных

### 🎨 Пользовательский интерфейс
- **Адаптивный дизайн** (Bootstrap 5)
- **Темная/светлая тема**
- **Splash screen** с анимацией
- **Интерактивные подсказки**
- **Оптимизированная производительность**

## 🏗️ Архитектура

```
flask_helpdesk/
├── blog/                    # Основное приложение Flask
│   ├── __init__.py         # Фабрика приложения
│   ├── models.py           # SQLAlchemy модели
│   ├── tasks/              # Модуль управления задачами
│   ├── users/              # Модуль пользователей
│   └── notification_service.py  # Сервис уведомлений
├── docs/                   # Документация
├── tests/                  # Тесты
├── scripts/                # Скрипты развертывания
├── app.py                  # Точка входа для разработки
├── wsgi.py                 # WSGI для продакшена
└── requirements.txt        # Зависимости Python
```

### Технологический стек

- **Backend**: Flask, SQLAlchemy, APScheduler
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Базы данных**: SQLite, MySQL
- **Уведомления**: WebSocket, pywebpush
- **Тестирование**: Pytest, Playwright
- **Развертывание**: Docker, Nginx

## 🔧 Установка и настройка

### Конфигурация

Создайте файл `.env` с настройками:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key

# База данных
DATABASE_URL=sqlite:///blog.db
MYSQL_HOST=localhost
MYSQL_USER=redmine_user
MYSQL_PASSWORD=password
MYSQL_DATABASE=redmine

# Redmine
REDMINE_URL=https://your-redmine.com
REDMINE_API_KEY=your-api-key

# Oracle ERP
ORACLE_HOST=your-oracle-host
ORACLE_PORT=1521
ORACLE_SERVICE=your-service
ORACLE_USER=your-user
ORACLE_PASSWORD=your-password

# Уведомления
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
```

### Настройка интеграций

#### Redmine
1. Получите API ключ в настройках Redmine
2. Настройте доступ к MySQL базе Redmine
3. Проверьте подключение через `/admin/redmine-test`

#### Oracle ERP
1. Настройте подключение к Oracle
2. Проверьте аутентификацию пользователей
3. Настройте синхронизацию данных

## 📚 Документация

Полная документация доступна в папке [`docs/`](docs/):

- **[API Документация](docs/API_DOCUMENTATION.md)** - Полное описание API
- **[Быстрый справочник](docs/QUICK_REFERENCE.md)** - Основные команды и примеры
- **[Руководство разработчика](docs/CONTRIBUTING.md)** - Стандарты кода и процесс разработки
- **[История изменений](docs/CHANGELOG.md)** - Версии и обновления

## 🧪 Тестирование

### Запуск тестов

```bash
# Python тесты
pytest tests/

# E2E тесты с Playwright
npm test

# Проверка качества кода
flake8 blog/
black blog/
mypy blog/
```

### Покрытие тестами

```bash
pytest --cov=blog tests/
```

## 🚀 Развертывание

### Docker

```bash
# Сборка образа
docker build -t flask-helpdesk .

# Запуск контейнера
docker run -p 5000:5000 flask-helpdesk
```

### Продакшен

1. Настройте Nginx как reverse proxy
2. Используйте Gunicorn для WSGI
3. Настройте SSL сертификаты
4. Настройте мониторинг и логирование

Подробные инструкции в [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## 🤝 Участие в разработке

Мы приветствуем вклад в развитие проекта! См. [`CONTRIBUTING.md`](docs/CONTRIBUTING.md) для деталей.

### Процесс разработки

1. Форкните репозиторий
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

### Стандарты кода

- **Python**: PEP 8, Black, Flake8
- **JavaScript**: ESLint, Prettier
- **Коммиты**: Conventional Commits
- **Документация**: Markdown

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Документация**: [`docs/`](docs/)
- **Email**: support@your-company.com

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

---

**Версия**: 2.0.0
**Последнее обновление**: 2024
**Поддерживаемые версии Python**: 3.8+
