#!/usr/bin/env python3
"""
Скрипт для мониторинга состояния базы данных Flask Helpdesk
Проверяет здоровье БД, производительность и выдает рекомендации
"""

import os
import sys
import sqlite3
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import json

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_monitor.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Класс для мониторинга базы данных"""

    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else project_root
        self.db_dir = self.app_root / 'blog' / 'db'
        self.db_path = self.db_dir / 'blog.db'
        self.reports_dir = self.db_dir / 'reports'

        # Создаем директорию для отчетов
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🔍 Монитор БД запущен")
        logger.info(f"📁 Корневая директория: {self.app_root}")
        logger.info(f"📄 Путь к БД: {self.db_path}")

    def check_database_health(self):
        """Проверяет общее здоровье базы данных"""
        logger.info("🏥 Проверка здоровья базы данных...")

        health_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }

        try:
            if not self.db_path.exists():
                health_report['status'] = 'critical'
                health_report['issues'].append("База данных не найдена")
                return health_report

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Проверка целостности
                logger.info("🔍 Проверка целостности...")
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]

                if integrity_result != 'ok':
                    health_report['status'] = 'critical'
                    health_report['issues'].append(f"Нарушение целостности: {integrity_result}")
                else:
                    logger.info("✅ Целостность БД в порядке")

                # Проверка версии миграции
                logger.info("🔍 Проверка версии миграции...")
                try:
                    cursor.execute("SELECT version_num FROM alembic_version")
                    version = cursor.fetchone()
                    if version:
                        logger.info(f"✅ Версия миграции: {version[0]}")
                    else:
                        health_report['warnings'].append("Версия миграции не определена")
                except sqlite3.Error:
                    health_report['warnings'].append("Таблица alembic_version не найдена")

                # Проверка основных таблиц
                logger.info("🔍 Проверка основных таблиц...")
                required_tables = ['users', 'posts', 'notifications']
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]

                missing_tables = [table for table in required_tables if table not in existing_tables]
                if missing_tables:
                    health_report['status'] = 'critical'
                    health_report['issues'].append(f"Отсутствуют таблицы: {missing_tables}")
                else:
                    logger.info("✅ Все основные таблицы присутствуют")

                # Проверка размера БД
                db_size = self.db_path.stat().st_size
                db_size_mb = db_size / (1024 * 1024)
                logger.info(f"💾 Размер БД: {db_size_mb:.2f} MB")

                if db_size_mb > 100:
                    health_report['warnings'].append(f"Большой размер БД: {db_size_mb:.2f} MB")
                    health_report['recommendations'].append("Рассмотрите архивирование старых данных")

                # Проверка количества записей
                logger.info("🔍 Проверка количества записей...")
                total_records = 0
                for table in existing_tables:
                    if not table.startswith('sqlite_'):
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        total_records += count
                        logger.info(f"  📋 {table}: {count} записей")

                if total_records == 0:
                    health_report['warnings'].append("База данных пуста")
                    health_report['recommendations'].append("Загрузите начальные данные")

                logger.info(f"📊 Всего записей: {total_records}")

        except Exception as e:
            health_report['status'] = 'critical'
            health_report['issues'].append(f"Ошибка проверки: {str(e)}")
            logger.error(f"❌ Ошибка проверки здоровья: {e}")

        # Определяем общий статус
        if health_report['issues']:
            health_report['status'] = 'critical'
        elif health_report['warnings']:
            health_report['status'] = 'warning'

        logger.info(f"🏥 Статус здоровья БД: {health_report['status'].upper()}")

        return health_report

    def check_performance(self):
        """Проверяет производительность базы данных"""
        logger.info("⚡ Проверка производительности...")

        performance_report = {
            'timestamp': datetime.now().isoformat(),
            'query_times': {},
            'recommendations': []
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Тест простого запроса
                start_time = time.time()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                simple_query_time = time.time() - start_time
                performance_report['query_times']['simple_select'] = simple_query_time

                # Тест подсчета записей в users
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM users")
                cursor.fetchone()
                count_query_time = time.time() - start_time
                performance_report['query_times']['count_users'] = count_query_time

                # Анализ производительности
                if simple_query_time > 0.1:
                    performance_report['recommendations'].append("Медленные простые запросы - проверьте диск")

                if count_query_time > 1.0:
                    performance_report['recommendations'].append("Медленный подсчет записей - добавьте индексы")

                logger.info(f"⚡ Простой запрос: {simple_query_time:.4f}s")
                logger.info(f"⚡ Подсчет записей: {count_query_time:.4f}s")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки производительности: {e}")
            performance_report['error'] = str(e)

        return performance_report

    def check_backups(self):
        """Проверяет состояние резервных копий"""
        logger.info("💾 Проверка резервных копий...")

        backup_report = {
            'timestamp': datetime.now().isoformat(),
            'backups_found': [],
            'recommendations': []
        }

        try:
            # Ищем файлы бэкапов в директории БД
            backup_patterns = ['*backup*.db', '*_backup_*.db', 'blog_*.db']

            for pattern in backup_patterns:
                for backup_file in self.db_dir.glob(pattern):
                    if backup_file != self.db_path:
                        backup_info = {
                            'file': backup_file.name,
                            'size_mb': backup_file.stat().st_size / (1024 * 1024),
                            'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                            'age_days': (datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
                        }
                        backup_report['backups_found'].append(backup_info)

            # Сортируем по дате создания (новые первые)
            backup_report['backups_found'].sort(key=lambda x: x['created'], reverse=True)

            # Анализ и рекомендации
            if not backup_report['backups_found']:
                backup_report['recommendations'].append("Резервные копии не найдены - создайте бэкап")
            else:
                logger.info(f"💾 Найдено резервных копий: {len(backup_report['backups_found'])}")

                # Проверяем свежесть последнего бэкапа
                latest_backup = backup_report['backups_found'][0]
                if latest_backup['age_days'] > 7:
                    backup_report['recommendations'].append(
                        f"Последний бэкап создан {latest_backup['age_days']} дней назад - создайте свежий"
                    )

                for backup in backup_report['backups_found'][:5]:  # Показываем последние 5
                    logger.info(f"  💾 {backup['file']}: {backup['size_mb']:.1f}MB, {backup['age_days']} дней назад")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки бэкапов: {e}")
            backup_report['error'] = str(e)

        return backup_report

    def generate_comprehensive_report(self):
        """Генерирует комплексный отчет о состоянии БД"""
        logger.info("📊 Генерация комплексного отчета...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"db_health_report_{timestamp}.json"

        comprehensive_report = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'database_path': str(self.db_path),
                'monitor_version': '1.0'
            },
            'health_check': self.check_database_health(),
            'performance_check': self.check_performance(),
            'backup_status': self.check_backups()
        }

        # Сохраняем отчет
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)

        # Генерируем сводку
        logger.info("📋 СВОДКА ОТЧЕТА:")
        logger.info(f"🏥 Здоровье: {comprehensive_report['health_check']['status'].upper()}")

        if comprehensive_report['health_check']['issues']:
            logger.error("❌ Критические проблемы:")
            for issue in comprehensive_report['health_check']['issues']:
                logger.error(f"   - {issue}")

        if comprehensive_report['health_check']['warnings']:
            logger.warning("⚠️  Предупреждения:")
            for warning in comprehensive_report['health_check']['warnings']:
                logger.warning(f"   - {warning}")

        # Собираем все рекомендации
        all_recommendations = []
        for section in ['health_check', 'performance_check', 'backup_status']:
            if 'recommendations' in comprehensive_report[section]:
                all_recommendations.extend(comprehensive_report[section]['recommendations'])

        if all_recommendations:
            logger.info("💡 Рекомендации:")
            for rec in all_recommendations:
                logger.info(f"   - {rec}")

        logger.info(f"📁 Полный отчет сохранен: {report_file}")

        return str(report_file)

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Мониторинг базы данных Flask Helpdesk')
    parser.add_argument('--app-root', help='Корневая директория приложения')

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # Проверка здоровья
    subparsers.add_parser('health', help='Проверка здоровья БД')

    # Проверка производительности
    subparsers.add_parser('performance', help='Проверка производительности')

    # Проверка бэкапов
    subparsers.add_parser('backups', help='Проверка резервных копий')

    # Полный отчет
    subparsers.add_parser('report', help='Генерация полного отчета')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Создаем монитор
    monitor = DatabaseMonitor(args.app_root)

    success = True

    try:
        if args.command == 'health':
            health = monitor.check_database_health()
            success = health['status'] != 'critical'

        elif args.command == 'performance':
            monitor.check_performance()

        elif args.command == 'backups':
            monitor.check_backups()

        elif args.command == 'report':
            report_file = monitor.generate_comprehensive_report()
            logger.info(f"📄 Отчет создан: {report_file}")

    except Exception as e:
        logger.error(f"❌ Ошибка выполнения команды: {e}")
        success = False

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
