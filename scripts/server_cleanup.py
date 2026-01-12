#!/usr/bin/env python3
"""
Server Cleanup Script for Flask Helpdesk
Очистка проблемных файлов на сервере, включая flask_session с проблемами прав доступа
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

class ServerCleanup:
    def __init__(self, app_path="/var/www/flask_helpdesk"):
        self.app_path = Path(app_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def check_permissions(self):
        """Проверка прав доступа к файлам"""
        logger.info("Проверка прав доступа к файлам приложения...")

        problematic_dirs = []

        # Проверяем основные директории
        for dir_name in ['flask_session', '__pycache__', 'logs']:
            dir_path = self.app_path / dir_name
            if dir_path.exists():
                try:
                    # Пытаемся создать тестовый файл
                    test_file = dir_path / f"test_{self.timestamp}.tmp"
                    test_file.touch()
                    test_file.unlink()
                    logger.info(f"✅ {dir_name}: права доступа в порядке")
                except PermissionError:
                    logger.warning(f"❌ {dir_name}: проблемы с правами доступа")
                    problematic_dirs.append(str(dir_path))

        return problematic_dirs

    def safe_remove_directory(self, dir_path):
        """Безопасное удаление директории с обработкой ошибок прав доступа"""
        dir_path = Path(dir_path)

        if not dir_path.exists():
            logger.info(f"Директория {dir_path} не существует")
            return True

        logger.info(f"Удаление директории: {dir_path}")

        try:
            # Сначала пытаемся изменить права доступа
            subprocess.run(['chmod', '-R', 'u+w', str(dir_path)],
                         capture_output=True, check=False)

            # Затем удаляем
            shutil.rmtree(dir_path, ignore_errors=True)

            # Проверяем, удалилась ли директория
            if dir_path.exists():
                logger.warning(f"Директория {dir_path} не была полностью удалена")
                # Пытаемся удалить отдельные файлы
                for item in dir_path.rglob('*'):
                    if item.is_file():
                        try:
                            item.unlink()
                        except PermissionError:
                            logger.warning(f"Не удалось удалить файл: {item}")
                return False
            else:
                logger.info(f"✅ Директория {dir_path} успешно удалена")
                return True

        except Exception as e:
            logger.error(f"Ошибка при удалении {dir_path}: {e}")
            return False

    def clean_flask_session(self):
        """Очистка файлов Flask сессий"""
        logger.info("Очистка файлов Flask сессий...")

        session_dir = self.app_path / 'flask_session'
        if not session_dir.exists():
            logger.info("Директория flask_session не найдена")
            return True

        # Подсчитываем файлы
        files_count = len(list(session_dir.glob('*')))
        logger.info(f"Найдено файлов сессий: {files_count}")

        if files_count == 0:
            return True

        # Создаем бэкап списка файлов
        backup_file = self.app_path / f'flask_session_backup_{self.timestamp}.txt'
        try:
            with open(backup_file, 'w') as f:
                for file_path in session_dir.glob('*'):
                    f.write(f"{file_path}\n")
            logger.info(f"Список файлов сохранен в: {backup_file}")
        except Exception as e:
            logger.warning(f"Не удалось создать бэкап списка файлов: {e}")

        # Удаляем файлы сессий
        success = self.safe_remove_directory(session_dir)

        # Пересоздаем директорию с правильными правами
        try:
            session_dir.mkdir(exist_ok=True)
            session_dir.chmod(0o755)
            logger.info("✅ Директория flask_session пересоздана")
        except Exception as e:
            logger.error(f"Ошибка при пересоздании директории flask_session: {e}")

        return success

    def clean_pycache(self):
        """Очистка файлов __pycache__"""
        logger.info("Очистка файлов __pycache__...")

        removed_count = 0

        # Ищем все __pycache__ директории
        for pycache_dir in self.app_path.rglob('__pycache__'):
            if self.safe_remove_directory(pycache_dir):
                removed_count += 1

        # Удаляем .pyc файлы
        pyc_count = 0
        for pyc_file in self.app_path.rglob('*.pyc'):
            try:
                pyc_file.unlink()
                pyc_count += 1
            except PermissionError:
                logger.warning(f"Не удалось удалить .pyc файл: {pyc_file}")

        logger.info(f"✅ Удалено {removed_count} __pycache__ директорий и {pyc_count} .pyc файлов")
        return True

    def clean_logs(self, keep_days=7):
        """Очистка старых лог файлов"""
        logger.info(f"Очистка лог файлов старше {keep_days} дней...")

        logs_dir = self.app_path / 'logs'
        if not logs_dir.exists():
            logger.info("Директория logs не найдена")
            return True

        removed_count = 0
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)

        for log_file in logs_dir.glob('*.log*'):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1
                    logger.info(f"Удален старый лог файл: {log_file.name}")
            except Exception as e:
                logger.warning(f"Не удалось удалить лог файл {log_file}: {e}")

        logger.info(f"✅ Удалено {removed_count} старых лог файлов")
        return True

    def clean_temp_files(self):
        """Очистка временных файлов"""
        logger.info("Очистка временных файлов...")

        temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak']
        removed_count = 0

        for pattern in temp_patterns:
            for temp_file in self.app_path.rglob(pattern):
                try:
                    temp_file.unlink()
                    removed_count += 1
                    logger.info(f"Удален временный файл: {temp_file}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_file}: {e}")

        logger.info(f"✅ Удалено {removed_count} временных файлов")
        return True

    def check_disk_space(self):
        """Проверка свободного места на диске"""
        logger.info("Проверка свободного места на диске...")

        try:
            result = subprocess.run(['df', '-h', str(self.app_path)],
                                  capture_output=True, text=True, check=True)
            logger.info("Информация о диске:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")

            # Извлекаем процент использования
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage_line = lines[1] if len(lines[1].split()) >= 5 else lines[2]
                usage_percent = usage_line.split()[4].rstrip('%')

                if int(usage_percent) > 90:
                    logger.warning(f"⚠️  Диск заполнен на {usage_percent}%")
                elif int(usage_percent) > 80:
                    logger.info(f"ℹ️  Диск заполнен на {usage_percent}%")
                else:
                    logger.info(f"✅ Диск заполнен на {usage_percent}%")

        except Exception as e:
            logger.error(f"Ошибка при проверке диска: {e}")

    def run_full_cleanup(self):
        """Запуск полной очистки"""
        logger.info("="*60)
        logger.info("ЗАПУСК ПОЛНОЙ ОЧИСТКИ СЕРВЕРА")
        logger.info("="*60)

        # Проверяем права доступа
        problematic_dirs = self.check_permissions()
        if problematic_dirs:
            logger.warning("Обнаружены проблемы с правами доступа:")
            for dir_path in problematic_dirs:
                logger.warning(f"  - {dir_path}")

        # Проверяем диск до очистки
        logger.info("\n--- СОСТОЯНИЕ ДИСКА ДО ОЧИСТКИ ---")
        self.check_disk_space()

        # Выполняем очистку
        logger.info("\n--- ВЫПОЛНЕНИЕ ОЧИСТКИ ---")
        self.clean_flask_session()
        self.clean_pycache()
        self.clean_logs()
        self.clean_temp_files()

        # Проверяем диск после очистки
        logger.info("\n--- СОСТОЯНИЕ ДИСКА ПОСЛЕ ОЧИСТКИ ---")
        self.check_disk_space()

        logger.info("="*60)
        logger.info("ОЧИСТКА ЗАВЕРШЕНА")
        logger.info("="*60)

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        app_path = sys.argv[2] if len(sys.argv) > 2 else "/var/www/flask_helpdesk"
    else:
        command = "full"
        app_path = "/var/www/flask_helpdesk"

    cleanup = ServerCleanup(app_path)

    if command == "check":
        cleanup.check_permissions()
        cleanup.check_disk_space()
    elif command == "sessions":
        cleanup.clean_flask_session()
    elif command == "cache":
        cleanup.clean_pycache()
    elif command == "logs":
        cleanup.clean_logs()
    elif command == "temp":
        cleanup.clean_temp_files()
    elif command == "disk":
        cleanup.check_disk_space()
    elif command == "full":
        cleanup.run_full_cleanup()
    else:
        print("Использование:")
        print("  python server_cleanup.py [command] [app_path]")
        print("")
        print("Команды:")
        print("  check     - Проверка прав доступа и диска")
        print("  sessions  - Очистка flask_session файлов")
        print("  cache     - Очистка __pycache__ и .pyc файлов")
        print("  logs      - Очистка старых лог файлов")
        print("  temp      - Очистка временных файлов")
        print("  disk      - Проверка свободного места")
        print("  full      - Полная очистка (по умолчанию)")
        print("")
        print("Примеры:")
        print("  python server_cleanup.py")
        print("  python server_cleanup.py check")
        print("  python server_cleanup.py sessions /var/www/flask_helpdesk")

if __name__ == "__main__":
    main()
