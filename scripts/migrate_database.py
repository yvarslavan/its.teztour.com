#!/usr/bin/env python3
"""
Скрипт для миграции и обновления базы данных Flask Helpdesk
Обрабатывает обновления схемы и данных при деплое
"""

import os
import sys
import sqlite3
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import shutil
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
        logging.FileHandler('database_migration.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Класс для миграции базы данных"""

    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else project_root
        self.db_dir = self.app_root / 'blog' / 'db'
        self.db_path = self.db_dir / 'blog.db'
        self.migrations_dir = self.app_root / 'migrations'

        logger.info(f"🔄 Мигратор БД запущен")
        logger.info(f"📁 Корневая директория: {self.app_root}")
        logger.info(f"📄 Путь к БД: {self.db_path}")

    def check_database_exists(self):
        """Проверяет существование базы данных"""
        if not self.db_path.exists():
            logger.error(f"❌ База данных не найдена: {self.db_path}")
            return False

        logger.info("✅ База данных найдена")
        return True

    def backup_database(self):
        """Создает резервную копию БД перед миграцией"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_dir / f"blog_pre_migration_{timestamp}.db"

        logger.info(f"💾 Создание резервной копии перед миграцией: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def get_current_migration_version(self):
        """Получает текущую версию миграции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
                result = cursor.fetchone()
                if result:
                    version = result[0]
                    logger.info(f"📋 Текущая версия миграции: {version}")
                    return version
                else:
                    logger.warning("⚠️  Версия миграции не найдена")
                    return None
        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения версии миграции: {e}")
            return None

    def get_available_migrations(self):
        """Получает список доступных миграций"""
        versions_dir = self.migrations_dir / 'versions'
        if not versions_dir.exists():
            logger.error("❌ Директория миграций не найдена")
            return []

        migrations = []
        for file in versions_dir.glob('*.py'):
            if file.name != '__init__.py':
                # Извлекаем версию из имени файла
                version = file.stem.split('_')[0]
                migrations.append({
                    'version': version,
                    'file': file.name,
                    'path': file
                })

        migrations.sort(key=lambda x: x['version'])
        logger.info(f"📋 Найдено миграций: {len(migrations)}")
        for migration in migrations:
            logger.info(f"  - {migration['version']}: {migration['file']}")

        return migrations

    def generate_migration(self, message=None):
        """Генерирует новую миграцию"""
        if not message:
            message = f"auto_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📝 Генерация новой миграции: {message}")

        try:
            os.chdir(self.app_root)

            result = subprocess.run(
                [sys.executable, '-m', 'flask', 'db', 'migrate', '-m', message],
                capture_output=True,
                text=True,
                env=dict(os.environ, FLASK_APP='app.py')
            )

            if result.returncode != 0:
                logger.error(f"❌ Ошибка генерации миграции: {result.stderr}")
                return False

            logger.info("✅ Миграция сгенерирована")
            logger.info(f"📄 Вывод: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка генерации миграции: {e}")
            return False

    def apply_migrations(self):
        """Применяет все доступные миграции"""
        logger.info("🔄 Применение миграций...")

        try:
            os.chdir(self.app_root)

            result = subprocess.run(
                [sys.executable, '-m', 'flask', 'db', 'upgrade'],
                capture_output=True,
                text=True,
                env=dict(os.environ, FLASK_APP='app.py')
            )

            if result.returncode != 0:
                logger.error(f"❌ Ошибка применения миграций: {result.stderr}")
                return False

            logger.info("✅ Миграции успешно применены")
            if result.stdout.strip():
                logger.info(f"📄 Вывод: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка применения миграций: {e}")
            return False

    def rollback_migration(self, target_version=None):
        """Откатывает миграцию к указанной версии"""
        if target_version:
            logger.info(f"⏪ Откат к версии: {target_version}")
            command = [sys.executable, '-m', 'flask', 'db', 'downgrade', target_version]
        else:
            logger.info("⏪ Откат на одну версию назад")
            command = [sys.executable, '-m', 'flask', 'db', 'downgrade']

        try:
            os.chdir(self.app_root)

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=dict(os.environ, FLASK_APP='app.py')
            )

            if result.returncode != 0:
                logger.error(f"❌ Ошибка отката миграции: {result.stderr}")
                return False

            logger.info("✅ Откат выполнен успешно")
            if result.stdout.strip():
                logger.info(f"📄 Вывод: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отката миграции: {e}")
            return False

    def verify_migration_integrity(self):
        """Проверяет целостность миграций"""
        logger.info("🔍 Проверка целостности миграций...")

        try:
            from blog import create_app, db

            app = create_app()

            with app.app_context():
                # Проверяем, что можем подключиться к БД
                db.session.execute('SELECT 1')

                # Проверяем основные таблицы
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()

                required_tables = ['users', 'posts', 'notifications', 'alembic_version']
                missing_tables = [table for table in required_tables if table not in tables]

                if missing_tables:
                    logger.error(f"❌ Отсутствуют таблицы: {missing_tables}")
                    return False

                logger.info(f"✅ Найдено таблиц: {len(tables)}")
                logger.info("✅ Целостность миграций подтверждена")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка проверки целостности: {e}")
            return False

    def run_migration_process(self, auto_generate=False, message=None):
        """Выполняет полный процесс миграции"""
        logger.info("🚀 Запуск процесса миграции")

        # Проверяем существование БД
        if not self.check_database_exists():
            logger.error("❌ База данных не найдена, используйте init_database.py")
            return False

        # Создаем резервную копию
        backup_path = self.backup_database()
        logger.info(f"💾 Резервная копия: {backup_path}")

        # Получаем текущую версию
        current_version = self.get_current_migration_version()

        # Автогенерация миграции если нужно
        if auto_generate:
            if not self.generate_migration(message):
                logger.error("❌ Не удалось сгенерировать миграцию")
                return False

        # Применяем миграции
        if not self.apply_migrations():
            logger.error("❌ Не удалось применить миграции")
            return False

        # Проверяем целостность
        if not self.verify_migration_integrity():
            logger.error("❌ Проверка целостности не пройдена")
            return False

        # Получаем новую версию
        new_version = self.get_current_migration_version()

        if current_version != new_version:
            logger.info(f"🔄 Миграция завершена: {current_version} → {new_version}")
        else:
            logger.info("✅ База данных уже актуальна")

        logger.info("🎉 Процесс миграции завершен успешно!")
        return True

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Миграция базы данных Flask Helpdesk')
    parser.add_argument('--auto-generate', action='store_true',
                       help='Автоматически генерировать миграцию')
    parser.add_argument('--message', '-m', help='Сообщение для миграции')
    parser.add_argument('--rollback', help='Откатить к указанной версии')
    parser.add_argument('--app-root', help='Корневая директория приложения')
    parser.add_argument('--check-only', action='store_true',
                       help='Только проверка целостности')

    args = parser.parse_args()

    # Создаем мигратор
    migrator = DatabaseMigrator(args.app_root)

    if args.check_only:
        # Только проверка
        if migrator.verify_migration_integrity():
            logger.info("✅ Миграции в порядке")
            sys.exit(0)
        else:
            logger.error("❌ Проблемы с миграциями")
            sys.exit(1)

    elif args.rollback:
        # Откат миграции
        success = migrator.rollback_migration(args.rollback)
        sys.exit(0 if success else 1)

    else:
        # Полная миграция
        success = migrator.run_migration_process(
            auto_generate=args.auto_generate,
            message=args.message
        )
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
