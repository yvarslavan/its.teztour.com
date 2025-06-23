#!/usr/bin/env python3
"""
Скрипт для автоматизации полного процесса развертывания Flask Helpdesk
Объединяет все этапы: инициализация БД, миграции, проверки, мониторинг
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
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
        logging.FileHandler('deployment.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DeploymentAutomation:
    """Класс для автоматизации развертывания"""

    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else project_root
        self.scripts_dir = self.app_root / 'scripts'
        self.db_dir = self.app_root / 'blog' / 'db'

        logger.info(f"🚀 Автоматизация развертывания запущена")
        logger.info(f"📁 Корневая директория: {self.app_root}")
        logger.info(f"📁 Директория скриптов: {self.scripts_dir}")

    def run_script(self, script_name, args=None, check_return_code=True):
        """Запускает скрипт и возвращает результат"""
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            logger.error(f"❌ Скрипт не найден: {script_path}")
            return False

        command = [sys.executable, str(script_path)]
        if args:
            command.extend(args)

        logger.info(f"🔧 Запуск: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.app_root
            )

            if result.stdout:
                logger.info(f"📄 Вывод:\n{result.stdout}")

            if result.stderr:
                logger.warning(f"⚠️  Ошибки:\n{result.stderr}")

            if check_return_code and result.returncode != 0:
                logger.error(f"❌ Скрипт завершился с ошибкой: код {result.returncode}")
                return False

            logger.info(f"✅ Скрипт выполнен успешно")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка выполнения скрипта: {e}")
            return False

    def check_prerequisites(self):
        """Проверяет предварительные условия для развертывания"""
        logger.info("🔍 Проверка предварительных условий...")

        # Проверяем наличие скриптов
        required_scripts = [
            'init_database.py',
            'migrate_database.py',
            'manage_data.py',
            'monitor_database.py'
        ]

        missing_scripts = []
        for script in required_scripts:
            if not (self.scripts_dir / script).exists():
                missing_scripts.append(script)

        if missing_scripts:
            logger.error(f"❌ Отсутствуют скрипты: {missing_scripts}")
            return False

        # Проверяем Python окружение
        try:
            import flask
            import flask_sqlalchemy
            import flask_migrate
            logger.info("✅ Все необходимые модули Python доступны")
        except ImportError as e:
            logger.error(f"❌ Отсутствует модуль Python: {e}")
            return False

        # Проверяем структуру проекта
        required_dirs = [
            'blog',
            'migrations',
            'blog/templates'
        ]

        missing_dirs = []
        for dir_name in required_dirs:
            if not (self.app_root / dir_name).exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            logger.error(f"❌ Отсутствуют директории: {missing_dirs}")
            return False

        logger.info("✅ Все предварительные условия выполнены")
        return True

    def deploy_fresh_installation(self):
        """Выполняет развертывание с нуля"""
        logger.info("🆕 Развертывание новой установки...")

        # 1. Инициализация базы данных
        logger.info("📋 Шаг 1: Инициализация базы данных")
        if not self.run_script('init_database.py', ['--from-sql', '--force']):
            logger.error("❌ Не удалось инициализировать базу данных")
            return False

        # 2. Проверка инициализации
        logger.info("📋 Шаг 2: Проверка инициализации")
        if not self.run_script('init_database.py', ['--check-only']):
            logger.error("❌ Проверка инициализации не пройдена")
            return False

        # 3. Создание тестовых данных (опционально)
        logger.info("📋 Шаг 3: Создание тестовых данных")
        self.run_script('manage_data.py', ['create-test'], check_return_code=False)

        # 4. Проверка здоровья БД
        logger.info("📋 Шаг 4: Проверка здоровья БД")
        if not self.run_script('monitor_database.py', ['health']):
            logger.warning("⚠️  Проблемы с здоровьем БД обнаружены")

        logger.info("🎉 Новая установка завершена успешно!")
        return True

    def deploy_update(self):
        """Выполняет обновление существующей установки"""
        logger.info("🔄 Обновление существующей установки...")

        # 1. Проверка текущего состояния
        logger.info("📋 Шаг 1: Проверка текущего состояния")
        if not self.run_script('monitor_database.py', ['health'], check_return_code=False):
            logger.warning("⚠️  Обнаружены проблемы с текущей БД")

        # 2. Применение миграций
        logger.info("📋 Шаг 2: Применение миграций")
        if not self.run_script('migrate_database.py'):
            logger.error("❌ Не удалось применить миграции")
            return False

        # 3. Проверка после миграции
        logger.info("📋 Шаг 3: Проверка после миграции")
        if not self.run_script('migrate_database.py', ['--check-only']):
            logger.error("❌ Проверка после миграции не пройдена")
            return False

        # 4. Финальная проверка здоровья
        logger.info("📋 Шаг 4: Финальная проверка здоровья")
        if not self.run_script('monitor_database.py', ['health']):
            logger.warning("⚠️  Проблемы с здоровьем БД после обновления")

        logger.info("🎉 Обновление завершено успешно!")
        return True

    def deploy_with_backup(self):
        """Выполняет развертывание с созданием резервной копии"""
        logger.info("💾 Развертывание с резервным копированием...")

        # 1. Создание резервной копии
        logger.info("📋 Шаг 1: Создание резервной копии")
        if not self.run_script('manage_data.py', ['export', '--format', 'sql']):
            logger.warning("⚠️  Не удалось создать резервную копию")

        # 2. Обновление
        logger.info("📋 Шаг 2: Выполнение обновления")
        if not self.deploy_update():
            logger.error("❌ Обновление не удалось")
            return False

        # 3. Проверка резервных копий
        logger.info("📋 Шаг 3: Проверка резервных копий")
        self.run_script('monitor_database.py', ['backups'], check_return_code=False)

        logger.info("🎉 Развертывание с резервным копированием завершено!")
        return True

    def generate_deployment_report(self):
        """Генерирует отчет о развертывании"""
        logger.info("📊 Генерация отчета о развертывании...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.app_root / f"deployment_report_{timestamp}.json"

        # Собираем информацию
        deployment_report = {
            'deployment_info': {
                'timestamp': datetime.now().isoformat(),
                'app_root': str(self.app_root),
                'python_version': sys.version,
                'platform': sys.platform
            },
            'database_status': {},
            'performance_check': {},
            'backup_status': {},
            'statistics': {}
        }

        # Запускаем проверки и собираем данные
        try:
            # Проверка здоровья БД
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'monitor_database.py'), 'health'],
                capture_output=True,
                text=True,
                cwd=self.app_root
            )
            if result.returncode == 0:
                deployment_report['database_status']['health'] = 'healthy'
            else:
                deployment_report['database_status']['health'] = 'issues_detected'

            # Статистика БД
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'manage_data.py'), 'stats'],
                capture_output=True,
                text=True,
                cwd=self.app_root
            )
            deployment_report['statistics']['collection_successful'] = result.returncode == 0

        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных для отчета: {e}")
            deployment_report['error'] = str(e)

        # Сохраняем отчет
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(deployment_report, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 Отчет о развертывании сохранен: {report_file}")
        return str(report_file)

    def run_post_deployment_checks(self):
        """Выполняет проверки после развертывания"""
        logger.info("🔍 Выполнение проверок после развертывания...")

        checks_passed = 0
        total_checks = 4

        # 1. Проверка здоровья БД
        logger.info("🔍 Проверка 1/4: Здоровье базы данных")
        if self.run_script('monitor_database.py', ['health'], check_return_code=False):
            checks_passed += 1
            logger.info("✅ Проверка здоровья БД пройдена")
        else:
            logger.warning("⚠️  Проверка здоровья БД не пройдена")

        # 2. Проверка производительности
        logger.info("🔍 Проверка 2/4: Производительность")
        if self.run_script('monitor_database.py', ['performance'], check_return_code=False):
            checks_passed += 1
            logger.info("✅ Проверка производительности пройдена")
        else:
            logger.warning("⚠️  Проверка производительности не пройдена")

        # 3. Проверка миграций
        logger.info("🔍 Проверка 3/4: Состояние миграций")
        if self.run_script('migrate_database.py', ['--check-only'], check_return_code=False):
            checks_passed += 1
            logger.info("✅ Проверка миграций пройдена")
        else:
            logger.warning("⚠️  Проверка миграций не пройдена")

        # 4. Проверка резервных копий
        logger.info("🔍 Проверка 4/4: Резервные копии")
        if self.run_script('monitor_database.py', ['backups'], check_return_code=False):
            checks_passed += 1
            logger.info("✅ Проверка резервных копий пройдена")
        else:
            logger.warning("⚠️  Проверка резервных копий не пройдена")

        success_rate = (checks_passed / total_checks) * 100
        logger.info(f"📊 Результат проверок: {checks_passed}/{total_checks} ({success_rate:.1f}%)")

        if checks_passed == total_checks:
            logger.info("🎉 Все проверки после развертывания пройдены!")
            return True
        elif checks_passed >= total_checks * 0.75:
            logger.warning("⚠️  Большинство проверок пройдено, но есть предупреждения")
            return True
        else:
            logger.error("❌ Критические проблемы обнаружены при проверках")
            return False

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Автоматизация развертывания Flask Helpdesk')
    parser.add_argument('--app-root', help='Корневая директория приложения')

    subparsers = parser.add_subparsers(dest='mode', help='Режим развертывания')

    # Новая установка
    subparsers.add_parser('fresh', help='Новая установка с нуля')

    # Обновление
    subparsers.add_parser('update', help='Обновление существующей установки')

    # Обновление с резервной копией
    subparsers.add_parser('update-safe', help='Безопасное обновление с резервной копией')

    # Только проверки
    subparsers.add_parser('check', help='Только проверки после развертывания')

    # Отчет
    subparsers.add_parser('report', help='Генерация отчета о развертывании')

    # Полный цикл
    full_parser = subparsers.add_parser('full', help='Полный цикл развертывания')
    full_parser.add_argument('--mode', choices=['fresh', 'update'], default='update',
                           help='Режим развертывания для полного цикла')

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        sys.exit(1)

    # Создаем автоматизатор
    automation = DeploymentAutomation(args.app_root)

    success = True

    try:
        # Проверяем предварительные условия
        if not automation.check_prerequisites():
            logger.error("❌ Предварительные условия не выполнены")
            sys.exit(1)

        if args.mode == 'fresh':
            success = automation.deploy_fresh_installation()

        elif args.mode == 'update':
            success = automation.deploy_update()

        elif args.mode == 'update-safe':
            success = automation.deploy_with_backup()

        elif args.mode == 'check':
            success = automation.run_post_deployment_checks()

        elif args.mode == 'report':
            report_file = automation.generate_deployment_report()
            logger.info(f"📄 Отчет создан: {report_file}")

        elif args.mode == 'full':
            # Полный цикл развертывания
            logger.info("🚀 Запуск полного цикла развертывания")

            if args.mode == 'fresh':
                success = automation.deploy_fresh_installation()
            else:
                success = automation.deploy_with_backup()

            if success:
                logger.info("✅ Развертывание завершено, запуск проверок...")
                success = automation.run_post_deployment_checks()

            # Генерируем отчет в любом случае
            automation.generate_deployment_report()

    except KeyboardInterrupt:
        logger.info("⏹️  Развертывание прервано пользователем")
        success = False
    except Exception as e:
        logger.error(f"❌ Критическая ошибка развертывания: {e}")
        success = False

    if success:
        logger.info("🎉 Автоматизация развертывания завершена успешно!")
    else:
        logger.error("❌ Развертывание завершилось с ошибками")

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
