-- Создание индексов для таблицы push_subscriptions
-- Выполнить в базе данных blog.db после создания таблицы push_subscriptions

CREATE INDEX idx_push_subscriptions_user_id
ON push_subscriptions(user_id);

CREATE INDEX idx_push_subscriptions_active
ON push_subscriptions(is_active);

CREATE INDEX idx_push_subscriptions_user_active
ON push_subscriptions(user_id, is_active);
