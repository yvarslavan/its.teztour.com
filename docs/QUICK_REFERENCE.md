# ⚡ Быстрый справочник Flask Helpdesk System

Краткое руководство по основным функциям, API и примерам использования системы.

## 📋 Содержание

- [🚀 Быстрый старт](#-быстрый-старт)
- [🔑 Основные API](#-основные-api)
- [💻 Примеры кода](#-примеры-кода)
- [🗄️ Модели данных](#️-модели-данных)
- [⚙️ Конфигурация](#️-конфигурация)
- [🧪 Тестирование](#-тестирование)
- [🔄 Рабочие процессы](#-рабочие-процессы)
- [🐛 Обработка ошибок](#-обработка-ошибок)
- [⚡ Производительность](#-производительность)
- [🔒 Безопасность](#-безопасность)

## 🚀 Быстрый старт

### Запуск приложения

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env файл

# Инициализация БД
flask db upgrade

# Запуск
python app.py
```

### Основные URL

- **Главная**: http://localhost:5000
- **Задачи**: http://localhost:5000/tasks/my-tasks
- **Вход**: http://localhost:5000/users/login
- **Профиль**: http://localhost:5000/users/profile
- **API**: http://localhost:5000/tasks/api/

## 🔑 Основные API

### Аутентификация

```python
# Вход в систему
POST /users/login
{
    "username": "user123",
    "password": "password123"
}

# Выход
GET /users/logout
```

### Управление задачами

```python
# Получить задачу
GET /tasks/api/task/{task_id}

# Изменить статус
PUT /tasks/api/task/{task_id}/status
{
    "status_id": 3,
    "comment": "Задача выполнена"
}

# Изменить приоритет
PUT /tasks/api/task/{task_id}/priority
{
    "priority_id": 2,
    "comment": "Повышен приоритет"
}

# Назначить исполнителя
PUT /tasks/api/task/{task_id}/assignee
{
    "assignee_id": 456,
    "comment": "Назначен новый исполнитель"
}

# Скачать вложение
GET /tasks/api/task/{task_id}/attachment/{attachment_id}/download
```

### Уведомления

```python
# Получить уведомления
GET /tasks/api/notifications?page=1&per_page=20

# Отметить как прочитанное
PUT /tasks/api/notifications/{notification_id}/read

# Подписка на push
POST /tasks/api/push-subscribe
{
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
        "p256dh": "BNcRd...",
        "auth": "tBHI..."
    }
}
```

## 💻 Примеры кода

### Python (Backend)

#### Обновление статуса задачи

```python
from blog.tasks.api_routes import update_task_status
from blog.models import User, Task

def change_task_status(task_id: int, new_status: int, user_id: int, comment: str = ""):
    """Обновление статуса задачи с уведомлениями."""
    try:
        # Получение пользователя
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        # Обновление статуса
        result = update_task_status(
            task_id=task_id,
            status_id=new_status,
            comment=comment
        )

        if result['success']:
            # Отправка уведомления
            send_task_notification(
                task_id=task_id,
                user_id=user_id,
                notification_type='status_change',
                data={
                    'old_status': get_task_status(task_id),
                    'new_status': get_status_name(new_status),
                    'updated_by': user.full_name
                }
            )

            return {
                'success': True,
                'message': 'Статус обновлен успешно',
                'task_id': task_id
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Ошибка обновления')
            }

    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {e}")
        return {
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }
```

#### Работа с уведомлениями

```python
from blog.notification_service import NotificationService
from blog.models import Notifications

def get_user_notifications(user_id: int, page: int = 1, per_page: int = 20):
    """Получение уведомлений пользователя с пагинацией."""
    try:
        # Запрос уведомлений
        notifications = Notifications.query.filter_by(
            user_id=user_id
        ).order_by(
            Notifications.date_created.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # Форматирование результата
        result = {
            'notifications': [],
            'pagination': {
                'page': notifications.page,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'pages': notifications.pages
            }
        }

        for notification in notifications.items:
            result['notifications'].append({
                'id': notification.id,
                'issue_id': notification.issue_id,
                'old_status': notification.old_status,
                'new_status': notification.new_status,
                'old_subj': notification.old_subj,
                'date_created': notification.date_created.isoformat(),
                'is_read': notification.is_read
            })

        return result

    except Exception as e:
        logger.error(f"Ошибка получения уведомлений: {e}")
        return {
            'notifications': [],
            'pagination': {'page': 1, 'per_page': 20, 'total': 0, 'pages': 0}
        }
```

#### Интеграция с Redmine

```python
from redmine import Redmine
from blog.utils.cache_manager import cached_response

@cached_response(timeout=300)  # Кэш на 5 минут
def get_redmine_projects():
    """Получение списка проектов из Redmine."""
    try:
        redmine = Redmine(
            url=current_app.config['REDMINE_URL'],
            key=current_app.config['REDMINE_API_KEY']
        )

        projects = redmine.project.all()
        return [
            {
                'id': project.id,
                'name': project.name,
                'identifier': project.identifier,
                'description': getattr(project, 'description', '')
            }
            for project in projects
        ]

    except Exception as e:
        logger.error(f"Ошибка получения проектов Redmine: {e}")
        return []

def update_redmine_task(task_id: int, **kwargs):
    """Обновление задачи в Redmine."""
    try:
        redmine = Redmine(
            url=current_app.config['REDMINE_URL'],
            key=current_app.config['REDMINE_API_KEY']
        )

        task = redmine.issue.get(task_id)

        # Обновление полей
        for field, value in kwargs.items():
            if hasattr(task, field):
                setattr(task, field, value)

        task.save()
        return True

    except Exception as e:
        logger.error(f"Ошибка обновления задачи {task_id}: {e}")
        return False
```

### JavaScript (Frontend)

#### Управление задачами

```javascript
// Класс для работы с задачами
class TaskManager {
    constructor() {
        this.baseUrl = '/tasks/api';
        this.csrfToken = this.getCsrfToken();
    }

    getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }

    async getTask(taskId) {
        try {
            const response = await fetch(`${this.baseUrl}/task/${taskId}`, {
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Ошибка получения задачи:', error);
            throw error;
        }
    }

    async updateTaskStatus(taskId, statusId, comment = '') {
        try {
            const response = await fetch(`${this.baseUrl}/task/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
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

            if (result.success) {
                // Обновление UI
                this.updateTaskUI(taskId, result.task);
                this.showNotification('Статус обновлен успешно', 'success');
            } else {
                this.showNotification(result.message, 'error');
            }

            return result;
        } catch (error) {
            console.error('Ошибка обновления статуса:', error);
            this.showNotification('Ошибка обновления статуса', 'error');
            throw error;
        }
    }

    async assignTask(taskId, assigneeId, comment = '') {
        try {
            const response = await fetch(`${this.baseUrl}/task/${taskId}/assignee`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    assignee_id: assigneeId,
                    comment: comment
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Ошибка назначения задачи:', error);
            throw error;
        }
    }

    updateTaskUI(taskId, taskData) {
        // Обновление элементов UI
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            // Обновление статуса
            const statusElement = taskElement.querySelector('.task-status');
            if (statusElement && taskData.status) {
                statusElement.textContent = taskData.status.name;
                statusElement.className = `task-status status-${taskData.status.id}`;
            }

            // Обновление исполнителя
            const assigneeElement = taskElement.querySelector('.task-assignee');
            if (assigneeElement && taskData.assignee) {
                assigneeElement.textContent = taskData.assignee.name;
            }
        }
    }

    showNotification(message, type = 'info') {
        // Показ уведомления пользователю
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.notifications-container');
        if (container) {
            container.appendChild(notification);

            // Автоматическое скрытие через 5 секунд
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
    }
}

// Использование
const taskManager = new TaskManager();

// Получение задачи
taskManager.getTask(12345)
    .then(task => {
        console.log('Задача:', task);
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });

// Обновление статуса
taskManager.updateTaskStatus(12345, 3, 'Задача выполнена')
    .then(result => {
        console.log('Результат:', result);
    });
```

#### WebSocket уведомления

```javascript
// Класс для работы с WebSocket уведомлениями
class NotificationManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect(userId) {
        try {
            this.socket = io('/notifications');

            this.socket.on('connect', () => {
                console.log('Подключен к серверу уведомлений');
                this.isConnected = true;
                this.reconnectAttempts = 0;

                // Подключение к каналу пользователя
                this.socket.emit('join_notifications', { user_id: userId });
            });

            this.socket.on('disconnect', () => {
                console.log('Отключен от сервера уведомлений');
                this.isConnected = false;
                this.attemptReconnect(userId);
            });

            this.socket.on('new_notification', (data) => {
                this.handleNewNotification(data);
            });

            this.socket.on('task_status_changed', (data) => {
                this.handleTaskStatusChange(data);
            });

            this.socket.on('connect_error', (error) => {
                console.error('Ошибка подключения к WebSocket:', error);
                this.attemptReconnect(userId);
            });

        } catch (error) {
            console.error('Ошибка инициализации WebSocket:', error);
        }
    }

    attemptReconnect(userId) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);

            setTimeout(() => {
                this.connect(userId);
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Превышено максимальное количество попыток переподключения');
        }
    }

    handleNewNotification(data) {
        console.log('Новое уведомление:', data);

        // Обновление счетчика уведомлений
        this.updateNotificationCount();

        // Показ уведомления
        this.showNotification(data.title, data.message, data.type);

        // Обновление списка уведомлений
        this.refreshNotificationsList();
    }

    handleTaskStatusChange(data) {
        console.log('Изменение статуса задачи:', data);

        // Обновление UI задачи
        const taskManager = new TaskManager();
        taskManager.updateTaskUI(data.task_id, {
            status: { name: data.new_status }
        });

        // Показ уведомления
        this.showNotification(
            'Изменение статуса задачи',
            `Задача #${data.task_id} переведена в статус "${data.new_status}"`,
            'info'
        );
    }

    updateNotificationCount() {
        const counter = document.querySelector('.notification-counter');
        if (counter) {
            const currentCount = parseInt(counter.textContent) || 0;
            counter.textContent = currentCount + 1;
            counter.style.display = currentCount + 1 > 0 ? 'block' : 'none';
        }
    }

    showNotification(title, message, type = 'info') {
        // Проверка поддержки браузерных уведомлений
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/img/notification-icon.png',
                tag: 'flask-helpdesk'
            });
        }

        // Показ in-app уведомления
        const notification = document.createElement('div');
        notification.className = `toast toast-${type}`;
        notification.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        const container = document.querySelector('.toast-container');
        if (container) {
            container.appendChild(notification);

            const toast = new bootstrap.Toast(notification);
            toast.show();
        }
    }

    refreshNotificationsList() {
        // Обновление списка уведомлений через AJAX
        fetch('/tasks/api/notifications?per_page=10')
            .then(response => response.json())
            .then(data => {
                this.updateNotificationsList(data.notifications);
            })
            .catch(error => {
                console.error('Ошибка обновления списка уведомлений:', error);
            });
    }

    updateNotificationsList(notifications) {
        const container = document.querySelector('.notifications-list');
        if (!container) return;

        container.innerHTML = '';

        notifications.forEach(notification => {
            const item = document.createElement('div');
            item.className = `notification-item ${notification.is_read ? 'read' : 'unread'}`;
            item.innerHTML = `
                <div class="notification-content">
                    <div class="notification-title">${notification.old_subj}</div>
                    <div class="notification-meta">
                        ${notification.old_status} → ${notification.new_status}
                    </div>
                    <div class="notification-time">
                        ${new Date(notification.date_created).toLocaleString()}
                    </div>
                </div>
            `;

            container.appendChild(item);
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
        }
    }
}

// Использование
const notificationManager = new NotificationManager();
notificationManager.connect(currentUserId);

// При выходе из системы
window.addEventListener('beforeunload', () => {
    notificationManager.disconnect();
});
```

### Flask Routes

#### API endpoints

```python
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from blog.models import Task, User, Notifications
from blog.utils.decorators import csrf_exempt

# Создание Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Получение задачи по ID."""
    try:
        task = get_redmine_task(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': 'Задача не найдена'
            }), 404

        return jsonify({
            'success': True,
            'task': task
        })

    except Exception as e:
        logger.error(f"Ошибка получения задачи {task_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }), 500

@api_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
@csrf_exempt
@login_required
def update_task_status(task_id):
    """Обновление статуса задачи."""
    try:
        data = request.get_json()
        status_id = data.get('status_id')
        comment = data.get('comment', '')

        if not status_id:
            return jsonify({
                'success': False,
                'message': 'Не указан status_id'
            }), 400

        result = update_redmine_task_status(task_id, status_id, comment)

        if result['success']:
            # Отправка уведомления
            send_task_notification(
                task_id=task_id,
                user_id=current_user.id,
                notification_type='status_change',
                data={
                    'old_status': result.get('old_status'),
                    'new_status': result.get('new_status'),
                    'updated_by': current_user.full_name
                }
            )

            return jsonify({
                'success': True,
                'message': 'Статус обновлен успешно',
                'task': result.get('task')
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Ошибка обновления')
            }), 400

    except Exception as e:
        logger.error(f"Ошибка обновления статуса задачи {task_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }), 500

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Получение уведомлений пользователя."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', False, type=bool)

        query = Notifications.query.filter_by(user_id=current_user.id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(
            Notifications.date_created.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        result = {
            'notifications': [
                {
                    'id': n.id,
                    'issue_id': n.issue_id,
                    'old_status': n.old_status,
                    'new_status': n.new_status,
                    'old_subj': n.old_subj,
                    'date_created': n.date_created.isoformat(),
                    'is_read': n.is_read
                }
                for n in notifications.items
            ],
            'pagination': {
                'page': notifications.page,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'pages': notifications.pages
            }
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Ошибка получения уведомлений: {e}")
        return jsonify({
            'notifications': [],
            'pagination': {'page': 1, 'per_page': 20, 'total': 0, 'pages': 0}
        }), 500
```

## 🗄️ Модели данных

### User (Пользователь)

```python
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    position = db.Column(db.String(120), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_redmine_user = db.Column(db.Boolean, default=False)
    id_redmine_user = db.Column(db.Integer, default=4)
    can_access_quality_control = db.Column(db.Boolean, default=False)
    browser_notifications_enabled = db.Column(db.Boolean, default=False)
    notifications_widget_enabled = db.Column(db.Boolean, default=True)

    # Отношения
    posts = db.relationship("Post", backref="author", lazy=True)
    push_subscriptions = db.relationship("PushSubscription", backref="user", lazy=True)
```

### Notifications (Уведомления)

```python
class Notifications(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    issue_id = db.Column(db.Integer)
    old_status = db.Column(db.Text)
    new_status = db.Column(db.Text)
    old_subj = db.Column(db.Text)
    date_created = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean, default=False)
```

### PushSubscription (Push-подписки)

```python
class PushSubscription(db.Model):
    __tablename__ = "push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## ⚙️ Конфигурация

### Основные настройки

```python
# config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redmine
    REDMINE_URL = os.environ.get('REDMINE_URL')
    REDMINE_API_KEY = os.environ.get('REDMINE_API_KEY')

    # Oracle ERP
    ORACLE_HOST = os.environ.get('ORACLE_HOST')
    ORACLE_PORT = os.environ.get('ORACLE_PORT', 1521)
    ORACLE_SERVICE = os.environ.get('ORACLE_SERVICE')
    ORACLE_USER = os.environ.get('ORACLE_USER')
    ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD')

    # Уведомления
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')

    # Планировщик
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Europe/Moscow"
```

### Переменные окружения

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

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

## 🧪 Тестирование

### Unit тесты

```python
# tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from blog.tasks.api_routes import update_task_status

class TestTaskAPI:
    def test_update_task_status_success(self):
        """Тест успешного обновления статуса."""
        with patch('blog.tasks.api_routes.update_redmine_task_status') as mock_update:
            mock_update.return_value = {'success': True}

            result = update_task_status(12345, 3, "Тест")

            assert result['success'] is True
            mock_update.assert_called_once_with(12345, 3, "Тест")

    def test_update_task_status_failure(self):
        """Тест неудачного обновления статуса."""
        with patch('blog.tasks.api_routes.update_redmine_task_status') as mock_update:
            mock_update.return_value = {'success': False, 'message': 'Ошибка'}

            result = update_task_status(12345, 999, "")

            assert result['success'] is False
            assert 'ошибка' in result['message'].lower()
```

### E2E тесты

```javascript
// tests/e2e/task-management.spec.js
const { test, expect } = require('@playwright/test');

test.describe('Управление задачами', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/users/login');
        await page.fill('#username', 'testuser');
        await page.fill('#password', 'testpass');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('/tasks/my-tasks');
    });

    test('должен изменять статус задачи', async ({ page }) => {
        await page.goto('/tasks/12345');
        await expect(page.locator('.task-status')).toHaveText('Новый');

        await page.selectOption('#status-select', '3');
        await page.fill('#status-comment', 'Начинаю работу');
        await page.click('#update-status-btn');

        await expect(page.locator('.task-status')).toHaveText('В работе');
        await expect(page.locator('.alert-success')).toContainText('Статус обновлен');
    });
});
```

### Запуск тестов

```bash
# Python тесты
pytest tests/ -v --cov=blog

# E2E тесты
npm test

# Все тесты с отчетом
pytest tests/ --cov=blog --cov-report=html && npm test
```

## 🔄 Рабочие процессы

### Типичный workflow

1. **Получение задач**
   ```python
   tasks = get_user_tasks(user_id, status_filter=['Новый', 'В работе'])
   ```

2. **Обновление статуса**
   ```python
   result = update_task_status(task_id, new_status_id, comment)
   ```

3. **Отправка уведомления**
   ```python
   send_notification(user_id, task_id, 'status_change', data)
   ```

4. **Обновление UI**
   ```javascript
   taskManager.updateTaskUI(taskId, taskData);
   ```

### Обработка ошибок

```python
def safe_api_call(func, *args, **kwargs):
    """Безопасный вызов API с обработкой ошибок."""
    try:
        return func(*args, **kwargs)
    except ConnectionError:
        logger.error("Ошибка подключения к внешнему сервису")
        return {'success': False, 'message': 'Сервис недоступен'}
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        return {'success': False, 'message': str(e)}
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return {'success': False, 'message': 'Внутренняя ошибка сервера'}
```

## 🐛 Обработка ошибок

### Логирование

```python
import logging

logger = logging.getLogger(__name__)

def handle_error(error, context=""):
    """Обработка и логирование ошибок."""
    logger.error(f"{context}: {error}", exc_info=True)

    # Отправка уведомления администратору
    if isinstance(error, (ConnectionError, TimeoutError)):
        send_admin_notification(
            title="Ошибка подключения",
            message=f"Проблема с {context}: {error}"
        )
```

### Валидация данных

```python
from marshmallow import Schema, fields, validate

class TaskUpdateSchema(Schema):
    status_id = fields.Integer(required=True, validate=validate.Range(min=1))
    comment = fields.String(validate=validate.Length(max=1000))
    priority_id = fields.Integer(validate=validate.Range(min=1))

def validate_task_update(data):
    """Валидация данных обновления задачи."""
    schema = TaskUpdateSchema()
    try:
        return schema.load(data)
    except ValidationError as e:
        raise ValueError(f"Ошибка валидации: {e.messages}")
```

## ⚡ Производительность

### Кэширование

```python
from functools import lru_cache
from blog.utils.cache_manager import cached_response

@lru_cache(maxsize=128)
def get_status_name(status_id):
    """Кэшированное получение названия статуса."""
    return query_redmine_status(status_id)

@cached_response(timeout=300)
def get_user_tasks(user_id):
    """Кэшированное получение задач пользователя."""
    return query_redmine_tasks(user_id)
```

### Оптимизация запросов

```python
# Плохо - N+1 проблема
for task in tasks:
    assignee = get_user_by_id(task.assignee_id)  # Дополнительный запрос

# Хорошо - предзагрузка
assignee_ids = [task.assignee_id for task in tasks]
assignees = {user.id: user for user in get_users_by_ids(assignee_ids)}
```

## 🔒 Безопасность

### CSRF защита

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

@csrf.exempt
def api_endpoint():
    """API endpoint без CSRF защиты."""
    pass
```

### Валидация входных данных

```python
import re

def sanitize_input(text):
    """Очистка пользовательского ввода."""
    if not text:
        return ""

    # Удаление потенциально опасных символов
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

def validate_user_input(data):
    """Валидация пользовательских данных."""
    if 'comment' in data:
        data['comment'] = sanitize_input(data['comment'])

    if len(data.get('comment', '')) > 1000:
        raise ValueError("Комментарий слишком длинный")
```

---

**Версия**: 2.1.0
**Последнее обновление**: 2024-01-16
