"""
Модуль для мониторинга соединений с базами данных
"""
import logging
import time
import socket
from datetime import datetime, timedelta
from mysql_db import execute_quality_query_safe, execute_main_query_safe, db_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ConnectionMonitor:
    """Класс для мониторинга соединений с базами данных"""

    def __init__(self):
        self.last_check = None
        self.connection_status = {
            'quality_db': {'status': 'unknown', 'last_success': None, 'last_error': None},
            'main_db': {'status': 'unknown', 'last_success': None, 'last_error': None}
        }

    def check_quality_database(self):
        """Проверка соединения с базой данных quality"""
        try:
            def test_query(session):
                result = session.execute(text("SELECT 1 as test"))
                return result.scalar()

            result = execute_quality_query_safe(test_query, "проверка соединения с quality DB")

            if result == 1:
                self.connection_status['quality_db']['status'] = 'connected'
                self.connection_status['quality_db']['last_success'] = datetime.now()
                self.connection_status['quality_db']['last_error'] = None
                return True
            else:
                self.connection_status['quality_db']['status'] = 'failed'
                self.connection_status['quality_db']['last_error'] = datetime.now()
                return False

        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с quality DB: {str(e)}")
            self.connection_status['quality_db']['status'] = 'error'
            self.connection_status['quality_db']['last_error'] = datetime.now()
            return False

    def check_main_database(self):
        """Проверка соединения с основной базой данных"""
        try:
            def test_query(session):
                result = session.execute(text("SELECT 1 as test"))
                return result.scalar()

            result = execute_main_query_safe(test_query, "проверка соединения с main DB")

            if result == 1:
                self.connection_status['main_db']['status'] = 'connected'
                self.connection_status['main_db']['last_success'] = datetime.now()
                self.connection_status['main_db']['last_error'] = None
                return True
            else:
                self.connection_status['main_db']['status'] = 'failed'
                self.connection_status['main_db']['last_error'] = datetime.now()
                return False

        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с main DB: {str(e)}")
            self.connection_status['main_db']['status'] = 'error'
            self.connection_status['main_db']['last_error'] = datetime.now()
            return False

    def check_all_connections(self):
        """Проверка всех соединений"""
        self.last_check = datetime.now()

        quality_ok = self.check_quality_database()
        main_ok = self.check_main_database()

        # Получаем статистику ошибок от менеджера подключений
        connection_stats = db_manager.get_connection_status()

        return {
            'quality_db': quality_ok,
            'main_db': main_ok,
            'overall': quality_ok and main_ok,
            'last_check': self.last_check,
            'connection_stats': connection_stats,
            'status_details': self.connection_status
        }

    def get_health_report(self):
        """Получение подробного отчета о состоянии соединений"""
        current_time = datetime.now()

        # Если проверка не проводилась более 5 минут, проводим её
        if self.last_check is None or (current_time - self.last_check) > timedelta(minutes=5):
            self.check_all_connections()

        report = {
            'timestamp': current_time.isoformat(),
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'databases': {}
        }

        for db_name, status in self.connection_status.items():
            report['databases'][db_name] = {
                'status': status['status'],
                'last_success': status['last_success'].isoformat() if status['last_success'] else None,
                'last_error': status['last_error'].isoformat() if status['last_error'] else None,
                'uptime': self._calculate_uptime(status['last_success'], status['last_error'])
            }

        # Добавляем статистику ошибок
        report['error_statistics'] = db_manager.get_connection_status()

        return report

    def _calculate_uptime(self, last_success, last_error):
        """Вычисление времени безотказной работы"""
        if last_success is None:
            return 0

        if last_error is None or last_success > last_error:
            return (datetime.now() - last_success).total_seconds()
        else:
            return 0

# Глобальный экземпляр монитора
connection_monitor = ConnectionMonitor()

def check_database_connections():
    """Функция для быстрой проверки соединений"""
    result = connection_monitor.check_all_connections()
    return result['overall']

def get_connection_health():
    """Получение состояния здоровья соединений"""
    return connection_monitor.get_health_report()

def log_connection_status():
    """Логирование текущего состояния соединений"""
    health = get_connection_health()

    for db_name, db_status in health['databases'].items():
        if db_status['status'] == 'connected':
            logger.info(f"База данных {db_name}: подключена")
        elif db_status['status'] == 'failed':
            logger.warning(f"База данных {db_name}: ошибка подключения")
        else:
            logger.error(f"База данных {db_name}: статус неизвестен")

    error_stats = health['error_statistics']
    if error_stats['total_errors'] > 0:
        logger.warning(f"Всего ошибок подключения: {error_stats['total_errors']}")
        for operation, count in error_stats['error_details'].items():
            logger.warning(f"  {operation}: {count} ошибок")
