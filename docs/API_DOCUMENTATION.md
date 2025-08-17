# 📚 API Документация Flask Helpdesk System

Полное описание всех API endpoints, функций и компонентов системы управления задачами.

## 📋 Содержание

- [🔐 Аутентификация](#-аутентификация)
- [👥 Пользователи](#-пользователи)
- [📋 Задачи](#-задачи)
- [🔔 Уведомления](#-уведомления)
- [📝 Посты](#-посты)
- [🌐 WebSocket Events](#-websocket-events)
- [🔗 Внешние интеграции](#-внешние-интеграции)
- [🛠️ Утилиты](#️-утилиты)
- [⚙️ Конфигурация](#️-конфигурация)
- [📊 Примеры использования](#-примеры-использования)

## 🔐 Аутентификация

### Вход в систему

**Endpoint:** `POST /users/login`

**Описание:** Аутентификация пользователя через ERP/Oracle или локальную базу данных

**Параметры:**
```json
{
  "username": "string",
  "password": "string",
  "remember": "boolean"
}
```

**Ответ:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@company.com",
    "full_name": "Иван Иванов",
    "is_admin": false,
    "can_access_quality_control": true
  },
  "redirect_url": "/tasks/my-tasks"
}
```

**Пример использования:**
```python
import requests

response = requests.post('http://localhost:5000/users/login', json={
    'username': 'user123',
    'password': 'password123',
    'remember': True
})

if response.status_code == 200:
    user_data = response.json()
    print(f"Пользователь {user_data['user']['full_name']} успешно авторизован")
```

### Выход из системы

**Endpoint:** `GET /users/logout`

**Описание:** Завершение сессии пользователя

**Ответ:**
```json
{
  "success": true,
  "message": "Вы успешно вышли из системы"
}
```

## 👥 Пользователи

### Получение профиля пользователя

**Endpoint:** `GET /users/profile`

**Описание:** Получение данных профиля текущего пользователя

**Ответ:**
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@company.com",
  "full_name": "Иван Иванов",
  "department": "IT",
  "position": "Разработчик",
  "phone": "+7-999-123-45-67",
  "vpn_end_date": "2024-12-31",
  "is_redmine_user": true,
  "id_redmine_user": 123,
  "can_access_quality_control": true,
  "browser_notifications_enabled": true,
  "notifications_widget_enabled": true
}
```

### Обновление профиля

**Endpoint:** `PUT /users/profile`

**Описание:** Обновление данных профиля пользователя

**Параметры:**
```json
{
  "full_name": "Иван Петров",
  "department": "Разработка",
  "position": "Старший разработчик",
  "phone": "+7-999-123-45-68",
  "browser_notifications_enabled": true
}
```

### Обновление VPN даты

**Endpoint:** `PUT /users/vpn-date`

**Описание:** Обновление даты окончания VPN доступа

**Параметры:**
```json
{
  "vpn_end_date": "2024-12-31"
}
```

## 📋 Задачи

### Получение задачи по ID

**Endpoint:** `GET /tasks/api/task/<int:task_id>`

**Описание:** Получение детальной информации о задаче

**Ответ:**
```json
{
  "id": 12345,
  "subject": "Исправить баг в системе уведомлений",
  "description": "Пользователи не получают push-уведомления",
  "status": {
    "id": 2,
    "name": "В работе",
    "color": "#ff9900"
  },
  "priority": {
    "id": 3,
    "name": "Высокий",
    "color": "#ff0000"
  },
  "assignee": {
    "id": 456,
    "name": "Петр Сидоров",
    "email": "petr@company.com"
  },
  "author": {
    "id": 789,
    "name": "Анна Козлова",
    "email": "anna@company.com"
  },
  "project": {
    "id": 1,
    "name": "Flask Helpdesk"
  },
  "created_on": "2024-01-15T10:30:00Z",
  "updated_on": "2024-01-16T14:20:00Z",
  "due_date": "2024-01-20T18:00:00Z",
  "attachments": [
    {
      "id": 1,
      "filename": "screenshot.png",
      "size": 1024000,
      "content_type": "image/png"
    }
  ]
}
```

### Изменение статуса задачи

**Endpoint:** `PUT /tasks/api/task/<int:task_id>/status`

**Описание:** Изменение статуса задачи с комментарием

**Параметры:**
```json
{
  "status_id": 3,
  "comment": "Задача выполнена и протестирована"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Статус задачи успешно изменен",
  "task": {
    "id": 12345,
    "status": {
      "id": 3,
      "name": "Решено",
      "color": "#00ff00"
    }
  }
}
```

### Изменение приоритета задачи

**Endpoint:** `PUT /tasks/api/task/<int:task_id>/priority`

**Описание:** Изменение приоритета задачи

**Параметры:**
```json
{
  "priority_id": 2,
  "comment": "Повышен приоритет по просьбе клиента"
}
```

### Назначение исполнителя

**Endpoint:** `PUT /tasks/api/task/<int:task_id>/assignee`

**Описание:** Назначение или смена исполнителя задачи

**Параметры:**
```json
{
  "assignee_id": 456,
  "comment": "Назначен новый исполнитель"
}
```

### Получение списка задач пользователя

**Endpoint:** `GET /tasks/my-tasks`

**Описание:** Получение всех задач, назначенных текущему пользователю

**Параметры запроса:**
- `status_id` (опционально) - фильтр по статусу
- `priority_id` (опционально) - фильтр по приоритету
- `project_id` (опционально) - фильтр по проекту
- `page` (опционально) - номер страницы
- `per_page` (опционально) - количество задач на странице

**Ответ:**
```json
{
  "tasks": [
    {
      "id": 12345,
      "subject": "Исправить баг в системе уведомлений",
      "status": "В работе",
      "priority": "Высокий",
      "project": "Flask Helpdesk",
      "due_date": "2024-01-20T18:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

### Скачивание вложения

**Endpoint:** `GET /tasks/api/task/<int:task_id>/attachment/<int:attachment_id>/download`

**Описание:** Скачивание файла, прикрепленного к задаче

**Ответ:** Файл для скачивания

## 🔔 Уведомления

### Получение уведомлений пользователя

**Endpoint:** `GET /tasks/api/notifications`

**Описание:** Получение списка уведомлений для текущего пользователя

**Параметры запроса:**
- `page` (опционально) - номер страницы
- `per_page` (опционально) - количество уведомлений на странице
- `unread_only` (опционально) - только непрочитанные

**Ответ:**
```json
{
  "notifications": [
    {
      "id": 1,
      "issue_id": 12345,
      "old_status": "Новый",
      "new_status": "В работе",
      "old_subj": "Исправить баг в системе уведомлений",
      "date_created": "2024-01-16T14:20:00Z",
      "is_read": false,
      "type": "status_change"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15,
    "pages": 1
  }
}
```

### Отметка уведомления как прочитанного

**Endpoint:** `PUT /tasks/api/notifications/<int:notification_id>/read`

**Описание:** Отметка уведомления как прочитанного

**Ответ:**
```json
{
  "success": true,
  "message": "Уведомление отмечено как прочитанное"
}
```

### Подписка на push-уведомления

**Endpoint:** `POST /tasks/api/push-subscribe`

**Описание:** Подписка на браузерные push-уведомления

**Параметры:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BNcRd...",
    "auth": "tBHI..."
  }
}
```

### Отписка от push-уведомлений

**Endpoint:** `DELETE /tasks/api/push-subscribe`

**Описание:** Отписка от браузерных push-уведомлений

**Параметры:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

## 📝 Посты

### Получение списка постов

**Endpoint:** `GET /posts`

**Описание:** Получение списка всех постов (новостей, объявлений)

**Ответ:**
```json
{
  "posts": [
    {
      "id": 1,
      "title": "Обновление системы уведомлений",
      "content": "Добавлена поддержка push-уведомлений...",
      "date_posted": "2024-01-15T10:00:00Z",
      "author": {
        "id": 1,
        "username": "admin",
        "full_name": "Администратор"
      }
    }
  ]
}
```

### Создание нового поста

**Endpoint:** `POST /posts`

**Описание:** Создание нового поста (только для администраторов)

**Параметры:**
```json
{
  "title": "Новое объявление",
  "content": "Содержание объявления..."
}
```

## 🌐 WebSocket Events

### Подключение к уведомлениям

**Event:** `join_notifications`

**Описание:** Подключение пользователя к каналу уведомлений

**Параметры:**
```json
{
  "user_id": 123
}
```

### Получение нового уведомления

**Event:** `new_notification`

**Описание:** Получение нового уведомления в реальном времени

**Данные:**
```json
{
  "id": 1,
  "issue_id": 12345,
  "title": "Изменение статуса задачи",
  "message": "Задача #12345 переведена в статус 'В работе'",
  "type": "status_change",
  "created_at": "2024-01-16T14:20:00Z"
}
```

### Изменение статуса задачи

**Event:** `task_status_changed`

**Описание:** Уведомление об изменении статуса задачи

**Данные:**
```json
{
  "task_id": 12345,
  "old_status": "Новый",
  "new_status": "В работе",
  "updated_by": "Петр Сидоров",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

## 🔗 Внешние интеграции

### Redmine API

#### Получение проектов

**Endpoint:** `GET /api/redmine/projects`

**Описание:** Получение списка проектов из Redmine

**Ответ:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Flask Helpdesk",
      "identifier": "flask-helpdesk",
      "description": "Система управления задачами"
    }
  ]
}
```

#### Получение статусов

**Endpoint:** `GET /api/redmine/statuses`

**Описание:** Получение списка статусов задач из Redmine

**Ответ:**
```json
{
  "statuses": [
    {
      "id": 1,
      "name": "Новый",
      "color": "#0000ff",
      "is_default": true,
      "is_closed": false
    }
  ]
}
```

### Oracle ERP

#### Проверка пользователя

**Endpoint:** `GET /api/erp/user/<username>`

**Описание:** Проверка существования пользователя в ERP

**Ответ:**
```json
{
  "exists": true,
  "user": {
    "username": "user123",
    "full_name": "Иван Иванов",
    "department": "IT",
    "position": "Разработчик"
  }
}
```

## 🛠️ Утилиты

### Сетевой мониторинг

#### Получение статуса хостов

**Endpoint:** `GET /netmonitor/status`

**Описание:** Получение статуса мониторинга сетевых хостов

**Ответ:**
```json
{
  "hosts": [
    {
      "name": "redmine.company.com",
      "ip": "192.168.1.100",
      "status": "online",
      "response_time": 45,
      "last_check": "2024-01-16T14:20:00Z"
    }
  ]
}
```

### Cisco Finesse

#### Получение диалогов

**Endpoint:** `GET /finesse/dialogs`

**Описание:** Получение активных диалогов из Cisco Finesse

**Ответ:**
```json
{
  "dialogs": [
    {
      "id": "dialog123",
      "agent_id": "agent456",
      "call_id": "call789",
      "state": "Connected",
      "start_time": "2024-01-16T14:15:00Z"
    }
  ]
}
```

## ⚙️ Конфигурация

### Получение настроек приложения

**Endpoint:** `GET /api/config`

**Описание:** Получение текущих настроек приложения

**Ответ:**
```json
{
  "redmine": {
    "url": "https://redmine.company.com",
    "api_enabled": true
  },
  "notifications": {
    "push_enabled": true,
    "email_enabled": true,
    "sound_enabled": true
  },
  "features": {
    "kanban_enabled": true,
    "quality_control_enabled": true
  }
}
```

## 📊 Примеры использования

### JavaScript (Frontend)

```javascript
// Подключение к WebSocket
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('Подключен к серверу');
    socket.emit('join_notifications', { user_id: currentUserId });
});

socket.on('new_notification', (data) => {
    console.log('Новое уведомление:', data);
    showNotification(data);
});

// Изменение статуса задачи
async function updateTaskStatus(taskId, statusId, comment) {
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

        const result = await response.json();
        if (result.success) {
            console.log('Статус обновлен:', result.message);
        }
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
    }
}

// Подписка на push-уведомления
async function subscribeToPushNotifications() {
    try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: vapidPublicKey
        });

        await fetch('/tasks/api/push-subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                endpoint: subscription.endpoint,
                keys: {
                    p256dh: btoa(String.fromCharCode.apply(null,
                        new Uint8Array(subscription.getKey('p256dh')))),
                    auth: btoa(String.fromCharCode.apply(null,
                        new Uint8Array(subscription.getKey('auth'))))
                }
            })
        });

        console.log('Подписка на push-уведомления активирована');
    } catch (error) {
        console.error('Ошибка подписки:', error);
    }
}
```

### Python (Backend)

```python
import requests
from flask import jsonify, request
from blog import create_app, db
from blog.models import User, Task

app = create_app()

# Получение задач пользователя
@app.route('/api/user/<int:user_id>/tasks')
def get_user_tasks(user_id):
    user = User.query.get_or_404(user_id)

    # Получение задач из Redmine
    redmine_tasks = get_redmine_user_tasks(user.id_redmine_user)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name
        },
        'tasks': redmine_tasks
    })

# Обновление статуса задачи
@app.route('/api/task/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    data = request.get_json()
    status_id = data.get('status_id')
    comment = data.get('comment', '')

    # Обновление в Redmine
    success = update_redmine_task_status(task_id, status_id, comment)

    if success:
        # Отправка уведомления
        send_task_notification(task_id, 'status_changed', {
            'old_status': get_task_status(task_id),
            'new_status': get_status_name(status_id)
        })

        return jsonify({
            'success': True,
            'message': 'Статус задачи успешно обновлен'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Ошибка обновления статуса'
        }), 400

# Отправка push-уведомления
def send_push_notification(user_id, title, message, data=None):
    user = User.query.get(user_id)
    if not user or not user.browser_notifications_enabled:
        return False

    for subscription in user.push_subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh,
                        'auth': subscription.auth
                    }
                },
                data=json.dumps({
                    'title': title,
                    'message': message,
                    'data': data or {}
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except Exception as e:
            print(f"Ошибка отправки push-уведомления: {e}")

    return True
```

### cURL (Командная строка)

```bash
# Авторизация
curl -X POST http://localhost:5000/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user123", "password": "password123"}' \
  -c cookies.txt

# Получение задач пользователя
curl -X GET http://localhost:5000/tasks/my-tasks \
  -b cookies.txt \
  -H "Accept: application/json"

# Изменение статуса задачи
curl -X PUT http://localhost:5000/tasks/api/task/12345/status \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(cat csrf_token.txt)" \
  -d '{"status_id": 3, "comment": "Задача выполнена"}'

# Получение уведомлений
curl -X GET http://localhost:5000/tasks/api/notifications \
  -b cookies.txt \
  -H "Accept: application/json"

# Отметка уведомления как прочитанного
curl -X PUT http://localhost:5000/tasks/api/notifications/1/read \
  -b cookies.txt \
  -H "X-CSRFToken: $(cat csrf_token.txt)"
```

---

**Версия API:** 2.0.0
**Последнее обновление:** 2024
**Базовый URL:** `http://localhost:5000`
