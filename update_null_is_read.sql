-- Обновление NULL значений is_read на FALSE для существующих уведомлений
-- Это нужно для корректной работы кнопки "Прочитано" в виджете

-- Обновляем таблицу уведомлений о статусах
UPDATE notifications
SET is_read = FALSE
WHERE is_read IS NULL;

-- Обновляем таблицу уведомлений о комментариях
UPDATE notifications_add_notes
SET is_read = FALSE
WHERE is_read IS NULL;

-- Проверяем результат
SELECT 'notifications' as table_name,
       COUNT(*) as total_records,
       SUM(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) as read_count,
       SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread_count,
       SUM(CASE WHEN is_read IS NULL THEN 1 ELSE 0 END) as null_count
FROM notifications

UNION ALL

SELECT 'notifications_add_notes' as table_name,
       COUNT(*) as total_records,
       SUM(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) as read_count,
       SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread_count,
       SUM(CASE WHEN is_read IS NULL THEN 1 ELSE 0 END) as null_count
FROM notifications_add_notes;
