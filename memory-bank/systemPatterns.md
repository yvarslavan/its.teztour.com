# Системные паттерны и конвенции Flask Helpdesk

## Архитектурные паттерны

### Application Factory Pattern
```python
# blog/__init__.py
def create_app():
    app = Flask(__name__)
    # Конфигурация и инициализация
    return app
```

### Blueprint Pattern
```python
# Модульная структура с blueprints
from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__)
api_bp = Blueprint('tasks_api', __name__, url_prefix='/tasks/api')
```

### Repository Pattern
```python
# blog/tasks/utils.py - утилиты для работы с данными
def create_redmine_connector(is_redmine_user, user_login, password=None):
    # Логика создания коннектора
    pass

def get_user_assigned_tasks_paginated_optimized(redmine_connector, ...):
    # Оптимизированное получение задач
    pass
```

## Паттерны работы с данными

### Status Management Pattern
```python
# Динамическое получение статусов из БД вместо хардкода
def get_status_name_from_id(connection, status_id):
    # Получение из u_statuses таблицы
    pass
```

### Connection Management Pattern
```python
# Повторные попытки подключения с логированием
def get_connection(host, user_name, password, name, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            connection = pymysql.connect(...)
            return connection
        except pymysql.Error as e:
            attempts += 1
            time.sleep(3)
```

### Performance Optimization Pattern
```python
# Декораторы для оптимизации производительности
@weekend_performance_optimizer
def my_tasks_page():
    # Оптимизированная логика для выходных
    pass
```

## Паттерны безопасности

### CSRF Protection Pattern
```python
# Исключения для API endpoints
@api_bp.route("/task/<int:task_id>", methods=["GET"])
@csrf.exempt
@login_required
def get_task_by_id(task_id):
    pass
```

### Authentication Pattern
```python
# Проверка прав доступа
@login_required
def protected_route():
    if not current_user.is_redmine_user:
        return jsonify({"error": "Доступ запрещен"}), 403
```

### Input Validation Pattern
```python
# Валидация входных данных
def validate_task_id(task_id):
    try:
        return int(task_id) > 0
    except (ValueError, TypeError):
        return False
```

## Паттерны логирования

### Structured Logging Pattern
```python
# Структурированное логирование с контекстом
current_app.logger.info(f"[API] GET /task/{task_id} - запрос от {current_user.username}")
```

### Performance Monitoring Pattern
```python
# Декоратор для мониторинга производительности
@monitor_performance("get_multiple_user_names")
def get_multiple_user_names(connection, user_ids):
    start_time = time.time()
    # Логика функции
    execution_time = time.time() - start_time
    logger.info(f"get_multiple_user_names выполнен за {execution_time:.2f}с")
```

## Паттерны обработки ошибок

### Graceful Degradation Pattern
```python
# Корректная обработка сбоев интеграций
try:
    task = redmine_connector.redmine.issue.get(task_id)
except ResourceNotFoundError:
    return jsonify({"error": "Задача не найдена"}), 404
except Exception as e:
    current_app.logger.error(f"Ошибка получения задачи: {e}")
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500
```

### Error Response Pattern
```python
# Стандартизированные ответы об ошибках
def error_response(message, status_code=400, success=False):
    return jsonify({
        "error": message,
        "success": success,
        "data": None
    }), status_code
```

## Паттерны API

### RESTful API Pattern
```python
# Стандартные HTTP методы
@api_bp.route("/task/<int:task_id>", methods=["GET"])    # Получение
@api_bp.route("/task/<int:task_id>", methods=["PUT"])    # Обновление
@api_bp.route("/task/<int:task_id>", methods=["DELETE"]) # Удаление
```

### Pagination Pattern
```python
# Постраничная загрузка данных
def get_user_assigned_tasks_paginated_optimized(
    redmine_connector, redmine_user_id,
    page=1, per_page=25,  # Параметры пагинации
    search_term='', sort_column='updated_on', sort_direction='desc'
):
    # Логика пагинации
    pass
```

### Response Standardization Pattern
```python
# Стандартизированные ответы API
def success_response(data, message="Успешно"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    })
```

## Паттерны конфигурации

### Environment-based Configuration Pattern
```python
# Разные настройки для разных окружений
if app.debug:
    # Настройки разработки
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        TEMPLATES_AUTO_RELOAD=True
    )
else:
    # Настройки продакшена
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_DOMAIN='.tez-tour.com'
    )
```

### Configuration Loading Pattern
```python
# Загрузка конфигурации из файлов
def setup_development_environment():
    load_dotenv('.flaskenv')
    load_dotenv('.env.development')
```

## Паттерны фронтенда

### Component Pattern
```javascript
// Модульная структура JavaScript
// blog/static/js/pages/tasks/components/
```

### Service Pattern
```javascript
// API сервисы для взаимодействия с бэкендом
// blog/static/js/pages/tasks/services/
```

### Utility Pattern
```javascript
// Переиспользуемые утилиты
// blog/static/js/pages/tasks/utils/
```

## Паттерны тестирования

### Debug Endpoint Pattern
```python
# Встроенные тестовые маршруты для отладки
@tasks_bp.route("/test-statistics-debug")
def test_statistics_debug():
    # Тестовая логика
    pass
```

### Performance Test Pattern
```python
# Тесты производительности
@tasks_bp.route("/test-direct-sql", methods=["GET"])
def test_direct_sql():
    # Тестирование прямых SQL запросов
    pass
```

## Конвенции именования

### File Naming Conventions
- **Python files**: snake_case (`redmine.py`, `api_routes.py`)
- **JavaScript files**: camelCase (`callTransfer.js`)
- **CSS files**: kebab-case (`kanban-onboarding.css`)

### Function Naming Conventions
- **API functions**: `get_task_by_id()`, `update_task_status()`
- **Utility functions**: `create_redmine_connector()`, `format_issue_date()`
- **Database functions**: `get_connection()`, `execute_query()`

### Variable Naming Conventions
- **Database connections**: `connection`, `mysql_conn`
- **Redmine objects**: `redmine_connector`, `redmine_instance`
- **User objects**: `current_user`, `user_obj`

## Конвенции кодирования

### Import Organization
```python
# 1. Стандартные библиотеки
import os
import time
from datetime import datetime

# 2. Сторонние библиотеки
from flask import Blueprint, request, jsonify
from redminelib import Redmine

# 3. Локальные импорты
from blog.models import User
from blog.utils.cache_manager import weekend_performance_optimizer
```

### Error Handling Conventions
```python
# Всегда используем конкретные исключения
try:
    # Код
except ResourceNotFoundError:
    # Обработка конкретной ошибки
except Exception as e:
    # Логирование и fallback
    current_app.logger.error(f"Неожиданная ошибка: {e}")
```

### Logging Conventions
```python
# Структурированные сообщения с префиксами
current_app.logger.info(f"[API] GET /task/{task_id}")
current_app.logger.error(f"[REDMINE] Ошибка подключения: {e}")
current_app.logger.warning(f"[CONFIG] Не удалось получить sender_email")
```
