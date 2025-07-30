# Технический контекст Flask Helpdesk

## Архитектура системы

### Backend Architecture
- **Flask Application Factory Pattern**: Приложение создается через `create_app()` в `blog/__init__.py`
- **Blueprint Structure**: Модульная архитектура с разделением на blueprints
- **SQLAlchemy ORM**: Работа с базами данных через ORM
- **Flask-Login**: Аутентификация и управление сессиями
- **Flask-WTF**: CSRF защита и валидация форм

### Базы данных
1. **SQLite** (`blog/db/blog.db`): Локальная база для пользователей и уведомлений
2. **MySQL** (Redmine): Основная база данных Redmine
3. **Oracle** (ERP): Корпоративная ERP система

### Интеграции

#### Redmine Integration
- **API Key Authentication**: Использует API ключ администратора
- **REST API**: Взаимодействие через python-redmine библиотеку
- **MySQL Direct Access**: Прямой доступ к MySQL для оптимизации
- **Status Management**: Динамическое получение статусов из `u_statuses` таблицы

#### Oracle ERP Integration
- **Thin Mode**: Использует python-oracledb в Thin Mode (без Oracle Client)
- **Connection Pooling**: Оптимизированные подключения
- **User Authentication**: Интеграция с ERP пользователями

### Frontend Architecture

#### JavaScript Structure
```
blog/static/js/
├── pages/tasks/          # Модули для задач
│   ├── components/       # React-подобные компоненты
│   ├── core/            # Основная логика
│   ├── services/        # API сервисы
│   └── utils/           # Утилиты
├── datatables/          # DataTables конфигурация
└── critical_ui_fixes.js # Критические UI исправления
```

#### CSS Architecture
```
blog/static/css/
├── pages/tasks/         # Стили для страниц задач
├── scss/               # SCSS исходники
└── components/         # Компонентные стили
```

### Система уведомлений

#### Push Notifications
- **Service Worker**: `blog/sw.js` - для браузерных уведомлений
- **VAPID Keys**: Конфигурация в `blog/config/vapid_keys.py`
- **Firebase Integration**: `blog/firebase_push_service.py`

#### Email Notifications
- **SMTP Configuration**: Настройки в `config.ini`
- **HTML Templates**: Шаблоны в `blog/templates/`

### Оптимизация производительности

#### Caching Strategy
- **Weekend Performance Optimizer**: Декоратор для оптимизации в выходные
- **Tasks Cache Optimizer**: Кэширование задач
- **Connection Pooling**: Пул подключений к БД

#### Database Optimization
- **Indexed Queries**: Оптимизированные запросы с индексами
- **Pagination**: Постраничная загрузка данных
- **Lazy Loading**: Ленивая загрузка связанных данных

### Безопасность

#### Authentication & Authorization
- **Flask-Login**: Управление сессиями пользователей
- **CSRF Protection**: Защита от CSRF атак
- **Session Security**: Безопасные настройки сессий

#### Data Protection
- **Input Validation**: Валидация входных данных
- **SQL Injection Prevention**: Использование параметризованных запросов
- **File Upload Security**: Безопасная загрузка файлов

### Мониторинг и логирование

#### Logging Configuration
- **Structured Logging**: python-json-logger для структурированных логов
- **Concurrent Log Handler**: Асинхронная запись логов
- **Performance Monitoring**: Декораторы для мониторинга производительности

#### Error Handling
- **Global Exception Handler**: Централизованная обработка ошибок
- **Graceful Degradation**: Корректная обработка сбоев интеграций
- **User-Friendly Messages**: Понятные сообщения об ошибках

### Деплой и инфраструктура

#### Production Setup
- **systemd Service**: `flask-helpdesk.service`
- **nginx Configuration**: `flask-helpdesk.nginx.conf`
- **Gunicorn**: WSGI сервер для продакшена

#### Development Setup
- **Flask Development Server**: `python app.py`
- **Hot Reload**: Автоматическая перезагрузка при изменениях
- **Debug Mode**: Подробная отладочная информация

### Конфигурация

#### Environment Variables
- **Development**: `.flaskenv` и `.env.development`
- **Production**: Системные переменные окружения
- **Secret Management**: Безопасное хранение секретов

#### Configuration Files
- **config.ini**: Основная конфигурация
- **config.py**: Python конфигурация
- **.pylintrc**: Настройки линтера

### Тестирование

#### Test Structure
- **Unit Tests**: Тесты отдельных компонентов
- **Integration Tests**: Тесты интеграций
- **API Tests**: Тесты API endpoints

#### Debug Endpoints
- **Test Routes**: Встроенные тестовые маршруты
- **Debug APIs**: API для отладки
- **Performance Monitoring**: Мониторинг производительности
