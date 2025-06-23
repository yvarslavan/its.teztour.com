#!/usr/bin/env python3
"""
Временный скрипт очистки сервера Flask Helpdesk
Для запуска в домашней директории пользователя
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_disk_space():
    """Проверка свободного места на диске"""
    logger.info("Проверка свободного места на диске...")

    try:
        result = subprocess.run(['df', '-h', '/var/www'],
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
                logger.warning(f"⚠️  КРИТИЧНО: Диск заполнен на {usage_percent}%")
                return False
            elif int(usage_percent) > 80:
                logger.warning(f"⚠️  Диск заполнен на {usage_percent}%")
                return True
            else:
                logger.info(f"✅ Диск заполнен на {usage_percent}%")
                return True

    except Exception as e:
        logger.error(f"Ошибка при проверке диска: {e}")
        return False

def clean_old_backups():
    """Очистка старых бэкапов"""
    logger.info("Поиск и очистка старых бэкапов...")

    backup_dir = Path("/var/www")
    backup_pattern = "flask_helpdesk_backup_*"

    backups = list(backup_dir.glob(backup_pattern))

    if not backups:
        logger.info("Старые бэкапы не найдены")
        return True

    logger.info(f"Найдено {len(backups)} старых бэкапов:")
    total_size = 0

    for backup in backups:
        try:
            # Получаем размер директории
            result = subprocess.run(['du', '-sh', str(backup)],
                                  capture_output=True, text=True, check=True)
            size = result.stdout.split()[0]
            logger.info(f"  - {backup.name}: {size}")

            # Конвертируем размер в MB для подсчета
            if 'G' in size:
                total_size += float(size.replace('G', '')) * 1024
            elif 'M' in size:
                total_size += float(size.replace('M', ''))

        except Exception as e:
            logger.warning(f"Не удалось получить размер {backup}: {e}")

    logger.warning(f"Общий размер бэкапов: ~{total_size/1024:.1f}GB")

    # Спрашиваем подтверждение
    response = input(f"\n❓ Удалить {len(backups)} старых бэкапов (~{total_size/1024:.1f}GB)? [y/N]: ")

    if response.lower() in ['y', 'yes', 'да']:
        removed_count = 0
        freed_space = 0

        for backup in backups:
            try:
                logger.info(f"Удаление {backup.name}...")

                # Получаем размер перед удалением
                result = subprocess.run(['du', '-sm', str(backup)],
                                      capture_output=True, text=True, check=True)
                size_mb = int(result.stdout.split()[0])

                # Удаляем
                shutil.rmtree(backup)
                removed_count += 1
                freed_space += size_mb

                logger.info(f"✅ Удален {backup.name} ({size_mb}MB)")

            except Exception as e:
                logger.error(f"❌ Ошибка при удалении {backup}: {e}")

        logger.info(f"✅ Удалено {removed_count} бэкапов, освобождено {freed_space}MB")
        return True
    else:
        logger.info("Удаление бэкапов отменено")
        return False

def clean_temp_files():
    """Очистка временных файлов"""
    logger.info("Очистка временных файлов...")

    temp_locations = [
        "/tmp/flask*",
        "/tmp/helpdesk*",
        "/var/tmp/flask*"
    ]

    removed_count = 0

    for pattern in temp_locations:
        try:
            result = subprocess.run(['find', pattern.split('*')[0], '-name', pattern.split('/')[-1], '-type', 'f'],
                                  capture_output=True, text=True, check=False)

            if result.stdout.strip():
                files = result.stdout.strip().split('\n')
                for file_path in files:
                    try:
                        os.unlink(file_path)
                        removed_count += 1
                        logger.info(f"Удален временный файл: {file_path}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить {file_path}: {e}")

        except Exception as e:
            logger.warning(f"Ошибка при поиске файлов {pattern}: {e}")

    logger.info(f"✅ Удалено {removed_count} временных файлов")
    return True

def clean_flask_session():
    """Очистка файлов Flask сессий"""
    logger.info("Очистка файлов Flask сессий...")

    session_dir = Path("/var/www/flask_helpdesk/flask_session")

    if not session_dir.exists():
        logger.info("Директория flask_session не найдена")
        return True

    # Подсчитываем файлы
    try:
        files = list(session_dir.glob('*'))
        files_count = len(files)
        logger.info(f"Найдено файлов сессий: {files_count}")

        if files_count == 0:
            return True

        # Спрашиваем подтверждение
        response = input(f"\n❓ Удалить {files_count} файлов сессий? [y/N]: ")

        if response.lower() in ['y', 'yes', 'да']:
            removed_count = 0

            for file_path in files:
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        removed_count += 1
                except PermissionError:
                    logger.warning(f"Нет прав для удаления: {file_path}")
                except Exception as e:
                    logger.warning(f"Ошибка при удалении {file_path}: {e}")

            logger.info(f"✅ Удалено {removed_count} из {files_count} файлов сессий")

            # Пересоздаем директорию
            if removed_count > 0:
                try:
                    session_dir.chmod(0o755)
                    logger.info("✅ Права доступа к flask_session обновлены")
                except Exception as e:
                    logger.warning(f"Не удалось обновить права: {e}")

            return True
        else:
            logger.info("Очистка flask_session отменена")
            return False

    except Exception as e:
        logger.error(f"Ошибка при работе с flask_session: {e}")
        return False

def main():
    logger.info("="*60)
    logger.info("ЭКСТРЕННАЯ ОЧИСТКА СЕРВЕРА FLASK HELPDESK")
    logger.info("="*60)

    # Проверяем диск до очистки
    logger.info("\n--- СОСТОЯНИЕ ДИСКА ДО ОЧИСТКИ ---")
    disk_critical = not check_disk_space()

    if disk_critical:
        logger.error("🚨 КРИТИЧЕСКОЕ СОСТОЯНИЕ ДИСКА!")
        logger.error("Необходима немедленная очистка!")

    # Очистка старых бэкапов (самое важное)
    logger.info("\n--- ОЧИСТКА СТАРЫХ БЭКАПОВ ---")
    clean_old_backups()

    # Проверяем диск после очистки бэкапов
    logger.info("\n--- СОСТОЯНИЕ ДИСКА ПОСЛЕ ОЧИСТКИ БЭКАПОВ ---")
    check_disk_space()

    # Очистка временных файлов
    logger.info("\n--- ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ ---")
    clean_temp_files()

    # Очистка flask_session (если есть права)
    logger.info("\n--- ОЧИСТКА FLASK SESSION ---")
    clean_flask_session()

    # Финальная проверка диска
    logger.info("\n--- ФИНАЛЬНОЕ СОСТОЯНИЕ ДИСКА ---")
    check_disk_space()

    logger.info("="*60)
    logger.info("ОЧИСТКА ЗАВЕРШЕНА")
    logger.info("="*60)

    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Убедитесь что свободно >2GB места")
    print("2. Запустите развертывание в GitLab CI/CD")
    print("3. После успешного развертывания выполните:")
    print("   sudo systemctl restart flask-helpdesk")
    print("   sudo chown -R www-data:www-data /var/www/flask_helpdesk/flask_session")

if __name__ == "__main__":
    main()
