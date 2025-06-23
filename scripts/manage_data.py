#!/usr/bin/env python3
"""
Скрипт для управления данными Flask Helpdesk
Поддерживает экспорт, импорт, очистку и заполнение тестовыми данными
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_management.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DataManager:
    """Класс для управления данными"""

    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else project_root
        self.db_dir = self.app_root / 'blog' / 'db'
        self.db_path = self.db_dir / 'blog.db'
        self.exports_dir = self.db_dir / 'exports'

        # Создаем директорию для экспортов
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🗄️  Менеджер данных запущен")
        logger.info(f"📁 Корневая директория: {self.app_root}")
        logger.info(f"📄 Путь к БД: {self.db_path}")

    def check_database_exists(self):
        """Проверяет существование базы данных"""
        if not self.db_path.exists():
            logger.error(f"❌ База данных не найдена: {self.db_path}")
            return False

        logger.info("✅ База данных найдена")
        return True

    def export_data(self, tables=None, format='json'):
        """Экспортирует данные из указанных таблиц"""
        if not self.check_database_exists():
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Получаем список всех таблиц если не указано
                if not tables:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tables = [row[0] for row in cursor.fetchall()]

                logger.info(f"📤 Экспорт таблиц: {tables}")

                export_data = {}

                for table in tables:
                    logger.info(f"📋 Экспорт таблицы: {table}")

                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()

                    # Конвертируем Row объекты в словари
                    table_data = []
                    for row in rows:
                        table_data.append(dict(row))

                    export_data[table] = {
                        'count': len(table_data),
                        'data': table_data
                    }

                    logger.info(f"  ✅ {len(table_data)} записей")

                # Сохраняем в файл
                if format.lower() == 'json':
                    export_file = self.exports_dir / f"export_{timestamp}.json"

                    # Кастомный JSON encoder для datetime
                    def json_serializer(obj):
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                    with open(export_file, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2, default=json_serializer)

                elif format.lower() == 'sql':
                    export_file = self.exports_dir / f"export_{timestamp}.sql"

                    with open(export_file, 'w', encoding='utf-8') as f:
                        # Экспорт в SQL формат
                        for table in tables:
                            f.write(f"-- Table: {table}\n")

                            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                            create_sql = cursor.fetchone()
                            if create_sql:
                                f.write(f"{create_sql[0]};\n\n")

                            cursor.execute(f"SELECT * FROM {table}")
                            rows = cursor.fetchall()

                            if rows:
                                # Получаем названия колонок
                                cursor.execute(f"PRAGMA table_info({table})")
                                columns = [col[1] for col in cursor.fetchall()]

                                for row in rows:
                                    values = []
                                    for value in row:
                                        if value is None:
                                            values.append('NULL')
                                        elif isinstance(value, str):
                                            # Экранируем кавычки
                                            escaped = value.replace("'", "''")
                                            values.append(f"'{escaped}'")
                                        else:
                                            values.append(str(value))

                                    f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

                            f.write("\n")

                logger.info(f"✅ Экспорт завершен: {export_file}")
                logger.info(f"📊 Экспортировано таблиц: {len(export_data)}")

                return str(export_file)

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return False

    def import_data(self, import_file, clear_tables=False):
        """Импортирует данные из файла"""
        if not self.check_database_exists():
            return False

        import_path = Path(import_file)
        if not import_path.exists():
            logger.error(f"❌ Файл импорта не найден: {import_file}")
            return False

        logger.info(f"📥 Импорт данных из: {import_file}")

        try:
            from blog import create_app, db

            app = create_app()

            with app.app_context():
                if import_path.suffix.lower() == '.json':
                    # Импорт из JSON
                    with open(import_path, 'r', encoding='utf-8') as f:
                        import_data = json.load(f)

                    for table_name, table_info in import_data.items():
                        logger.info(f"📋 Импорт таблицы: {table_name} ({table_info['count']} записей)")

                        if clear_tables:
                            # Очищаем таблицу перед импортом
                            db.session.execute(f"DELETE FROM {table_name}")
                            logger.info(f"  🗑️  Таблица {table_name} очищена")

                        # Импортируем данные
                        for record in table_info['data']:
                            # Создаем SQL запрос для вставки
                            columns = list(record.keys())
                            values = list(record.values())

                            placeholders = ', '.join(['?' for _ in columns])
                            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                            db.session.execute(sql, values)

                        db.session.commit()
                        logger.info(f"  ✅ Импортировано записей: {len(table_info['data'])}")

                elif import_path.suffix.lower() == '.sql':
                    # Импорт из SQL
                    with open(import_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()

                    # Выполняем SQL скрипт
                    db.session.execute(sql_content)
                    db.session.commit()
                    logger.info("✅ SQL скрипт выполнен")

                logger.info("🎉 Импорт завершен успешно!")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка импорта: {e}")
            return False

    def clear_data(self, tables=None, confirm=False):
        """Очищает данные из указанных таблиц"""
        if not self.check_database_exists():
            return False

        if not confirm:
            logger.warning("⚠️  Операция очистки данных требует подтверждения (--confirm)")
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Получаем список всех таблиц если не указано
                if not tables:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'")
                    tables = [row[0] for row in cursor.fetchall()]

                logger.info(f"🗑️  Очистка таблиц: {tables}")

                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                    logger.info(f"  ✅ Таблица {table} очищена")

                conn.commit()
                logger.info("🎉 Очистка завершена успешно!")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
            return False

    def create_test_data(self):
        """Создает тестовые данные"""
        logger.info("🧪 Создание тестовых данных...")

        try:
            from blog import create_app, db
            from blog.models import User, Post
            from blog import bcrypt

            app = create_app()

            with app.app_context():
                # Создаем тестовых пользователей
                test_users = [
                    {
                        'username': 'testuser1',
                        'full_name': 'Тестовый Пользователь 1',
                        'email': 'test1@tez-tour.com',
                        'password': 'test123',
                        'department': 'IT',
                        'position': 'Разработчик'
                    },
                    {
                        'username': 'testuser2',
                        'full_name': 'Тестовый Пользователь 2',
                        'email': 'test2@tez-tour.com',
                        'password': 'test123',
                        'department': 'Поддержка',
                        'position': 'Специалист'
                    }
                ]

                for user_data in test_users:
                    # Проверяем, не существует ли уже такой пользователь
                    existing_user = User.query.filter_by(username=user_data['username']).first()
                    if not existing_user:
                        user = User(
                            username=user_data['username'],
                            full_name=user_data['full_name'],
                            email=user_data['email'],
                            password=bcrypt.generate_password_hash(user_data['password']).decode('utf-8'),
                            department=user_data['department'],
                            position=user_data['position'],
                            image_file='default.jpg'
                        )
                        db.session.add(user)
                        logger.info(f"👤 Создан пользователь: {user_data['username']}")

                db.session.commit()

                # Создаем тестовые посты
                admin_user = User.query.filter_by(is_admin=True).first()
                if admin_user:
                    test_posts = [
                        {
                            'title': 'Тестовый пост 1',
                            'content': 'Это тестовый пост для проверки функциональности системы.',
                            'user_id': admin_user.id
                        },
                        {
                            'title': 'Обновление системы',
                            'content': 'Информация о последних обновлениях в системе поддержки.',
                            'user_id': admin_user.id
                        }
                    ]

                    for post_data in test_posts:
                        # Проверяем, не существует ли уже такой пост
                        existing_post = Post.query.filter_by(title=post_data['title']).first()
                        if not existing_post:
                            post = Post(
                                title=post_data['title'],
                                content=post_data['content'],
                                user_id=post_data['user_id']
                            )
                            db.session.add(post)
                            logger.info(f"📝 Создан пост: {post_data['title']}")

                    db.session.commit()

                logger.info("🎉 Тестовые данные созданы успешно!")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовых данных: {e}")
            return False

    def get_statistics(self):
        """Получает статистику по базе данных"""
        if not self.check_database_exists():
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                logger.info("📊 Статистика базы данных:")

                # Получаем список всех таблиц
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]

                total_records = 0

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_records += count
                    logger.info(f"  📋 {table}: {count} записей")

                logger.info(f"📊 Всего записей: {total_records}")
                logger.info(f"📊 Всего таблиц: {len(tables)}")

                # Размер файла БД
                db_size = self.db_path.stat().st_size
                db_size_mb = db_size / (1024 * 1024)
                logger.info(f"💾 Размер БД: {db_size_mb:.2f} MB")

                return {
                    'tables': len(tables),
                    'total_records': total_records,
                    'size_mb': db_size_mb,
                    'table_stats': {table: count for table in tables}
                }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return False

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Управление данными Flask Helpdesk')
    parser.add_argument('--app-root', help='Корневая директория приложения')

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # Экспорт
    export_parser = subparsers.add_parser('export', help='Экспорт данных')
    export_parser.add_argument('--tables', nargs='+', help='Список таблиц для экспорта')
    export_parser.add_argument('--format', choices=['json', 'sql'], default='json', help='Формат экспорта')

    # Импорт
    import_parser = subparsers.add_parser('import', help='Импорт данных')
    import_parser.add_argument('file', help='Файл для импорта')
    import_parser.add_argument('--clear', action='store_true', help='Очистить таблицы перед импортом')

    # Очистка
    clear_parser = subparsers.add_parser('clear', help='Очистка данных')
    clear_parser.add_argument('--tables', nargs='+', help='Список таблиц для очистки')
    clear_parser.add_argument('--confirm', action='store_true', help='Подтверждение очистки')

    # Тестовые данные
    subparsers.add_parser('create-test', help='Создать тестовые данные')

    # Статистика
    subparsers.add_parser('stats', help='Показать статистику БД')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Создаем менеджер данных
    manager = DataManager(args.app_root)

    success = False

    if args.command == 'export':
        result = manager.export_data(args.tables, args.format)
        success = bool(result)
        if success:
            logger.info(f"📁 Файл экспорта: {result}")

    elif args.command == 'import':
        success = manager.import_data(args.file, args.clear)

    elif args.command == 'clear':
        success = manager.clear_data(args.tables, args.confirm)

    elif args.command == 'create-test':
        success = manager.create_test_data()

    elif args.command == 'stats':
        success = bool(manager.get_statistics())

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
