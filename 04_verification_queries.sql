-- Проверочные запросы для проверки миграции
-- Выполнить в базе данных blog.db после выполнения всех миграций

-- Проверка структуры таблицы users (должно включать browser_notifications_enabled)
PRAGMA table_info(users);

-- Проверка структуры таблицы push_subscriptions
PRAGMA table_info(push_subscriptions);

-- Проверка всех таблиц в базе данных
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Проверка всех индексов
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_push%' ORDER BY name;

-- Проверка внешних ключей
PRAGMA foreign_key_list(push_subscriptions);

-- Тестовый запрос для проверки работы новых полей
SELECT id, username, browser_notifications_enabled
FROM users
LIMIT 5;
