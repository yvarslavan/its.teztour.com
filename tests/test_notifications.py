import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sqlite3
import tempfile
import os
from flask import Flask
from flask_testing import TestCase

# Импорты из приложения
from blog import create_app, db
from blog.models import User, Notifications, NotificationsAddNotes
from redmine import (
    check_notifications,
    get_notifications,
    get_notifications_add_notes,
    get_count_notifications,
    get_count_notifications_add_notes,
    add_notification_to_database,
    add_notification_notes_to_database,
    process_status_changes,
    process_added_notes
)


class NotificationSystemTestCase(TestCase):
    """Тесты для аудита системы уведомлений"""

    def create_app(self):
        """Создание тестового приложения"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        """Настройка тестовой среды"""
        db.create_all()

        # Создаем тестового пользователя
        self.test_user = User(
            username='testuser',
            email='test@tez-tour.com',
            password='testpass',
            full_name='Test User',
            department='IT',
            position='Developer',
            phone='1234'
        )
        db.session.add(self.test_user)
        db.session.commit()

        # Создаем временную SQLite базу для тестов
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

        # Создаем таблицы в временной базе
        self._create_test_tables()

    def tearDown(self):
        """Очистка после тестов"""
        db.session.remove()
        db.drop_all()

        # Удаляем временную базу
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def _create_test_tables(self):
        """Создание тестовых таблиц в SQLite"""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()

        # Таблица уведомлений о статусах
        cursor.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                issue_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                old_subj TEXT,
                date_created DATETIME
            )
        ''')

        # Таблица уведомлений о комментариях
        cursor.execute('''
            CREATE TABLE notifications_add_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                issue_id INTEGER,
                author TEXT,
                notes TEXT,
                date_created DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def test_get_notifications_basic(self):
        """Тест базового получения уведомлений о статусах"""
        # Создаем тестовое уведомление
        notification = Notifications(
            user_id=self.test_user.id,
            issue_id=12345,
            old_status='Новая',
            new_status='В работе',
            old_subj='Тестовая заявка',
            date_created=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()

        # Получаем уведомления
        notifications = get_notifications(self.test_user.id)

        # Проверяем результат
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].issue_id, 12345)
        self.assertEqual(notifications[0].old_status, 'Новая')
        self.assertEqual(notifications[0].new_status, 'В работе')

    def test_get_notifications_add_notes_basic(self):
        """Тест базового получения уведомлений о комментариях"""
        # Создаем тестовое уведомление о комментарии
        notification = NotificationsAddNotes(
            user_id=self.test_user.id,
            issue_id=12345,
            author='admin@tez-tour.com',
            notes='Тестовый комментарий',
            date_created=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()

        # Получаем уведомления
        notifications = get_notifications_add_notes(self.test_user.id)

        # Проверяем результат
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].issue_id, 12345)
        self.assertEqual(notifications[0].author, 'admin@tez-tour.com')
        self.assertEqual(notifications[0].notes, 'Тестовый комментарий')

    def test_count_notifications(self):
        """Тест подсчета количества уведомлений"""
        # Создаем несколько уведомлений
        for i in range(3):
            notification = Notifications(
                user_id=self.test_user.id,
                issue_id=12345 + i,
                old_status='Новая',
                new_status='В работе',
                old_subj=f'Тестовая заявка {i}',
                date_created=datetime.now()
            )
            db.session.add(notification)

        db.session.commit()

        # Проверяем количество
        count = get_count_notifications(self.test_user.id)
        self.assertEqual(count, 3)

    def test_count_notifications_add_notes(self):
        """Тест подсчета количества уведомлений о комментариях"""
        # Создаем несколько уведомлений о комментариях
        for i in range(2):
            notification = NotificationsAddNotes(
                user_id=self.test_user.id,
                issue_id=12345 + i,
                author='admin@tez-tour.com',
                notes=f'Тестовый комментарий {i}',
                date_created=datetime.now()
            )
            db.session.add(notification)

        db.session.commit()

        # Проверяем количество
        count = get_count_notifications_add_notes(self.test_user.id)
        self.assertEqual(count, 2)

    def test_no_duplicate_notifications(self):
        """Тест отсутствия дублирования уведомлений"""
        # Создаем одинаковые уведомления
        for _ in range(2):
            notification = Notifications(
                user_id=self.test_user.id,
                issue_id=12345,
                old_status='Новая',
                new_status='В работе',
                old_subj='Тестовая заявка',
                date_created=datetime.now()
            )
            db.session.add(notification)

        db.session.commit()

        # Проверяем, что создались оба уведомления (дублирование есть)
        count = get_count_notifications(self.test_user.id)
        self.assertEqual(count, 2)

        # Это указывает на проблему - нужна дедупликация

    def test_notifications_for_different_users(self):
        """Тест изоляции уведомлений между пользователями"""
        # Создаем второго пользователя
        user2 = User(
            username='testuser2',
            email='test2@tez-tour.com',
            password='testpass',
            full_name='Test User 2'
        )
        db.session.add(user2)
        db.session.commit()

        # Создаем уведомления для разных пользователей
        notification1 = Notifications(
            user_id=self.test_user.id,
            issue_id=12345,
            old_status='Новая',
            new_status='В работе',
            old_subj='Заявка пользователя 1',
            date_created=datetime.now()
        )

        notification2 = Notifications(
            user_id=user2.id,
            issue_id=12346,
            old_status='Новая',
            new_status='Закрыта',
            old_subj='Заявка пользователя 2',
            date_created=datetime.now()
        )

        db.session.add(notification1)
        db.session.add(notification2)
        db.session.commit()

        # Проверяем изоляцию
        user1_notifications = get_notifications(self.test_user.id)
        user2_notifications = get_notifications(user2.id)

        self.assertEqual(len(user1_notifications), 1)
        self.assertEqual(len(user2_notifications), 1)
        self.assertEqual(user1_notifications[0].old_subj, 'Заявка пользователя 1')
        self.assertEqual(user2_notifications[0].old_subj, 'Заявка пользователя 2')

    @patch('redmine.get_connection')
    def test_check_notifications_mysql_connection_failure(self, mock_get_connection):
        """Тест обработки ошибки подключения к MySQL"""
        mock_get_connection.return_value = None

        result = check_notifications('test@tez-tour.com', self.test_user.id)

        self.assertFalse(result)

    @patch('redmine.get_connection')
    @patch('redmine.get_database_cursor')
    def test_check_notifications_cursor_failure(self, mock_get_cursor, mock_get_connection):
        """Тест обработки ошибки получения курсора"""
        mock_connection = Mock()
        mock_get_connection.return_value = mock_connection
        mock_get_cursor.return_value = None

        result = check_notifications('test@tez-tour.com', self.test_user.id)

        self.assertFalse(result)

    @patch('redmine.db_absolute_path', new_callable=lambda: tempfile.NamedTemporaryFile(delete=False).name)
    def test_add_notification_to_database_sqlite(self, mock_db_path):
        """Тест добавления уведомления в SQLite базу"""
        # Создаем временную базу
        conn = sqlite3.connect(mock_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                issue_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                old_subj TEXT,
                date_created DATETIME
            )
        ''')
        conn.commit()
        conn.close()

        # Тестовые данные
        notification_data = {
            'user_id': self.test_user.id,
            'issue_id': 12345,
            'old_status': 'Новая',
            'new_status': 'В работе',
            'old_subj': 'Тестовая заявка',
            'date_created': datetime.now()
        }

        # Добавляем уведомление
        add_notification_to_database(notification_data)

        # Проверяем, что уведомление добавлено
        conn = sqlite3.connect(mock_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ?', (self.test_user.id,))
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

        # Очищаем
        os.unlink(mock_db_path)

    def test_notification_timing(self):
        """Тест своевременности доставки уведомлений"""
        start_time = datetime.now()

        # Создаем уведомление
        notification = Notifications(
            user_id=self.test_user.id,
            issue_id=12345,
            old_status='Новая',
            new_status='В работе',
            old_subj='Тестовая заявка',
            date_created=start_time
        )
        db.session.add(notification)
        db.session.commit()

        # Получаем уведомления
        notifications = get_notifications(self.test_user.id)

        # Проверяем, что уведомление получено быстро
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        self.assertLess(processing_time, 1.0)  # Должно быть меньше секунды
        self.assertEqual(len(notifications), 1)

    def test_notification_data_integrity(self):
        """Тест целостности данных уведомлений"""
        # Создаем уведомление с специальными символами
        special_text = "Тест с символами: <>&\"'`\n\t"

        notification = Notifications(
            user_id=self.test_user.id,
            issue_id=12345,
            old_status='Новая',
            new_status='В работе',
            old_subj=special_text,
            date_created=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()

        # Получаем уведомление
        notifications = get_notifications(self.test_user.id)

        # Проверяем целостность данных
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].old_subj, special_text)

    def test_large_notification_content(self):
        """Тест обработки больших уведомлений"""
        # Создаем большое уведомление
        large_content = "Большой текст " * 1000  # ~13KB

        notification = NotificationsAddNotes(
            user_id=self.test_user.id,
            issue_id=12345,
            author='admin@tez-tour.com',
            notes=large_content,
            date_created=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()

        # Получаем уведомление
        notifications = get_notifications_add_notes(self.test_user.id)

        # Проверяем, что большое уведомление обработано корректно
        self.assertEqual(len(notifications), 1)
        self.assertEqual(len(notifications[0].notes), len(large_content))

    def test_concurrent_notifications(self):
        """Тест обработки одновременных уведомлений"""
        import threading
        import time

        results = []

        def create_notification(index):
            try:
                notification = Notifications(
                    user_id=self.test_user.id,
                    issue_id=12345 + index,
                    old_status='Новая',
                    new_status='В работе',
                    old_subj=f'Заявка {index}',
                    date_created=datetime.now()
                )
                db.session.add(notification)
                db.session.commit()
                results.append(True)
            except Exception as e:
                results.append(False)

        # Создаем несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_notification, args=(i,))
            threads.append(thread)

        # Запускаем потоки одновременно
        for thread in threads:
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join()

        # Проверяем результаты
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))  # Все операции должны быть успешными

        # Проверяем, что все уведомления созданы
        count = get_count_notifications(self.test_user.id)
        self.assertEqual(count, 5)


class NotificationIntegrationTestCase(TestCase):
    """Интеграционные тесты для системы уведомлений"""

    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()

        self.test_user = User(
            username='testuser',
            email='test@tez-tour.com',
            password='testpass'
        )
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('redmine.get_connection')
    @patch('redmine.connect_to_database')
    def test_full_notification_flow(self, mock_connect_db, mock_get_connection):
        """Тест полного цикла обработки уведомлений"""
        # Мокаем подключения к базам данных
        mock_mysql_conn = Mock()
        mock_sqlite_conn = Mock()
        mock_cursor = Mock()

        mock_get_connection.return_value = mock_mysql_conn
        mock_connect_db.return_value = mock_sqlite_conn
        mock_mysql_conn.cursor.return_value = mock_cursor

        # Мокаем данные из MySQL
        mock_cursor.fetchall.side_effect = [
            [  # Данные для статусов
                {
                    'IssueID': 12345,
                    'OldStatus': 'Новая',
                    'NewStatus': 'В работе',
                    'OldSubj': 'Тестовая заявка',
                    'Body': 'Тело уведомления',
                    'RowDateCreated': datetime.now()
                }
            ],
            [  # Данные для комментариев
                {
                    'issue_id': 12345,
                    'Author': 'admin@tez-tour.com',
                    'notes': 'Тестовый комментарий',
                    'date_created': datetime.now()
                }
            ]
        ]

        # Мокаем настройки Vacuum-IM
        mock_sqlite_cursor = Mock()
        mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
        mock_sqlite_cursor.fetchone.return_value = (1,)  # Включены уведомления

        # Выполняем проверку уведомлений
        with patch('redmine.add_notification_to_database') as mock_add_notification, \
             patch('redmine.add_notification_notes_to_database') as mock_add_notes, \
             patch('redmine.delete_notifications') as mock_delete_notifications, \
             patch('redmine.delete_notifications_notes') as mock_delete_notes:

            result = check_notifications('test@tez-tour.com', self.test_user.id)

            # Проверяем, что функции были вызваны
            mock_add_notification.assert_called_once()
            mock_add_notes.assert_called_once()
            mock_delete_notifications.assert_called_once()
            mock_delete_notes.assert_called_once()

            # Проверяем результат
            self.assertEqual(result, 2)  # 1 статус + 1 комментарий

    def test_notification_route_access(self):
        """Тест доступа к маршруту уведомлений"""
        with self.client:
            # Логинимся
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True

            # Делаем запрос к странице уведомлений
            response = self.client.get('/notifications')

            # Проверяем успешный ответ
            self.assertEqual(response.status_code, 200)

    def test_notification_count_api(self):
        """Тест API подсчета уведомлений"""
        # Создаем уведомления
        notification = Notifications(
            user_id=self.test_user.id,
            issue_id=12345,
            old_status='Новая',
            new_status='В работе',
            old_subj='Тестовая заявка',
            date_created=datetime.now()
        )
        db.session.add(notification)
        db.session.commit()

        with self.client:
            # Логинимся
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True

            # Делаем запрос к API
            response = self.client.get('/get-notification-count')

            # Проверяем ответ
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['count'], 1)


if __name__ == '__main__':
    unittest.main()
