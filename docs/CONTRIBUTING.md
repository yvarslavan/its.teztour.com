# 🤝 Руководство для разработчиков

Добро пожаловать в проект Flask Helpdesk System! Это руководство поможет вам начать работу с проектом и внести свой вклад в его развитие.

## 📋 Содержание

- [🚀 Начало работы](#-начало-работы)
- [🔧 Настройка окружения](#-настройка-окружения)
- [📝 Стандарты кода](#-стандарты-кода)
- [🧪 Тестирование](#-тестирование)
- [📚 Документация](#-документация)
- [🔄 Процесс разработки](#-процесс-разработки)
- [🐛 Отчеты об ошибках](#-отчеты-об-ошибках)
- [💡 Предложения по улучшению](#-предложения-по-улучшению)
- [📞 Поддержка](#-поддержка)

## 🚀 Начало работы

### Предварительные требования

- **Python 3.8+** - основная версия языка
- **Node.js 14+** - для тестов и сборки фронтенда
- **Git** - система контроля версий
- **MySQL 5.7+** - для интеграции с Redmine
- **Oracle Client** - для интеграции с ERP (опционально)

### Клонирование репозитория

```bash
# Клонирование основного репозитория
git clone https://github.com/your-username/flask-helpdesk.git
cd flask-helpdesk

# Добавление upstream репозитория
git remote add upstream https://github.com/original-owner/flask-helpdesk.git
```

### Создание виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация в Linux/Mac
source venv/bin/activate

# Активация в Windows
venv\Scripts\activate

# Обновление pip
pip install --upgrade pip
```

## 🔧 Настройка окружения

### Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Установка зависимостей для разработки
pip install -r requirements-dev.txt

# Установка Node.js зависимостей
npm install
```

### Настройка конфигурации

1. **Создайте файл `.env`** на основе `.env.example`:

```bash
cp .env.example .env
```

2. **Настройте переменные окружения**:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# База данных
DATABASE_URL=sqlite:///blog.db
MYSQL_HOST=localhost
MYSQL_USER=redmine_user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=redmine

# Redmine
REDMINE_URL=https://your-redmine.com
REDMINE_API_KEY=your-redmine-api-key

# Oracle ERP (опционально)
ORACLE_HOST=your-oracle-host
ORACLE_PORT=1521
ORACLE_SERVICE=your-service
ORACLE_USER=your-user
ORACLE_PASSWORD=your-password

# Уведомления
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
```

3. **Настройте `config.ini`**:

```ini
[database]
db_path = blog/db/blog.db

[mysql]
host = localhost
database = redmine_db
user = redmine_user
password = your-mysql-password

[oracle]
host = your-oracle-host
service_name = your-service
user = your-user
password = your-password

[redmine]
url = https://your-redmine.com
api_key = your-redmine-api-key
anonymous_user_id = 4
```

### Инициализация базы данных

```bash
# Создание таблиц
flask db upgrade

# Создание первого пользователя (опционально)
python scripts/create_admin_user.py
```

### Запуск приложения

```bash
# Режим разработки
python app.py

# Или через Flask CLI
flask run --host=0.0.0.0 --port=5000
```

Приложение будет доступно по адресу: http://localhost:5000

## 📝 Стандарты кода

### Python

#### Стиль кода (PEP 8)

Мы используем **Black** для автоматического форматирования кода:

```bash
# Форматирование кода
black blog/
black tests/

# Проверка стиля
flake8 blog/
flake8 tests/
```

#### Структура импортов

```python
# Стандартная библиотека
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Сторонние библиотеки
from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String
import requests

# Локальные импорты
from blog.models import User, Task
from blog.utils.helpers import format_datetime
```

#### Документация функций

```python
def update_task_status(task_id: int, status_id: int, comment: str = "") -> Dict[str, any]:
    """
    Обновляет статус задачи в Redmine.

    Args:
        task_id (int): ID задачи для обновления
        status_id (int): ID нового статуса
        comment (str, optional): Комментарий к изменению. По умолчанию "".

    Returns:
        Dict[str, any]: Результат операции с ключами:
            - success (bool): Успешность операции
            - message (str): Сообщение о результате
            - task (Dict): Обновленные данные задачи

    Raises:
        ValueError: Если task_id или status_id некорректны
        ConnectionError: При ошибке подключения к Redmine

    Example:
        >>> result = update_task_status(12345, 3, "Задача выполнена")
        >>> print(result['success'])
        True
    """
    if not isinstance(task_id, int) or task_id <= 0:
        raise ValueError("task_id должен быть положительным целым числом")

    # Реализация функции...
    pass
```

#### Обработка ошибок

```python
from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

def handle_api_error(error):
    """Обработчик ошибок для API endpoints."""
    if isinstance(error, HTTPException):
        response = {
            'success': False,
            'error': error.description,
            'code': error.code
        }
        return jsonify(response), error.code

    # Логирование неожиданных ошибок
    logger.error(f"Неожиданная ошибка: {error}", exc_info=True)

    return jsonify({
        'success': False,
        'error': 'Внутренняя ошибка сервера',
        'code': 500
    }), 500
```

### JavaScript

#### Стиль кода

Используем **ESLint** и **Prettier**:

```bash
# Проверка стиля
npm run lint

# Автоматическое исправление
npm run lint:fix

# Форматирование
npm run format
```

#### Структура функций

```javascript
/**
 * Обновляет статус задачи через API
 * @param {number} taskId - ID задачи
 * @param {number} statusId - ID нового статуса
 * @param {string} comment - Комментарий к изменению
 * @returns {Promise<Object>} Результат операции
 * @throws {Error} При ошибке сети или сервера
 */
async function updateTaskStatus(taskId, statusId, comment = '') {
    try {
        const response = await fetch(`/tasks/api/task/${taskId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                status_id: statusId,
                comment: comment
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.message || 'Неизвестная ошибка');
        }

        return result;
    } catch (error) {
        console.error('Ошибка обновления статуса задачи:', error);
        throw error;
    }
}

// Пример использования
updateTaskStatus(12345, 3, 'Задача выполнена')
    .then(result => {
        console.log('Статус обновлен:', result.message);
    })
    .catch(error => {
        console.error('Ошибка:', error.message);
    });
```

### HTML/CSS

#### Структура HTML

```html
<!-- Используем семантические теги -->
<main class="container">
    <header class="page-header">
        <h1>Управление задачами</h1>
        <nav class="breadcrumb">
            <a href="/">Главная</a> /
            <a href="/tasks">Задачи</a> /
            <span>Детали задачи</span>
        </nav>
    </header>

    <section class="task-details">
        <article class="task-card">
            <header class="task-header">
                <h2>Задача #12345</h2>
                <div class="task-meta">
                    <span class="status status-in-progress">В работе</span>
                    <span class="priority priority-high">Высокий</span>
                </div>
            </header>

            <div class="task-content">
                <p>Описание задачи...</p>
            </div>
        </article>
    </section>
</main>
```

#### CSS классы

```css
/* Используем BEM методологию */
.task-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.task-card__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.task-card__title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #333;
}

.task-card__meta {
    display: flex;
    gap: 0.5rem;
}

.status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status--in-progress {
    background-color: #fff3cd;
    color: #856404;
}

.priority--high {
    background-color: #f8d7da;
    color: #721c24;
}
```

## 🧪 Тестирование

### Python тесты

#### Структура тестов

```python
# tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from blog.models import Task, User
from blog.tasks.api_routes import update_task_status

class TestTaskAPI:
    """Тесты для API управления задачами."""

    @pytest.fixture
    def sample_task(self):
        """Фикстура для тестовой задачи."""
        return Task(
            id=12345,
            subject="Тестовая задача",
            status_id=1,
            priority_id=2
        )

    @pytest.fixture
    def sample_user(self):
        """Фикстура для тестового пользователя."""
        return User(
            id=1,
            username="testuser",
            email="test@example.com"
        )

    def test_update_task_status_success(self, sample_task, sample_user):
        """Тест успешного обновления статуса задачи."""
        with patch('blog.tasks.api_routes.update_redmine_task_status') as mock_update:
            mock_update.return_value = True

            result = update_task_status(
                task_id=sample_task.id,
                status_id=3,
                comment="Тестовый комментарий"
            )

            assert result['success'] is True
            assert 'успешно обновлен' in result['message']
            mock_update.assert_called_once_with(
                sample_task.id, 3, "Тестовый комментарий"
            )

    def test_update_task_status_failure(self, sample_task):
        """Тест неудачного обновления статуса задачи."""
        with patch('blog.tasks.api_routes.update_redmine_task_status') as mock_update:
            mock_update.return_value = False

            result = update_task_status(
                task_id=sample_task.id,
                status_id=999,  # Несуществующий статус
                comment=""
            )

            assert result['success'] is False
            assert 'ошибка' in result['message'].lower()

    @pytest.mark.parametrize("task_id,status_id,expected_error", [
        (0, 1, "task_id должен быть положительным"),
        (-1, 1, "task_id должен быть положительным"),
        (12345, 0, "status_id должен быть положительным"),
    ])
    def test_update_task_status_invalid_input(self, task_id, status_id, expected_error):
        """Тест валидации входных данных."""
        with pytest.raises(ValueError, match=expected_error):
            update_task_status(task_id, status_id)
```

#### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=blog --cov-report=html

# Конкретный тест
pytest tests/test_tasks.py::TestTaskAPI::test_update_task_status_success

# Тесты с подробным выводом
pytest -v

# Тесты с остановкой при первой ошибке
pytest -x
```

### E2E тесты (Playwright)

#### Структура тестов

```javascript
// tests/e2e/task-management.spec.js
const { test, expect } = require('@playwright/test');

test.describe('Управление задачами', () => {
    test.beforeEach(async ({ page }) => {
        // Авторизация перед каждым тестом
        await page.goto('/users/login');
        await page.fill('#username', 'testuser');
        await page.fill('#password', 'testpass');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('/tasks/my-tasks');
    });

    test('должен изменять статус задачи', async ({ page }) => {
        // Переход к деталям задачи
        await page.goto('/tasks/12345');

        // Проверка текущего статуса
        await expect(page.locator('.task-status')).toHaveText('Новый');

        // Изменение статуса
        await page.selectOption('#status-select', '3'); // "В работе"
        await page.fill('#status-comment', 'Начинаю работу над задачей');
        await page.click('#update-status-btn');

        // Проверка обновления
        await expect(page.locator('.task-status')).toHaveText('В работе');
        await expect(page.locator('.alert-success')).toContainText('Статус обновлен');
    });

    test('должен назначать исполнителя', async ({ page }) => {
        await page.goto('/tasks/12345');

        // Открытие модального окна назначения
        await page.click('#assign-task-btn');

        // Выбор исполнителя
        await page.selectOption('#assignee-select', '456');
        await page.fill('#assign-comment', 'Назначен новый исполнитель');
        await page.click('#confirm-assign-btn');

        // Проверка назначения
        await expect(page.locator('.task-assignee')).toContainText('Петр Сидоров');
    });
});
```

#### Запуск E2E тестов

```bash
# Все E2E тесты
npm test

# Конкретный тест
npm test -- tests/e2e/task-management.spec.js

# Тесты в определенном браузере
npm test -- --project=chromium

# Тесты с видео
npm test -- --video=on
```

## 📚 Документация

### Обновление документации

При внесении изменений в код обязательно обновляйте документацию:

1. **API изменения** - обновите `docs/API_DOCUMENTATION.md`
2. **Новые функции** - добавьте примеры в `docs/QUICK_REFERENCE.md`
3. **Изменения в процессе** - обновите `docs/CONTRIBUTING.md`
4. **Новые возможности** - обновите `docs/README.md`

### Стандарты документации

```markdown
# Название раздела

## Описание
Краткое описание функциональности.

## Использование
Примеры использования с кодом.

### Параметры
- `param1` (type): описание параметра
- `param2` (type): описание параметра

### Возвращаемое значение
Описание возвращаемого значения.

### Примеры
```python
# Пример кода
function_call(param1, param2)
```

## Примечания
Дополнительная информация и предупреждения.
```

## 🔄 Процесс разработки

### Создание feature branch

```bash
# Обновление основной ветки
git checkout main
git pull upstream main

# Создание новой ветки
git checkout -b feature/your-feature-name

# Или для исправления ошибок
git checkout -b fix/issue-description
```

### Коммиты

Используем **Conventional Commits**:

```bash
# Новые функции
git commit -m "feat: добавить систему push-уведомлений"

# Исправления ошибок
git commit -m "fix: исправить дублирование уведомлений в Kanban"

# Документация
git commit -m "docs: обновить API документацию"

# Рефакторинг
git commit -m "refactor: оптимизировать запросы к базе данных"

# Тесты
git commit -m "test: добавить тесты для API уведомлений"

# Стиль кода
git commit -m "style: форматировать код согласно PEP 8"
```

### Pull Request

1. **Создайте PR** в GitHub/GitLab
2. **Опишите изменения** в описании PR
3. **Добавьте тесты** для новой функциональности
4. **Обновите документацию** при необходимости
5. **Проверьте CI/CD** pipeline

#### Шаблон описания PR

```markdown
## Описание
Краткое описание изменений.

## Тип изменений
- [ ] Исправление ошибки
- [ ] Новая функция
- [ ] Рефакторинг
- [ ] Документация
- [ ] Тесты

## Тестирование
- [ ] Локальные тесты пройдены
- [ ] E2E тесты пройдены
- [ ] Документация обновлена

## Чек-лист
- [ ] Код соответствует стандартам
- [ ] Добавлены тесты для новой функциональности
- [ ] Обновлена документация
- [ ] Проверена обратная совместимость

## Скриншоты (если применимо)
Добавьте скриншоты для изменений UI.

## Дополнительная информация
Любая дополнительная информация.
```

### Code Review

#### Для ревьюера

1. **Проверьте код** на соответствие стандартам
2. **Запустите тесты** локально
3. **Проверьте документацию** на актуальность
4. **Оставьте конструктивные комментарии**

#### Для автора

1. **Исправьте замечания** ревьюера
2. **Отвечайте на комментарии** вежливо
3. **Обновляйте PR** при внесении изменений
4. **Попросите повторного ревью** после исправлений

## 🐛 Отчеты об ошибках

### Создание issue

Используйте шаблон для создания issue:

```markdown
## Описание ошибки
Четкое и краткое описание проблемы.

## Шаги для воспроизведения
1. Перейти к '...'
2. Нажать на '...'
3. Прокрутить до '...'
4. Увидеть ошибку

## Ожидаемое поведение
Что должно происходить в норме.

## Фактическое поведение
Что происходит на самом деле.

## Скриншоты
Если применимо, добавьте скриншоты.

## Окружение
- ОС: [например, Windows 10]
- Браузер: [например, Chrome 91]
- Версия приложения: [например, 2.0.0]

## Дополнительная информация
Любая дополнительная информация о проблеме.
```

### Отладка

#### Логирование

```python
import logging

logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("Начало выполнения функции")
    try:
        # Код функции
        result = some_operation()
        logger.info(f"Операция выполнена успешно: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}", exc_info=True)
        raise
```

#### Отладочные инструменты

```python
# Flask debug toolbar
from flask_debugtoolbar import DebugToolbarExtension

# В режиме разработки
if app.debug:
    toolbar = DebugToolbarExtension(app)
```

## 💡 Предложения по улучшению

### Feature Request

```markdown
## Описание
Краткое описание предлагаемой функции.

## Проблема
Какую проблему решает эта функция?

## Предлагаемое решение
Описание решения.

## Альтернативы
Рассмотренные альтернативы.

## Дополнительная информация
Любая дополнительная информация.
```

## 📞 Поддержка

### Получение помощи

1. **Документация** - начните с `docs/`
2. **Issues** - поищите похожие проблемы
3. **Discussions** - задайте вопрос в обсуждениях
4. **Email** - для срочных вопросов

### Полезные команды

```bash
# Проверка статуса
git status

# Просмотр логов
tail -f logs/app.log

# Проверка зависимостей
pip list --outdated

# Очистка кэша
python -Bc "import compileall; compileall.compile_dir('.', force=True)"

# Проверка безопасности
safety check
```

---

**Спасибо за ваш вклад в развитие проекта!** 🚀
