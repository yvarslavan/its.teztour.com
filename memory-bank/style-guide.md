# Руководство по стилю кода Flask Helpdesk

## Python Style Guide

### PEP 8 Compliance
- **Отступы**: 4 пробела (не табуляция)
- **Длина строки**: максимум 120 символов
- **Импорты**: группировка и сортировка
- **Пробелы**: вокруг операторов, после запятых

### Naming Conventions

#### Функции и переменные
```python
# snake_case для функций и переменных
def get_user_tasks():
    user_id = current_user.id
    return tasks

# camelCase для методов классов (если требуется совместимость)
def getUserTasks():
    pass
```

#### Классы
```python
# PascalCase для классов
class RedmineConnector:
    pass

class User(db.Model):
    pass
```

#### Константы
```python
# UPPER_CASE для констант
ANONYMOUS_USER_ID = 4
REDMINE_URL = "https://helpdesk.teztour.com"
```

### Import Organization
```python
# 1. Стандартные библиотеки Python
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 2. Сторонние библиотеки
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError

# 3. Локальные импорты проекта
from blog.models import User, Notifications
from blog.utils.cache_manager import weekend_performance_optimizer
from blog.tasks.utils import create_redmine_connector
from config import get
from redmine import RedmineConnector
```

### Function Documentation
```python
def get_user_assigned_tasks_paginated_optimized(
    redmine_connector,
    redmine_user_id,
    page=1,
    per_page=25,
    search_term='',
    sort_column='updated_on',
    sort_direction='desc',
    status_ids=None,
    priority_ids=None,
    project_ids=None,
    advanced_search_enabled=False,
    force_load=False,
    exclude_completed=False
):
    """
    Оптимизированное получение задач пользователя с пагинацией.

    Args:
        redmine_connector: Экземпляр RedmineConnector
        redmine_user_id (int): ID пользователя в Redmine
        page (int): Номер страницы (начиная с 1)
        per_page (int): Количество задач на страницу
        search_term (str): Поисковый запрос
        sort_column (str): Колонка для сортировки
        sort_direction (str): Направление сортировки ('asc' или 'desc')
        status_ids (list): Список ID статусов для фильтрации
        priority_ids (list): Список ID приоритетов для фильтрации
        project_ids (list): Список ID проектов для фильтрации
        advanced_search_enabled (bool): Включить расширенный поиск
        force_load (bool): Принудительная загрузка данных
        exclude_completed (bool): Исключить завершенные задачи

    Returns:
        dict: Словарь с задачами и метаданными пагинации

    Raises:
        Exception: При ошибках подключения к Redmine
    """
    pass
```

### Error Handling
```python
def safe_redmine_operation(func):
    """Декоратор для безопасного выполнения операций с Redmine."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResourceNotFoundError as e:
            current_app.logger.warning(f"Ресурс не найден: {e}")
            return None
        except AuthError as e:
            current_app.logger.error(f"Ошибка аутентификации: {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            return None
    return wrapper
```

### Logging Standards
```python
# Структурированное логирование с контекстом
current_app.logger.info(f"[API] GET /task/{task_id} - запрос от {current_user.username}")
current_app.logger.error(f"[REDMINE] Ошибка подключения: {e}")
current_app.logger.warning(f"[CONFIG] Не удалось получить sender_email из конфига")

# Для отладки
current_app.logger.debug(f"[DEBUG] Параметры запроса: {request.args}")
```

## JavaScript Style Guide

### Naming Conventions
```javascript
// camelCase для переменных и функций
const getUserTasks = () => {
    const userId = currentUser.id;
    return tasks;
};

// PascalCase для классов
class TaskManager {
    constructor() {
        this.tasks = [];
    }
}

// UPPER_CASE для констант
const API_ENDPOINTS = {
    TASKS: '/tasks/api',
    USERS: '/users/api'
};
```

### Function Documentation
```javascript
/**
 * Получает задачи пользователя с пагинацией
 * @param {number} page - Номер страницы
 * @param {number} perPage - Количество задач на страницу
 * @param {string} searchTerm - Поисковый запрос
 * @param {Object} filters - Объект с фильтрами
 * @returns {Promise<Object>} Объект с задачами и метаданными
 */
async function getUserTasksPaginated(page = 1, perPage = 25, searchTerm = '', filters = {}) {
    try {
        const response = await fetch(`/tasks/api/get-paginated?page=${page}&per_page=${perPage}&search=${searchTerm}`);
        return await response.json();
    } catch (error) {
        console.error('Ошибка получения задач:', error);
        throw error;
    }
}
```

### Error Handling
```javascript
// Try-catch для асинхронных операций
async function updateTaskStatus(taskId, newStatus) {
    try {
        const response = await fetch(`/tasks/api/task/${taskId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status_id: newStatus })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Ошибка обновления статуса задачи:', error);
        showErrorMessage('Не удалось обновить статус задачи');
        throw error;
    }
}
```

## HTML/CSS Style Guide

### HTML Structure
```html
<!-- Семантическая структура -->
<main class="tasks-container">
    <header class="tasks-header">
        <h1>Мои задачи</h1>
        <div class="tasks-controls">
            <!-- Элементы управления -->
        </div>
    </header>

    <section class="tasks-content">
        <!-- Основной контент -->
    </section>

    <footer class="tasks-footer">
        <!-- Пагинация и дополнительная информация -->
    </footer>
</main>
```

### CSS Naming
```css
/* BEM методология */
.tasks-container {
    /* Основной контейнер */
}

.tasks-container__header {
    /* Заголовок контейнера */
}

.tasks-container__content {
    /* Контент контейнера */
}

.tasks-controls {
    /* Элементы управления */
}

.tasks-controls__filter {
    /* Фильтр в элементах управления */
}

.tasks-controls__search {
    /* Поиск в элементах управления */
}
```

### CSS Organization
```css
/* 1. Сброс и базовые стили */
* {
    box-sizing: border-box;
}

/* 2. Переменные */
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
}

/* 3. Типографика */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

/* 4. Компоненты */
.btn {
    /* Базовые стили кнопок */
}

.btn--primary {
    /* Модификатор для основной кнопки */
}

/* 5. Утилиты */
.text-center {
    text-align: center;
}

.mt-3 {
    margin-top: 1rem;
}
```

## Database Style Guide

### Table Naming
```sql
-- snake_case для таблиц
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL
);

-- snake_case для колонок
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    issue_id INTEGER,
    old_status TEXT,
    new_status TEXT,
    date_created DATETIME
);
```

### Query Formatting
```sql
-- Читаемые SQL запросы с отступами
SELECT
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.department
FROM users u
WHERE u.is_redmine_user = 1
    AND u.is_admin = 0
ORDER BY u.username ASC;
```

## API Response Standards

### Success Response
```json
{
    "success": true,
    "message": "Задача успешно обновлена",
    "data": {
        "id": 123,
        "subject": "Обновленная задача",
        "status": "В работе"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
    "success": false,
    "error": "Задача не найдена",
    "error_code": "TASK_NOT_FOUND",
    "data": null,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination Response
```json
{
    "success": true,
    "data": {
        "tasks": [...],
        "pagination": {
            "current_page": 1,
            "per_page": 25,
            "total_pages": 5,
            "total_records": 125
        }
    }
}
```

## Configuration Standards

### Environment Variables
```bash
# .env.development
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_RUN_PORT=5000
SECRET_KEY=dev-secret-key
```

### Configuration Files
```ini
# config.ini - структурированная конфигурация
[redmine]
url = https://helpdesk.teztour.com
api_key = your-api-key
login_admin = Admin
password_admin = admin-password
anonymous_user_id = 4

[mysql]
host = helpdesk.teztour.com
database = redmine
user = easyredmine
password = your-password
```

## Testing Standards

### Test Function Naming
```python
def test_get_user_tasks_success():
    """Тест успешного получения задач пользователя."""
    pass

def test_get_user_tasks_unauthorized():
    """Тест получения задач неавторизованным пользователем."""
    pass

def test_update_task_status_invalid_id():
    """Тест обновления статуса задачи с неверным ID."""
    pass
```

### Test Structure
```python
def test_task_api_endpoint():
    """Тест API endpoint для задач."""
    # Arrange
    client = app.test_client()
    user = create_test_user()
    login_user(client, user)

    # Act
    response = client.get('/tasks/api/task/1')

    # Assert
    assert response.status_code == 200
    assert 'success' in response.json
    assert response.json['success'] is True
```

## Documentation Standards

### Code Comments
```python
# Краткие комментарии для сложной логики
def complex_algorithm(data):
    # Сортируем данные по приоритету
    sorted_data = sorted(data, key=lambda x: x.priority, reverse=True)

    # Группируем по статусу
    grouped_data = {}
    for item in sorted_data:
        status = item.status
        if status not in grouped_data:
            grouped_data[status] = []
        grouped_data[status].append(item)

    return grouped_data
```

### Function Documentation
```python
def process_user_notifications(user_id: int, notification_type: str) -> bool:
    """
    Обрабатывает уведомления пользователя.

    Args:
        user_id: ID пользователя
        notification_type: Тип уведомления ('email', 'push', 'browser')

    Returns:
        bool: True если обработка прошла успешно

    Raises:
        ValueError: Если неверный тип уведомления
        UserNotFoundError: Если пользователь не найден
    """
    pass
```

## Performance Standards

### Database Queries
```python
# Используем индексы и оптимизированные запросы
def get_optimized_user_tasks(user_id):
    """Оптимизированное получение задач пользователя."""
    query = """
    SELECT i.id, i.subject, i.status_id, s.name as status_name
    FROM issues i
    JOIN issue_statuses s ON i.status_id = s.id
    WHERE i.assigned_to_id = %s
    ORDER BY i.updated_on DESC
    LIMIT 25
    """
    return execute_query(query, (user_id,))
```

### Caching Strategy
```python
# Кэширование часто используемых данных
@cache.memoize(timeout=300)  # 5 минут
def get_status_names():
    """Получает названия статусов с кэшированием."""
    return get_all_status_names_from_db()
```
