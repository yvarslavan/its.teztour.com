#!/usr/bin/env python3
"""
Скрипт для автоматической инициализации базы данных Flask Helpdesk
Поддерживает создание новой БД, применение миграций и заполнение начальными данными
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
        logging.FileHandler('database_init.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Класс для инициализации базы данных"""

    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else project_root
        self.db_dir = self.app_root / 'blog' / 'db'
        self.db_path = self.db_dir / 'blog.db'
        self.sql_dump_path = self.db_dir / 'blog.db.sql'
        self.migrations_dir = self.app_root / 'migrations'

        # Создаем директории если их нет
        self.db_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🔧 Инициализатор БД запущен")
        logger.info(f"📁 Корневая директория: {self.app_root}")
        logger.info(f"📁 Директория БД: {self.db_dir}")
        logger.info(f"📄 Путь к БД: {self.db_path}")

    def check_environment(self):
        """Проверяет окружение и зависимости"""
        logger.info("🔍 Проверка окружения...")

        # Проверяем наличие Flask приложения
        try:
            from blog import create_app
            logger.info("✅ Flask приложение найдено")
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта Flask приложения: {e}")
            return False

        # Проверяем наличие миграций
        if not self.migrations_dir.exists():
            logger.warning("⚠️  Директория миграций не найдена")
            return False
        else:
            logger.info("✅ Директория миграций найдена")

        # Проверяем flask-migrate
        try:
            import flask_migrate
            logger.info("✅ Flask-Migrate доступен")
        except ImportError:
            logger.error("❌ Flask-Migrate не установлен")
            return False

        return True

    def backup_existing_database(self):
        """Создает резервную копию существующей БД"""
        if self.db_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_dir / f"blog_backup_{timestamp}.db"

            logger.info(f"💾 Создание резервной копии: {backup_path}")
            shutil.copy2(self.db_path, backup_path)
            return backup_path
        return None

    def create_database_from_sql(self):
        """Создает базу данных из SQL дампа"""
        if not self.sql_dump_path.exists():
            logger.error(f"❌ SQL дамп не найден: {self.sql_dump_path}")
            return False

        logger.info("📄 Создание БД из SQL дампа...")

        try:
            # Удаляем существующую БД если есть
            if self.db_path.exists():
                self.db_path.unlink()

            # Создаем новую БД из SQL
            with sqlite3.connect(self.db_path) as conn:
                with open(self.sql_dump_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    conn.executescript(sql_content)
                    conn.commit()

            logger.info("✅ БД успешно создана из SQL дампа")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания БД из SQL: {e}")
            return False

    def init_migrations(self):
        """Инициализирует систему миграций"""
        logger.info("🔄 Инициализация миграций...")

        try:
            # Переходим в корневую директорию проекта
            os.chdir(self.app_root)

            # Проверяем, инициализированы ли миграции
            if not (self.migrations_dir / 'env.py').exists():
                logger.info("📋 Инициализация Flask-Migrate...")
                result = subprocess.run(
                    [sys.executable, '-m', 'flask', 'db', 'init'],
                    capture_output=True,
                    text=True,
                    env=dict(os.environ, FLASK_APP='app.py')
                )

                if result.returncode != 0:
                    logger.error(f"❌ Ошибка инициализации миграций: {result.stderr}")
                    return False

                logger.info("✅ Миграции инициализированы")
            else:
                logger.info("✅ Миграции уже инициализированы")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации миграций: {e}")
            return False

    def apply_migrations(self):
        """Применяет миграции к базе данных"""
        logger.info("🔄 Применение миграций...")

        try:
            os.chdir(self.app_root)

            # Применяем миграции
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
            logger.info(f"📄 Вывод: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка применения миграций: {e}")
            return False

    def create_admin_user(self):
        """Создает администратора по умолчанию"""
        logger.info("👤 Создание пользователя-администратора...")

        try:
            from blog import create_app, db
            from blog.models import User
            from blog import bcrypt

            app = create_app()

            with app.app_context():
                # Проверяем, есть ли уже администратор
                admin = User.query.filter_by(is_admin=True).first()
                if admin:
                    logger.info(f"✅ Администратор уже существует: {admin.username}")
                    return True

                # Создаем администратора
                admin_user = User(
                    username='admin',
                    full_name='Системный администратор',
                    email='admin@tez-tour.com',
                    password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                    is_admin=True,
                    department='IT',
                    position='Администратор системы',
                    image_file='default.jpg'
                )

                db.session.add(admin_user)
                db.session.commit()

                logger.info("✅ Администратор создан (admin/admin123)")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания администратора: {e}")
            return False

    def verify_database(self):
        """Проверяет корректность созданной БД"""
        logger.info("🔍 Проверка базы данных...")

        try:
            from blog import create_app, db
            from blog.models import User, Post, Notifications

            app = create_app()

            with app.app_context():
                # Проверяем основные таблицы
                tables_to_check = [User, Post, Notifications]
                for model in tables_to_check:
                    count = model.query.count()
                    logger.info(f"📊 {model.__tablename__}: {count} записей")

                # Проверяем соединение
                db.session.execute('SELECT 1')
                logger.info("✅ База данных работает корректно")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка проверки БД: {e}")
            return False

    def run_full_initialization(self, force=False, from_sql=False):
        """Выполняет полную инициализацию БД"""
        logger.info("🚀 Запуск полной инициализации базы данных")

        # Проверяем окружение
        if not self.check_environment():
            logger.error("❌ Проверка окружения не пройдена")
            return False

        # Создаем резервную копию если БД существует
        if self.db_path.exists() and not force:
            logger.warning("⚠️  База данных уже существует")
            response = input("Перезаписать? (y/N): ")
            if response.lower() != 'y':
                logger.info("❌ Операция отменена")
                return False

        backup_path = self.backup_existing_database()
        if backup_path:
            logger.info(f"💾 Резервная копия создана: {backup_path}")

        # Выбираем способ создания БД
        if from_sql and self.sql_dump_path.exists():
            # Создаем из SQL дампа
            if not self.create_database_from_sql():
                return False
        else:
            # Создаем через миграции
            if not self.init_migrations():
                return False

            if not self.apply_migrations():
                return False

        # Создаем администратора
        if not self.create_admin_user():
            logger.warning("⚠️  Не удалось создать администратора")

        # Проверяем результат
        if not self.verify_database():
            return False

        logger.info("🎉 Инициализация базы данных завершена успешно!")
        return True

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Инициализация базы данных Flask Helpdesk')
    parser.add_argument('--force', action='store_true', help='Принудительная перезапись БД')
    parser.add_argument('--from-sql', action='store_true', help='Создать БД из SQL дампа')
    parser.add_argument('--app-root', help='Корневая директория приложения')
    parser.add_argument('--check-only', action='store_true', help='Только проверка БД')

    args = parser.parse_args()

    # Создаем инициализатор
    initializer = DatabaseInitializer(args.app_root)

    if args.check_only:
        # Только проверка
        if initializer.verify_database():
            logger.info("✅ База данных в порядке")
            sys.exit(0)
        else:
            logger.error("❌ Проблемы с базой данных")
            sys.exit(1)
    else:
        # Полная инициализация
        success = initializer.run_full_initialization(
            force=args.force,
            from_sql=args.from_sql
        )

        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
