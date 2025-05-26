#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления поддержки браузерных пуш-уведомлений
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Выполняет миграцию базы данных"""

    # Путь к базе данных
    db_path = 'blog/db/site.db'

    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False

    print(f"🔄 Начинаю миграцию базы данных: {db_path}")

    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаем резервную копию
        backup_path = f'blog/db/site_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"✅ Создана резервная копия: {backup_path}")

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

        # Создаем индексы для оптимизации
        print("➕ Создаю индексы...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id
                ON push_subscriptions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_push_subscriptions_active
                ON push_subscriptions(is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_active
                ON push_subscriptions(user_id, is_active)
            """)
            print("✅ Индексы созданы")
        except sqlite3.Error as e:
            print(f"⚠️  Предупреждение при создании индексов: {e}")

        # Сохраняем изменения
        conn.commit()

        # Проверяем результат
        cursor.execute("PRAGMA table_info(users)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Обновленные поля в таблице users: {updated_columns}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Существующие таблицы: {tables}")

        conn.close()

        print("🎉 Миграция базы данных завершена успешно!")
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка при миграции базы данных: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def verify_migration():
    """Проверяет успешность миграции"""

    db_path = 'blog/db/site.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем поле browser_notifications_enabled
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'browser_notifications_enabled' not in columns:
            print("❌ Поле browser_notifications_enabled не найдено")
            return False

        # Проверяем таблицу push_subscriptions
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='push_subscriptions'
        """)

        if not cursor.fetchone():
            print("❌ Таблица push_subscriptions не найдена")
            return False

        # Проверяем структуру таблицы push_subscriptions
        cursor.execute("PRAGMA table_info(push_subscriptions)")
        push_columns = [column[1] for column in cursor.fetchall()]
        required_columns = ['id', 'user_id', 'endpoint', 'p256dh_key', 'auth_key',
                          'user_agent', 'created_at', 'last_used', 'is_active']

        missing_columns = [col for col in required_columns if col not in push_columns]
        if missing_columns:
            print(f"❌ Отсутствуют поля в таблице push_subscriptions: {missing_columns}")
            return False

        conn.close()

        print("✅ Миграция прошла успешно - все необходимые поля и таблицы присутствуют")
        return True

    except Exception as e:
        print(f"❌ Ошибка при проверке миграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции базы данных для поддержки пуш-уведомлений")
    print("=" * 60)

    if migrate_database():
        print("\n" + "=" * 60)
        print("🔍 Проверка результатов миграции...")
        if verify_migration():
            print("\n🎉 Миграция завершена успешно!")
            print("\nТеперь можно запускать приложение:")
            print("python wsgi.py")
        else:
            print("\n❌ Миграция завершилась с ошибками")
    else:
        print("\n❌ Миграция не удалась")
