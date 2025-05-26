#!/usr/bin/env python3
"""
Скрипт для тестирования улучшенной системы обработки ошибок подключения к базе данных
"""

import sys
import os
import logging
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mysql_db import execute_quality_query_safe, execute_main_query_safe, db_manager
from blog.utils.connection_monitor import check_database_connections, get_connection_health, log_connection_status
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_db_connection.log')
    ]
)

logger = logging.getLogger(__name__)

def test_quality_database():
    """Тестирование подключения к базе качества"""
    logger.info("=== Тестирование базы данных Quality ===")

    def test_query(session):
        result = session.execute(text("SELECT COUNT(*) as count FROM issues WHERE project_id = 1"))
        return result.scalar()

    result = execute_quality_query_safe(test_query, "тест подключения к quality DB")

    if result is not None:
        logger.info(f"✅ Успешно подключились к базе Quality. Найдено {result} записей в проекте 1")
        return True
    else:
        logger.error("❌ Не удалось подключиться к базе Quality")
        return False

def test_main_database():
    """Тестирование подключения к основной базе"""
    logger.info("=== Тестирование основной базы данных ===")

    def test_query(session):
        result = session.execute(text("SELECT COUNT(*) as count FROM issues"))
        return result.scalar()

    result = execute_main_query_safe(test_query, "тест подключения к main DB")

    if result is not None:
        logger.info(f"✅ Успешно подключились к основной базе. Найдено {result} записей")
        return True
    else:
        logger.error("❌ Не удалось подключиться к основной базе")
        return False

def test_new_issues_query():
    """Тестирование запроса новых обращений"""
    logger.info("=== Тестирование запроса новых обращений ===")

    def query_new_issues(session):
        query = """
            SELECT id, subject, description, created_on
            FROM issues
            WHERE project_id = 1
            AND tracker_id = 1
            AND status_id = 1
            ORDER BY created_on DESC
            LIMIT 5
        """
        result = session.execute(text(query))
        return result.mappings().all()

    issues = execute_quality_query_safe(query_new_issues, "получение новых обращений")

    if issues is not None:
        logger.info(f"✅ Успешно получили {len(issues)} новых обращений")
        for issue in issues:
            logger.info(f"  - Обращение #{issue['id']}: {issue['subject']}")
        return True
    else:
        logger.error("❌ Не удалось получить новые обращения")
        return False

def test_comment_notifications():
    """Тестирование запроса уведомлений о комментариях"""
    logger.info("=== Тестирование запроса уведомлений о комментариях ===")

    def query_notifications(session):
        query = """
            SELECT j.id, j.journalized_id, j.notes, j.created_on,
                   j.user_id, i.subject
            FROM journals j
            INNER JOIN issues i ON j.journalized_id = i.id
            WHERE j.journalized_type = 'Issue'
            AND i.project_id = 1
            AND j.notes IS NOT NULL
            AND TRIM(j.notes) != ''
            AND j.is_read = 0
            ORDER BY j.created_on DESC
            LIMIT 5
        """
        result = session.execute(text(query))
        return result.mappings().all()

    notifications = execute_quality_query_safe(query_notifications, "получение уведомлений о комментариях")

    if notifications is not None:
        logger.info(f"✅ Успешно получили {len(notifications)} уведомлений о комментариях")
        for notification in notifications:
            logger.info(f"  - Уведомление #{notification['id']} для обращения #{notification['journalized_id']}")
        return True
    else:
        logger.error("❌ Не удалось получить уведомления о комментариях")
        return False

def test_connection_monitor():
    """Тестирование монитора соединений"""
    logger.info("=== Тестирование монитора соединений ===")

    try:
        # Проверяем все соединения
        is_connected = check_database_connections()
        logger.info(f"Общий статус соединений: {'✅ Подключены' if is_connected else '❌ Проблемы'}")

        # Получаем детальный отчет
        health = get_connection_health()
        logger.info("Детальный отчет о состоянии:")

        for db_name, db_info in health['databases'].items():
            status_icon = "✅" if db_info['status'] == 'connected' else "❌"
            logger.info(f"  {status_icon} {db_name}: {db_info['status']}")
            if db_info['last_success']:
                logger.info(f"    Последнее успешное подключение: {db_info['last_success']}")
            if db_info['last_error']:
                logger.info(f"    Последняя ошибка: {db_info['last_error']}")

        # Статистика ошибок
        error_stats = health['error_statistics']
        if error_stats['total_errors'] > 0:
            logger.warning(f"Всего ошибок: {error_stats['total_errors']}")
            for operation, count in error_stats['error_details'].items():
                logger.warning(f"  {operation}: {count} ошибок")
        else:
            logger.info("Ошибок не обнаружено")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании монитора: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info(f"Начало тестирования системы обработки ошибок БД - {datetime.now()}")
    logger.info("=" * 60)

    tests = [
        ("Подключение к базе Quality", test_quality_database),
        ("Подключение к основной базе", test_main_database),
        ("Запрос новых обращений", test_new_issues_query),
        ("Запрос уведомлений о комментариях", test_comment_notifications),
        ("Монитор соединений", test_connection_monitor),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Выполняется тест: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Тест '{test_name}' завершился с ошибкой: {str(e)}")
            results.append((test_name, False))

    # Итоговый отчет
    logger.info("\n" + "=" * 60)
    logger.info("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1

    logger.info(f"\nРезультат: {passed}/{total} тестов пройдено")

    if passed == total:
        logger.info("🎉 Все тесты успешно пройдены!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} тестов провалено")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
