# Инструкция по миграции базы данных blog.db

## Обзор
Для поддержки браузерных пуш-уведомлений необходимо добавить:
1. Поле `browser_notifications_enabled` в таблицу `users`
2. Новую таблицу `push_subscriptions`
3. Индексы для оптимизации

## Порядок выполнения

### Вариант 1: Выполнить все сразу
Выполните файл `sql_migration.sql` целиком в вашем SQLite клиенте.

### Вариант 2: Пошаговое выполнение

1. **Добавление поля в таблицу users**
   ```sql
   -- Выполните содержимое файла: 01_add_browser_notifications_field.sql
   ALTER TABLE users
   ADD COLUMN browser_notifications_enabled BOOLEAN DEFAULT 0 NOT NULL;
   ```

2. **Создание таблицы push_subscriptions**
   ```sql
   -- Выполните содержимое файла: 02_create_push_subscriptions_table.sql
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
   ```

3. **Создание индексов**
   ```sql
   -- Выполните содержимое файла: 03_create_indexes.sql
   CREATE INDEX idx_push_subscriptions_user_id ON push_subscriptions(user_id);
   CREATE INDEX idx_push_subscriptions_active ON push_subscriptions(is_active);
   CREATE INDEX idx_push_subscriptions_user_active ON push_subscriptions(user_id, is_active);
   ```

4. **Проверка результата**
   ```sql
   -- Выполните содержимое файла: 04_verification_queries.sql
   PRAGMA table_info(users);
   PRAGMA table_info(push_subscriptions);
   ```

## Способы выполнения SQL

### Через SQLite командную строку:
```bash
sqlite3 blog.db < sql_migration.sql
```

### Через DB Browser for SQLite:
1. Откройте blog.db в DB Browser for SQLite
2. Перейдите на вкладку "Execute SQL"
3. Скопируйте и выполните содержимое sql_migration.sql

### Через Python:
```python
import sqlite3

conn = sqlite3.connect('blog.db')
cursor = conn.cursor()

# Выполните каждый SQL запрос
with open('sql_migration.sql', 'r') as f:
    sql_script = f.read()
    cursor.executescript(sql_script)

conn.commit()
conn.close()
```

## Проверка успешности миграции

После выполнения миграции проверьте:

1. **Поле browser_notifications_enabled добавлено:**
   ```sql
   PRAGMA table_info(users);
   ```
   Должно показать поле `browser_notifications_enabled` типа `BOOLEAN`

2. **Таблица push_subscriptions создана:**
   ```sql
   SELECT name FROM sqlite_master WHERE type='table' AND name='push_subscriptions';
   ```
   Должно вернуть `push_subscriptions`

3. **Индексы созданы:**
   ```sql
   SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_push%';
   ```
   Должно показать 3 индекса

## Откат миграции (если нужно)

Если что-то пошло не так, можно откатить изменения:

```sql
-- Удаление таблицы push_subscriptions
DROP TABLE IF EXISTS push_subscriptions;

-- Удаление поля browser_notifications_enabled (сложнее в SQLite)
-- Потребуется пересоздание таблицы users без этого поля
```

## После миграции

После успешной миграции можно запускать приложение:
```bash
python wsgi.py
```

Браузерные пуш-уведомления будут доступны в интерфейсе приложения.
