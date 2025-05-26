-- Добавление поля browser_notifications_enabled в таблицу users
-- Выполнить в базе данных blog.db

ALTER TABLE users
ADD COLUMN browser_notifications_enabled BOOLEAN DEFAULT 0 NOT NULL;
