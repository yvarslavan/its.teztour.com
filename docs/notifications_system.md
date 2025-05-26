# Система уведомлений HelpDesk

## Обзор

Система уведомлений HelpDesk обеспечивает доставку уведомлений пользователям о важных событиях в системе заявок. Система поддерживает два типа уведомлений:

1. **Внутренние уведомления** - отображаются в интерфейсе приложения
2. **Браузерные пуш-уведомления** - отправляются через Web Push API с поддержкой звуковых сигналов

## Архитектура

### Компоненты системы

1. **NotificationService** (`blog/notification_service.py`) - основной сервис обработки уведомлений
2. **BrowserPushService** - сервис браузерных пуш-уведомлений
3. **NotificationDeduplicator** - система дедупликации уведомлений
4. **PushNotificationManager** (`blog/static/js/push-notifications.js`) - клиентский JavaScript
5. **Service Worker** (`blog/static/js/sw.js`) - обработка пуш-уведомлений в браузере

### Модели данных

#### PushSubscription
```python
class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
```

#### User (дополнительные поля)
```python
browser_notifications_enabled = db.Column(db.Boolean, default=False)
push_subscriptions = db.relationship("PushSubscription", backref="user", lazy=True)
```

## Типы уведомлений

### NotificationType (Enum)
- `STATUS_CHANGE` - изменение статуса заявки
- `COMMENT_ADDED` - добавление комментария
- `ISSUE_ASSIGNED` - назначение заявки
- `ISSUE_CREATED` - создание новой заявки

## API Endpoints

### Управление подписками

#### POST /api/push/subscribe
Подписка на браузерные пуш-уведомления.

**Запрос:**
```json
{
  "subscription": {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
      "p256dh": "BNK...",
      "auth": "tBH..."
    }
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Подписка на уведомления успешно оформлена"
}
```

#### POST /api/push/unsubscribe
Отписка от браузерных пуш-уведомлений.

**Запрос:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

#### GET /api/push/status
Получение статуса подписки на пуш-уведомления.

**Ответ:**
```json
{
  "enabled": true,
  "subscriptions_count": 2,
  "has_subscriptions": true
}
```

#### POST /api/push/test
Отправка тестового пуш-уведомления.

#### GET /api/vapid-public-key
Получение публичного VAPID ключа для подписки.

**Ответ:**
```json
{
  "publicKey": "BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9f8HnRG-ATXBdPdk-y1x-SoPGH6RpgAuSPiMtXVBNWBuUjb3C_XY"
}
```

## Конфигурация

### Переменные окружения

```python
# config.py или переменные окружения
VAPID_PRIVATE_KEY = "your-vapid-private-key"
VAPID_PUBLIC_KEY = "your-vapid-public-key"
VAPID_CLAIMS = {
    "sub": "mailto:admin@tez-tour.com"
}
```

### Генерация VAPID ключей

```bash
# Установка py-vapid
pip install py-vapid

# Генерация ключей
vapid --gen

# Получение публичного ключа
vapid --applicationServerKey
```

## Использование

### Клиентская часть

```javascript
// Инициализация менеджера пуш-уведомлений
const pushManager = new PushNotificationManager();

// Проверка поддержки
if (pushManager.isSupported) {
    console.log('Пуш-уведомления поддерживаются');
}

// Подписка на уведомления
await pushManager.subscribe();

// Отписка от уведомлений
await pushManager.unsubscribe();

// Отправка тестового уведомления
await pushManager.sendTestNotification();
```

### Серверная часть

```python
from blog.notification_service import notification_service, NotificationData, NotificationType

# Создание уведомления
notification = NotificationData(
    user_id=user.id,
    issue_id=12345,
    notification_type=NotificationType.STATUS_CHANGE,
    title="Изменение статуса заявки #12345",
    message="Статус изменился с 'Новая' на 'В работе'",
    data={
        'old_status': 'Новая',
        'new_status': 'В работе',
        'subject': 'Тестовая заявка'
    },
    created_at=datetime.now()
)

# Отправка пуш-уведомления
notification_service.push_service.send_push_notification(notification)
```

## Дедупликация уведомлений

Система автоматически предотвращает дублирование уведомлений на основе:
- ID пользователя
- ID заявки
- Типа уведомления
- Содержимого сообщения

Время жизни кеша дедупликации: 60 минут (настраивается).

## Звуковые уведомления

### Звуковой файл
- `default` - `/static/sounds/notification.mp3` (используется для всех типов уведомлений)

### Воспроизведение
Звук воспроизводится через Service Worker и передается клиенту для воспроизведения. Один звуковой файл используется для всех типов уведомлений.

## Обработка ошибок

### Недействительные подписки
Система автоматически помечает недействительные подписки как неактивные при получении HTTP статусов:
- 410 (Gone)
- 413 (Payload Too Large)
- 429 (Too Many Requests)

### Логирование
Все ошибки логируются с соответствующими уровнями:
- `INFO` - успешные операции
- `WARNING` - предупреждения (недействительные подписки)
- `ERROR` - критические ошибки

## Тестирование

### Unit тесты

```bash
# Запуск тестов
python -m pytest tests/test_notifications.py -v

# Запуск с покрытием
python -m pytest tests/test_notifications.py --cov=blog.notification_service
```

### Интеграционные тесты

```python
def test_full_notification_flow():
    # Создание пользователя
    user = create_test_user()

    # Подписка на уведомления
    subscription_data = create_test_subscription()

    # Отправка уведомления
    notification = create_test_notification(user.id)

    # Проверка доставки
    assert notification_delivered(notification)
```

## Мониторинг и метрики

### Ключевые метрики
- Количество активных подписок
- Успешность доставки уведомлений
- Время обработки уведомлений
- Количество дедуплицированных уведомлений

### Логи для мониторинга
```python
logger.info(f"Отправлено {successful_sends} пуш-уведомлений для пользователя {user_id}")
logger.warning(f"Неудачных отправок: {len(failed_subscriptions)}")
logger.error(f"Ошибка при обработке уведомлений: {error}")
```

## Безопасность

### VAPID ключи
- Приватный ключ должен храниться в безопасном месте
- Публичный ключ может быть доступен клиентам
- Регулярная ротация ключей (рекомендуется раз в год)

### Валидация подписок
- Проверка формата endpoint
- Валидация ключей p256dh и auth
- Ограничение количества подписок на пользователя

## Производительность

### Оптимизации
- Батчевая обработка уведомлений
- Кеширование подписок
- Асинхронная отправка
- Дедупликация на уровне приложения

### Рекомендации
- Ограничение частоты отправки уведомлений
- Использование индексов в базе данных
- Мониторинг размера очереди уведомлений

## Совместимость браузеров

### Поддерживаемые браузеры
- Chrome 50+
- Firefox 44+
- Safari 16+ (macOS 13+, iOS 16.4+)
- Edge 17+

### Graceful degradation
Система автоматически определяет поддержку браузера и отключает функциональность для неподдерживаемых браузеров.

## Миграция данных

### Создание таблиц

```sql
-- Создание таблицы подписок
CREATE TABLE push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (user_id, endpoint)
);

-- Добавление поля в таблицу пользователей
ALTER TABLE users ADD COLUMN browser_notifications_enabled BOOLEAN DEFAULT 0;
```

## Troubleshooting

### Частые проблемы

1. **Service Worker не регистрируется**
   - Проверьте HTTPS соединение
   - Убедитесь в корректности пути к sw.js

2. **Уведомления не приходят**
   - Проверьте разрешения браузера
   - Убедитесь в активности подписки
   - Проверьте VAPID ключи

3. **Звук не воспроизводится**
   - Проверьте наличие звуковых файлов
   - Убедитесь в разрешениях на автовоспроизведение

### Отладка

```javascript
// Включение подробного логирования
localStorage.setItem('push-debug', 'true');

// Проверка состояния Service Worker
navigator.serviceWorker.getRegistrations().then(registrations => {
    console.log('Зарегистрированные SW:', registrations);
});

// Проверка подписки
navigator.serviceWorker.ready.then(registration => {
    return registration.pushManager.getSubscription();
}).then(subscription => {
    console.log('Текущая подписка:', subscription);
});
```
