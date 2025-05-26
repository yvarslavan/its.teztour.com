-- SQL скрипт для добавления поддержки браузерных пуш-уведомлений
-- Выполнить в базе данных blog.db

-- 1. Добавление поля browser_notifications_enabled в таблицу users
ALTER TABLE users
ADD COLUMN browser_notifications_enabled BOOLEAN DEFAULT 0 NOT NULL;

-- 2. Создание таблицы push_subscriptions
CREATE TABLE push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (user_id, endpoint)
);

-- 3. Создание индексов для оптимизации производительности
CREATE INDEX idx_push_subscriptions_user_id
ON push_subscriptions(user_id);

CREATE INDEX idx_push_subscriptions_active
ON push_subscriptions(is_active);

CREATE INDEX idx_push_subscriptions_user_active
ON push_subscriptions(user_id, is_active);

-- 4. Проверочные запросы (можно выполнить для проверки)
-- Проверка структуры таблицы users
-- PRAGMA table_info(users);

-- Проверка структуры таблицы push_subscriptions
-- PRAGMA table_info(push_subscriptions);

-- Проверка всех таблиц в базе
-- SELECT name FROM sqlite_master WHERE type='table';
