#!/usr/bin/env python3
"""
Скрипт для добавления поля browser_notifications_enabled в существующую базу blog.db
"""

import sqlite3
import os

def add_browser_notifications_field():
    """Добавляет поле browser_notifications_enabled в таблицу users"""

    # Путь к базе данных
    db_path = 'blog.db'

    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False

    print(f"🔄 Добавляю поле browser_notifications_enabled в {db_path}")

    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем существующие поля в таблице users
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Существующие поля в таблице users: {existing_columns}")

        # Добавляем поле browser_notifications_enabled если его нет
        if 'browser_notifications_enabled' not in existing_columns:
            print("➕ Добавляю поле browser_notifications_enabled...")
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN browser_notifications_enabled BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("✅ Поле browser_notifications_enabled добавлено")
        else:
            print("ℹ️  Поле browser_notifications_enabled уже существует")

        # Проверяем существование таблицы push_subscriptions
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='push_subscriptions'
        """)

        if not cursor.fetchone():
            print("➕ Создаю таблицу push_subscriptions...")
            cursor.execute("""
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
                )
            """)
            print("✅ Таблица push_subscriptions создана")
        else:
            print("ℹ️  Таблица push_subscriptions уже существует")

        # Сохраняем изменения
        conn.commit()

        # Проверяем результат
        cursor.execute("PRAGMA table_info(users)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Обновленные поля в таблице users: {updated_columns}")

        conn.close()

        print("🎉 Поле успешно добавлено!")
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка при добавлении поля: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Добавление поля browser_notifications_enabled")
    print("=" * 50)

    if add_browser_notifications_field():
        print("\n🎉 Готово! Теперь можно запускать приложение:")
        print("python wsgi.py")
    else:
        print("\n❌ Не удалось добавить поле")
