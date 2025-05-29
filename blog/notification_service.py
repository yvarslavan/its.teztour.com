"""
Улучшенный сервис уведомлений с поддержкой браузерных пуш-уведомлений
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import threading
from contextlib import contextmanager
from flask import current_app, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
import uuid
from urllib.parse import urlparse
import pymysql.cursors

from blog import db
from blog.models import User, Notifications, NotificationsAddNotes, PushSubscription
import redmine

# Настраиваем логгер сразу
logger = logging.getLogger(__name__)

# Импорт pywebpush
WEBPUSH_AVAILABLE = False
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
    logger.info("pywebpush успешно импортирован")
    print("[INIT] pywebpush успешно импортирован", flush=True)
except ImportError as e:
    logger.error(f"Ошибка импорта pywebpush: {e}")
    print(f"[CRITICAL_ERROR] Ошибка импорта pywebpush: {e}", flush=True)
    # Заглушки для типизации
    class WebPushException(Exception):
        pass
    def webpush(*args, **kwargs):
        raise ImportError("pywebpush не установлен")


class NotificationType(Enum):
    """Типы уведомлений"""
    STATUS_CHANGE = "status_change"
    COMMENT_ADDED = "comment_added"
    ISSUE_ASSIGNED = "issue_assigned"
    ISSUE_CREATED = "issue_created"
    TEST = "test"  # Тип для тестовых уведомлений


@dataclass
class NotificationData:
    """Структура данных уведомления"""
    user_id: int
    issue_id: int
    notification_type: NotificationType
    title: str
    message: str
    data: Dict
    created_at: datetime

    def to_dict(self) -> Dict:
        """Преобразование в словарь для JSON"""
        return {
            'user_id': self.user_id,
            'issue_id': self.issue_id,
            'type': self.notification_type.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }

    def get_hash(self) -> str:
        """Получение хеша для дедупликации"""
        content = f"{self.user_id}:{self.issue_id}:{self.notification_type.value}:{self.message}"
        return hashlib.md5(content.encode()).hexdigest()


class NotificationDeduplicator:
    """Класс для дедупликации уведомлений"""

    def __init__(self, ttl_minutes: int = 60):
        self.ttl_minutes = ttl_minutes
        self._cache = {}
        self._lock = threading.Lock()

    def is_duplicate(self, notification: NotificationData, request_id: Optional[uuid.UUID] = None) -> bool:
        """Проверка на дублирование"""
        # Используем request_id в логах, если он передан
        log_prefix = f"[REQ_ID:{request_id}][DEDUPLICATOR]" if request_id else "[DEDUPLICATOR]"

        with self._lock:
            hash_key = notification.get_hash()
            now = datetime.now()

            # Очищаем устаревшие записи
            self._cleanup_expired(now)

            # Проверяем наличие дубликата
            if hash_key in self._cache:
                logger.info(f"{log_prefix} Проверка хеша: {hash_key}. Результат: ДУБЛИКАТ (Найден в кеше). Время в кеше: {self._cache[hash_key]}")
                return True

            # Добавляем новую запись
            self._cache[hash_key] = now
            logger.info(f"{log_prefix} Проверка хеша: {hash_key}. Результат: НОВЫЙ. Добавлен в кеш с временем {now}")
            return False

    def _cleanup_expired(self, now: datetime):
        """Очистка устаревших записей"""
        cutoff = now - timedelta(minutes=self.ttl_minutes)
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cutoff
        ]
        for key in expired_keys:
            del self._cache[key]


class NotificationService:
    """Улучшенный сервис уведомлений"""

    def __init__(self):
        logger.info("[NotificationService] CONSTRUCTOR CALLED")
        self.deduplicator = NotificationDeduplicator()
        self.push_service = BrowserPushService()
        logger.info(f"[NotificationService] push_service INITIALIZED: {type(self.push_service)}")

    def process_notifications(self, user_email: str, user_id: int) -> int:
        """
        Обработка уведомлений для пользователя

        Returns:
            int: Количество обработанных уведомлений
        """
        request_id = uuid.uuid4()
        logger.info(f"[REQ_ID:{request_id}] Начало обработки уведомлений для пользователя {user_id}, email: {user_email}")

        try:
            # Получаем подключение к MySQL
            connection = redmine.get_connection(
                redmine.db_redmine_host,
                redmine.db_redmine_user_name,
                redmine.db_redmine_password,
                redmine.db_redmine_name
            )

            if not connection:
                logger.error(f"[REQ_ID:{request_id}] Не удалось подключиться к MySQL для пользователя {user_id}")
                return 0

            logger.info(f"[REQ_ID:{request_id}] Успешно подключились к MySQL для пользователя {user_id}")

            total_processed = 0

            try:
                # Обрабатываем уведомления о статусах
                status_count = self._process_status_notifications(
                    connection, user_email, user_id, request_id
                )
                total_processed += status_count

                # Обрабатываем уведомления о комментариях
                comment_count = self._process_comment_notifications(
                    connection, user_email, user_id, request_id
                )
                total_processed += comment_count

                logger.info(f"[REQ_ID:{request_id}] Обработано {total_processed} уведомлений для пользователя {user_id}")
                return total_processed

            finally:
                connection.close()
                logger.info(f"[REQ_ID:{request_id}] Соединение с MySQL закрыто для пользователя {user_id}")

        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Ошибка при обработке уведомлений для пользователя {user_id}: {e}", exc_info=True)
            return 0

    def _process_status_notifications(self, connection, user_email: str, user_id: int, request_id: uuid.UUID) -> int:
        """Обработка уведомлений об изменении статуса"""
        logger.info(f"[REQ_ID:{request_id}] _process_status_notifications для user_id={user_id}")
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            email_part = user_email.lower().split("@")[0]

            query = """
                SELECT ID, IssueID, OldStatus, NewStatus, OldSubj, Body, RowDateCreated
                FROM u_its_update_status
                WHERE LOWER(SUBSTRING_INDEX(Author, '@', 1)) = LOWER(%s)
                ORDER BY RowDateCreated DESC
                LIMIT 50
            """

            logger.info(f"[REQ_ID:{request_id}] MySQL Query (status): {query} с email_part: {email_part}")
            cursor.execute(query, (email_part,))
            rows = cursor.fetchall()
            if not rows:
                logger.info(f"[REQ_ID:{request_id}][MYSQL_FETCH_DEBUG] _process_status_notifications: Для {email_part} из u_its_update_status НЕ НАЙДЕНО НИ ОДНОЙ ЗАПИСИ.")
            else:
                logger.info(f"[REQ_ID:{request_id}][MYSQL_FETCH_DEBUG] _process_status_notifications: Для {email_part} из u_its_update_status НАЙДЕНО {len(rows)} строк.")
                for i, row_data in enumerate(rows):
                    logger.info(f"[REQ_ID:{request_id}][MYSQL_FETCH_DEBUG] _process_status_notifications: Строка {i+1}: {row_data}")
            logger.info(f"[REQ_ID:{request_id}] Получено {len(rows)} строк из u_its_update_status. IDs: {[row.get('ID', 'N/A') for row in rows] if rows else '[]'}")

            processed_count = 0
            notifications_to_save = []
            ids_to_delete_from_mysql = []

            for row in rows:
                notification_data = NotificationData(
                    user_id=user_id,
                    issue_id=row['IssueID'],
                    notification_type=NotificationType.STATUS_CHANGE,
                    title=f"Изменение статуса заявки #{row['IssueID']}",
                    message=f"Статус изменился с '{row['OldStatus']}' на '{row['NewStatus']}'",
                    data={
                        'old_status': row['OldStatus'],
                        'new_status': row['NewStatus'],
                        'subject': row['OldSubj'],
                        'body': row['Body']
                    },
                    created_at=row['RowDateCreated']
                )

                # Проверяем на дублирование
                if not self.deduplicator.is_duplicate(notification_data, request_id):
                    logger.info(f"[REQ_ID:{request_id}] Статус-уведомление (MySQL ID: {row['ID']}) не дубликат, добавляем к сохранению.")
                    notifications_to_save.append(notification_data)
                    ids_to_delete_from_mysql.append(row['ID'])
                    processed_count += 1
                else:
                    logger.info(f"[REQ_ID:{request_id}] Статус-уведомление (MySQL ID: {row['ID']}) определено как дубликат Deduplicator-ом.")

            # Сохраняем уведомления в базу
            if notifications_to_save:
                logger.info(f"[REQ_ID:{request_id}] Планируется сохранить {len(notifications_to_save)} статус-уведомлений. IDs из MySQL для удаления: {ids_to_delete_from_mysql}")
                self._save_status_notifications(notifications_to_save, request_id)

                # Отправляем браузерные пуш-уведомления
                for notification in notifications_to_save:
                    logger.info(f"[REQ_ID:{request_id}][PUSH_STATUS_PRE_SEND] Готовимся отправить PUSH для статус-уведомления (MySQL ID: {row['ID'] if 'ID' in row else 'N/A'}, Issue ID: {notification.issue_id}). Данные уведомления: {notification.to_dict()}")
                    try:
                        self.push_service.send_push_notification(notification)
                        logger.info(f"[REQ_ID:{request_id}][PUSH_STATUS_POST_SEND_SUCCESS] PUSH для статус-уведомления (Issue ID: {notification.issue_id}) ВЫЗВАН (результат см. в логах push_service).")
                    except Exception as e_push:
                        logger.error(f"[REQ_ID:{request_id}][PUSH_STATUS_POST_SEND_ERROR] ОШИБКА при вызове send_push_notification для статус-уведомления (Issue ID: {notification.issue_id}): {e_push}", exc_info=True)

                # Удаляем успешно обработанные записи из MySQL по их ID
                if ids_to_delete_from_mysql:
                    self._delete_processed_status_notifications(connection, ids_to_delete_from_mysql, request_id)
            else:
                logger.info(f"[REQ_ID:{request_id}] Нет новых статус-уведомлений для сохранения.")

            cursor.close()
            return processed_count

        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Ошибка при обработке уведомлений о статусах: {e}", exc_info=True)
            return 0

    def _process_comment_notifications(self, connection, user_email: str, user_id: int, request_id: uuid.UUID) -> int:
        """Обработка уведомлений о комментариях"""
        logger.info(f"[REQ_ID:{request_id}] _process_comment_notifications для user_id={user_id}")
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            email_part = user_email.lower().split("@")[0]

            query = """
                SELECT ID, issue_id, Author, notes, date_created
                FROM u_its_add_notes
                WHERE LOWER(SUBSTRING_INDEX(Author, '@', 1)) = LOWER(%s)
                ORDER BY date_created DESC
                LIMIT 50
            """

            logger.info(f"[REQ_ID:{request_id}] MySQL Query (comment): {query} с email_part: {email_part}")
            cursor.execute(query, (email_part,))
            rows = cursor.fetchall()
            logger.info(f"[REQ_ID:{request_id}] Получено {len(rows)} строк из u_its_add_notes. IDs: {[row.get('ID', 'N/A') for row in rows] if rows else '[]'}")

            processed_count = 0
            notifications_to_save = []
            ids_to_delete_from_mysql = []

            for row in rows:
                notification_data = NotificationData(
                    user_id=user_id,
                    issue_id=row['issue_id'],
                    notification_type=NotificationType.COMMENT_ADDED,
                    title=f"Новый комментарий к заявке #{row['issue_id']}",
                    message=f"Добавлен комментарий от {row['Author']}",
                    data={
                        'author': row['Author'],
                        'notes': row['notes'][:200] + '...' if len(row['notes']) > 200 else row['notes']
                    },
                    created_at=row['date_created']
                )

                # Проверяем на дублирование
                if not self.deduplicator.is_duplicate(notification_data, request_id):
                    logger.info(f"[REQ_ID:{request_id}] Коммент-уведомление (MySQL ID: {row['ID']}) не дубликат, добавляем к сохранению.")
                    notifications_to_save.append(notification_data)
                    ids_to_delete_from_mysql.append(row['ID'])
                    processed_count += 1
                else:
                    logger.info(f"[REQ_ID:{request_id}] Коммент-уведомление (MySQL ID: {row['ID']}) определено как дубликат Deduplicator-ом.")

            # Сохраняем уведомления в базу
            if notifications_to_save:
                logger.info(f"[REQ_ID:{request_id}] Планируется сохранить {len(notifications_to_save)} коммент-уведомлений. IDs из MySQL для удаления: {ids_to_delete_from_mysql}")
                self._save_comment_notifications(notifications_to_save, request_id)

                # Отправляем браузерные пуш-уведомления
                for notification in notifications_to_save:
                    logger.info(f"[REQ_ID:{request_id}][PUSH_COMMENT_PRE_SEND] Готовимся отправить PUSH для коммент-уведомления (MySQL ID: {row['ID'] if 'ID' in row else 'N/A'}, Issue ID: {notification.issue_id}). Данные уведомления: {notification.to_dict()}")
                    try:
                        self.push_service.send_push_notification(notification)
                        logger.info(f"[REQ_ID:{request_id}][PUSH_COMMENT_POST_SEND_SUCCESS] PUSH для коммент-уведомления (Issue ID: {notification.issue_id}) ВЫЗВАН (результат см. в логах push_service).")
                    except Exception as e_push:
                        logger.error(f"[REQ_ID:{request_id}][PUSH_COMMENT_POST_SEND_ERROR] ОШИБКА при вызове send_push_notification для коммент-уведомления (Issue ID: {notification.issue_id}): {e_push}", exc_info=True)

                # Удаляем успешно обработанные записи из MySQL по их ID
                if ids_to_delete_from_mysql:
                    self._delete_processed_comment_notifications(connection, ids_to_delete_from_mysql, request_id)
            else:
                logger.info(f"[REQ_ID:{request_id}] Нет новых коммент-уведомлений для сохранения.")

            cursor.close()
            return processed_count

        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Ошибка при обработке уведомлений о комментариях: {e}", exc_info=True)
            return 0

    def _save_status_notifications(self, notifications: List[NotificationData], request_id: uuid.UUID):
        """
        Сохраняет список уведомлений об изменении статуса в базу данных
        и отправляет push-уведомления.
        """
        logger.info(f"[REQ_ID:{request_id}] _save_status_notifications: {len(notifications)} уведомлений")
        if not notifications:
            logger.info(f"[REQ_ID:{request_id}] Нет статус-уведомлений для сохранения.")
            return

        # Контекст приложения УЖЕ должен быть установлен выше по стеку вызовов,
        # когда этот метод вызывается из планировщика (через scheduled_check_all_user_notifications).
        # Повторная попытка получить его через current_app здесь может вызывать проблемы,
        # если current_app не ссылается на правильный инстанс в этом потоке.

        # Удаляем: with current_app.app_context():
        new_db_notifications = []
        notifications_to_send_push = []

        for notification_data in notifications:
            try:
                # Проверка, существует ли уже такое уведомление для данного пользователя и задачи
                existing_notification = Notifications.query.filter_by(
                    user_id=notification_data.user_id,
                    issue_id=notification_data.issue_id,
                    old_status=notification_data.data.get("old_status"),
                    new_status=notification_data.data.get("new_status"),
                    old_subj=notification_data.title # Предполагаем, что title из NotificationData соответствует old_subj
                ).first()

                if existing_notification:
                    logger.info(f"[REQ_ID:{request_id}] Уведомление для задачи {notification_data.issue_id} (статус) уже существует, пропускаем.")
                    continue

                # Аргументы должны соответствовать конструктору Notifications
                db_notification = Notifications(
                    user_id=notification_data.user_id,
                    issue_id=notification_data.issue_id,
                    old_status=notification_data.data.get("old_status"),
                    new_status=notification_data.data.get("new_status"),
                    old_subj=notification_data.title, # title из NotificationData как old_subj
                    date_created=notification_data.created_at
                    # Поля is_read, is_new, author, body, type - отсутствуют в конструкторе Notifications
                    # и должны управляться либо значениями по умолчанию в модели (если есть),
                    # либо устанавливаться отдельно после создания объекта, если это необходимо.
                    # В данном случае, модель Notifications не имеет этих полей, кроме тех, что в конструкторе.
                )
                new_db_notifications.append(db_notification)
                notifications_to_send_push.append(notification_data)
                logger.debug(f"[REQ_ID:{request_id}] Подготовлено к сохранению Notification: {db_notification!r}")

            except Exception as e:
                logger.error(f"[REQ_ID:{request_id}] Ошибка при подготовке уведомления о статусе для сохранения: {e}", exc_info=True)

        if new_db_notifications:
            try:
                db.session.add_all(new_db_notifications)
                db.session.commit()
                logger.info(f"[REQ_ID:{request_id}] Успешно сохранено {len(new_db_notifications)} новых статус-уведомлений в БД.")

                # Отправляем push-уведомления только для успешно сохраненных
                for nd_data in notifications_to_send_push:
                    logger.info(f"[REQ_ID:{request_id}] Инициируем отправку push-уведомления для статус-изменения задачи {nd_data.issue_id}")
                    self.push_service.send_push_notification(nd_data)

            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"[REQ_ID:{request_id}] Ошибка SQLAlchemy при сохранении статус-уведомлений: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"[REQ_ID:{request_id}] Непредвиденная ошибка при сохранении статус-уведомлений или отправке push: {e}", exc_info=True)
        else:
            logger.info(f"[REQ_ID:{request_id}] Нет новых уникальных статус-уведомлений для сохранения в БД.")

    def _save_comment_notifications(self, notifications: List[NotificationData], request_id: uuid.UUID):
        """
        Сохраняет список уведомлений о новых комментариях в базу данных
        и отправляет push-уведомления.
        """
        logger.info(f"[REQ_ID:{request_id}] _save_comment_notifications: {len(notifications)} уведомлений")
        if not notifications:
            logger.info(f"[REQ_ID:{request_id}] Нет коммент-уведомлений для сохранения.")
            return

        # Контекст приложения УЖЕ должен быть установлен выше по стеку вызовов.
        # Удаляем: with current_app.app_context():
        new_db_notifications = []
        notifications_to_send_push = []

        for notification_data in notifications:
            try:
                # Проверка, существует ли уже такое уведомление
                existing_notification = NotificationsAddNotes.query.filter_by(
                    user_id=notification_data.user_id,
                    issue_id=notification_data.issue_id,
                    notes=notification_data.message, # message из NotificationData - это сам комментарий
                    author=notification_data.data.get("author")
                ).first()

                if existing_notification:
                    logger.info(f"[REQ_ID:{request_id}] Уведомление для задачи {notification_data.issue_id} (комментарий) уже существует, пропускаем.")
                    continue

                # Аргументы должны соответствовать конструктору NotificationsAddNotes
                db_notification = NotificationsAddNotes(
                    user_id=notification_data.user_id,
                    issue_id=notification_data.issue_id,
                    author=notification_data.data.get("author"),
                    notes=notification_data.message, # message из NotificationData
                    date_created=notification_data.created_at
                    # Поля is_read, is_new, type, subj - отсутствуют в конструкторе NotificationsAddNotes
                    # и должны управляться либо значениями по умолчанию в модели (если есть),
                    # либо устанавливаться отдельно после создания объекта, если это необходимо.
                )
                new_db_notifications.append(db_notification)
                notifications_to_send_push.append(notification_data)
                logger.debug(f"[REQ_ID:{request_id}] Подготовлено к сохранению NotificationAddNotes: {db_notification!r}")

            except Exception as e:
                logger.error(f"[REQ_ID:{request_id}] Ошибка при подготовке уведомления о комментарии для сохранения: {e}", exc_info=True)

        if new_db_notifications:
            try:
                db.session.add_all(new_db_notifications)
                db.session.commit()
                logger.info(f"[REQ_ID:{request_id}] Успешно сохранено {len(new_db_notifications)} новых коммент-уведомлений в БД.")

                for nd_data in notifications_to_send_push:
                    logger.info(f"[REQ_ID:{request_id}] Инициируем отправку push-уведомления для нового комментария к задаче {nd_data.issue_id}")
                    self.push_service.send_push_notification(nd_data)

            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"[REQ_ID:{request_id}] Ошибка SQLAlchemy при сохранении коммент-уведомлений: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"[REQ_ID:{request_id}] Непредвиденная ошибка при сохранении коммент-уведомлений или отправке push: {e}", exc_info=True)
        else:
            logger.info(f"[REQ_ID:{request_id}] Нет новых уникальных коммент-уведомлений для сохранения в БД.")

    def _delete_processed_status_notifications(self, connection, ids_to_delete: List[int], request_id: uuid.UUID):
        """Удаление обработанных уведомлений о статусах из MySQL по списку ID"""
        logger.info(f"[REQ_ID:{request_id}] _delete_processed_status_notifications: IDs {ids_to_delete}")
        if not ids_to_delete:
            return
        try:
            cursor = connection.cursor()
            # Создаем плейсхолдеры %s для каждого ID
            placeholders = ', '.join(['%s'] * len(ids_to_delete))
            query = f"""
                DELETE FROM u_its_update_status
                WHERE ID IN ({placeholders})
            """
            cursor.execute(query, tuple(ids_to_delete))
            connection.commit()
            logger.info(f"[REQ_ID:{request_id}] Удалено {cursor.rowcount} записей о статусах из MySQL (IDs: {ids_to_delete})")
            cursor.close()
        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Ошибка при удалении обработанных уведомлений о статусах (IDs: {ids_to_delete}): {e}", exc_info=True)
            # Важно: не откатывать транзакцию здесь, если она управляется выше по стеку,
            # но для DELETE это обычно атомарная операция для данного cursor.execute.

    def _delete_processed_comment_notifications(self, connection, ids_to_delete: List[int], request_id: uuid.UUID):
        """Удаление обработанных уведомлений о комментариях из MySQL по списку ID"""
        logger.info(f"[REQ_ID:{request_id}] _delete_processed_comment_notifications: IDs {ids_to_delete}")
        if not ids_to_delete:
            return
        try:
            cursor = connection.cursor()
            placeholders = ', '.join(['%s'] * len(ids_to_delete))
            query = f"""
                DELETE FROM u_its_add_notes
                WHERE ID IN ({placeholders})
            """
            cursor.execute(query, tuple(ids_to_delete))
            connection.commit()
            logger.info(f"[REQ_ID:{request_id}] Удалено {cursor.rowcount} записей о комментариях из MySQL (IDs: {ids_to_delete})")
            cursor.close()
        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Ошибка при удалении обработанных уведомлений о комментариях (IDs: {ids_to_delete}): {e}", exc_info=True)

    def get_user_notifications(self, user_id: int) -> Dict:
        """Получение всех уведомлений пользователя"""
        try:
            status_notifications = db.session.query(Notifications).filter_by(
                user_id=user_id
            ).order_by(Notifications.date_created.desc()).all()

            comment_notifications = db.session.query(NotificationsAddNotes).filter_by(
                user_id=user_id
            ).order_by(NotificationsAddNotes.date_created.desc()).all()

            return {
                'status_notifications': status_notifications,
                'comment_notifications': comment_notifications,
                'total_count': len(status_notifications) + len(comment_notifications)
            }

        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомлений пользователя {user_id}: {e}")
            return {'status_notifications': [], 'comment_notifications': [], 'total_count': 0}

    def clear_user_notifications(self, user_id: int) -> bool:
        """Очистка всех уведомлений пользователя"""
        try:
            # Удаляем уведомления о статусах
            db.session.query(Notifications).filter_by(user_id=user_id).delete()

            # Удаляем уведомления о комментариях
            db.session.query(NotificationsAddNotes).filter_by(user_id=user_id).delete()

            db.session.commit()
            logger.info(f"Очищены все уведомления для пользователя {user_id}")
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при очистке уведомлений пользователя {user_id}: {e}")
            return False

    def delete_notification(self, notification_id: int, notification_type: str, user_id: int) -> bool:
        """Удаление конкретного уведомления"""
        try:
            if notification_type == 'status':
                deleted = db.session.query(Notifications).filter(
                    and_(
                        Notifications.issue_id == notification_id,
                        Notifications.user_id == user_id
                    )
                ).delete()
            elif notification_type == 'comment':
                deleted = db.session.query(NotificationsAddNotes).filter(
                    and_(
                        NotificationsAddNotes.issue_id == notification_id,
                        NotificationsAddNotes.user_id == user_id
                    )
                ).delete()
            else:
                return False

            db.session.commit()
            logger.info(f"Удалено уведомление {notification_type}:{notification_id} для пользователя {user_id}")
            return deleted > 0

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при удалении уведомления {notification_type}:{notification_id}: {e}")
            return False


class BrowserPushService:
    """Сервис браузерных пуш-уведомлений"""

    def __init__(self):
        logger.info("[BrowserPushService] CONSTRUCTOR CALLED")
        # Не инициализируем VAPID ключи в конструкторе
        self.vapid_private_key = None
        self.vapid_public_key = None
        self.vapid_claims = None

    def _ensure_vapid_config(self):
        """Ленивая инициализация VAPID конфигурации"""
        logger.info("[VAPID_CONFIG_ENSURE] Вызов _ensure_vapid_config")
        if self.vapid_private_key is None or self.vapid_public_key is None:
            logger.info("[VAPID_CONFIG_ENSURE] Один из ключей (или оба) is None. Попытка инициализации.")
            try:
                from flask import current_app
                logger.info("[VAPID_CONFIG_ENSURE] Контекст приложения доступен.")

                # Получаем ключи из конфигурации
                config_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
                config_public_key = current_app.config.get('VAPID_PUBLIC_KEY')
                self.vapid_claims = current_app.config.get('VAPID_CLAIMS', {
                    "sub": "mailto:admin@tez-tour.com" # Дефолтное значение, если не найдено в конфиге
                })

                logger.info(f"[VAPID_CONFIG_ENSURE] Извлечено из current_app.config: "
                            f"Private Key Exists: {bool(config_private_key)} (первые 5 символов: {config_private_key[:5] if config_private_key else 'N/A'}), "
                            f"Public Key Exists: {bool(config_public_key)} (первые 5 символов: {config_public_key[:5] if config_public_key else 'N/A'})")
                logger.info(f"[VAPID_CONFIG_ENSURE] Claims из current_app.config: {self.vapid_claims}")


                if config_private_key and config_public_key:
                    logger.info("[VAPID_CONFIG_ENSURE] Ключи найдены в current_app.config. Используем их.")
                    self.vapid_private_key = config_private_key
                    self.vapid_public_key = config_public_key
                else:
                    logger.warning("[VAPID_CONFIG_ENSURE] Один или оба ключа отсутствуют в current_app.config. Попытка генерации НОВЫХ КЛЮЧЕЙ.")
                    try:
                        from py_vapid import Vapid
                        logger.info("[VAPID_CONFIG_ENSURE] py_vapid импортирован для генерации ключей.")

                        vapid = Vapid()
                        vapid.generate_keys()

                        private_key_gen = vapid.private_key.encode().decode('utf-8')
                        public_key_gen = vapid.public_key.encode().decode('utf-8')

                        logger.info(f"[VAPID_CONFIG_ENSURE] СГЕНЕРИРОВАНЫ новые VAPID ключи. "
                                    f"Private Key (первые 5): {private_key_gen[:5]}, Public Key (первые 5): {public_key_gen[:5]}")

                        self.vapid_private_key = private_key_gen
                        self.vapid_public_key = public_key_gen
                        # Claims остаются те, что были получены из config.get или дефолтные

                        # ВАЖНО: НЕ сохраняем сгенерированные ключи обратно в current_app.config здесь,
                        # так как это может привести к неожиданному поведению, если они должны были быть статичными.
                        # Если ключи генерируются, это признак проблемы с конфигурацией.
                        logger.warning("[VAPID_CONFIG_ENSURE] НОВЫЕ КЛЮЧИ БЫЛИ СГЕНЕРИРОВАНЫ И ИСПОЛЬЗУЮТСЯ В ЭТОМ ЭКЗЕМПЛЯРЕ СЕРВИСА. "
                                       "Это может привести к ошибкам 'MismatchSenderId', если подписки были созданы с другими ключами.")

                    except ImportError:
                        logger.error("[VAPID_CONFIG_ENSURE] Ошибка: py_vapid не найден, невозможно сгенерировать ключи.")
                        return False # Невозможно продолжить без ключей
                    except Exception as e_gen:
                        logger.error(f"[VAPID_CONFIG_ENSURE] Ошибка при генерации VAPID ключей: {e_gen}", exc_info=True)
                        return False # Невозможно продолжить при ошибке генерации

                # Логирование итоговых значений ключей (частично)
                logger.info(f"[VAPID_CONFIG_ENSURE] ПОСЛЕ ИНИЦИАЛИЗАЦИИ/ГЕНЕРАЦИИ: "
                            f"Private Key (первые 5): {self.vapid_private_key[:5] if self.vapid_private_key else 'None'}, "
                            f"Public Key (первые 5): {self.vapid_public_key[:5] if self.vapid_public_key else 'None'}")
                logger.info(f"[VAPID_CONFIG_ENSURE] Итоговые Claims: {self.vapid_claims}")

                # Возвращаем True, если все ключи успешно получены/сгенерированы
                result = bool(self.vapid_private_key and self.vapid_public_key and self.vapid_claims)
                logger.info(f"[VAPID_CONFIG_ENSURE] Итоговый результат проверки наличия ключей: {result}")
                return result

            except RuntimeError as e_runtime:
                logger.critical(f"[VAPID_CONFIG_ENSURE] КРИТИЧЕСКАЯ ОШИБКА: Нет контекста приложения Flask ('RuntimeError: Working outside of application context.') "
                                f"для получения VAPID конфигурации: {e_runtime}. Это основная причина проблем с ключами!", exc_info=True)
                # Вне контекста приложения мы не можем ни получить, ни сохранить ключи.
                # Это может быть проблемой для фоновых задач, если они не создают контекст.
                # В этом случае, ключи должны быть заданы через переменные окружения и загружены при старте.
                return False
            except Exception as e_unexpected:
                logger.error(f"[VAPID_CONFIG_ENSURE] Неожиданная ошибка при получении/генерации VAPID конфигурации: {e_unexpected}", exc_info=True)
                return False
        else:
            logger.info("[VAPID_CONFIG_ENSURE] VAPID ключи уже были инициализированы ранее в этом экземпляре BrowserPushService.")
            # Если ключи уже инициализированы, просто проверяем их наличие и логируем
            logger.info(f"[VAPID_CONFIG_ENSURE] Ранее инициализированные ключи: "
                        f"Private Key (первые 5): {self.vapid_private_key[:5] if self.vapid_private_key else 'None'}, "
                        f"Public Key (первые 5): {self.vapid_public_key[:5] if self.vapid_public_key else 'None'}")
            logger.info(f"[VAPID_CONFIG_ENSURE] Ранее инициализированные Claims: {self.vapid_claims}")
            result = bool(self.vapid_private_key and self.vapid_public_key and self.vapid_claims)
            logger.info(f"[VAPID_CONFIG_ENSURE] Повторная проверка ранее инициализированных ключей: {result}")
            return result

    def send_push_notification(self, notification: NotificationData):
        """Отправка push-уведомления на все активные подписки пользователя"""
        # Немедленно вызовем ошибку, чтобы проверить, выполняется ли этот код
        # raise ValueError("[!!!SURELY_EXECUTED!!!] Тестовая ошибка из send_push_notification для проверки обновления кода.")

        # Остальной код метода оставляем как есть, но он не должен выполниться, если ошибка сработает
        logger.info(f"[!!!SEND_PUSH_ENTRY!!!] Вызван send_push_notification для пользователя {notification.user_id}, тип: {notification.notification_type.value}")

        if not WEBPUSH_AVAILABLE:
            logger.warning(f"[PUSH_SERVICE] Библиотека pywebpush недоступна. Пропускаем push для пользователя {notification.user_id}")
            return {'status': 'service_unavailable', 'message': 'pywebpush не доступна', 'results': []}

        logger.info("[PUSH_SERVICE] Проверка VAPID конфигурации...")
        if not self._ensure_vapid_config():
            logger.error("[PUSH_SERVICE] VAPID конфигурация неполная. Невозможно отправить push-уведомления.")
            return {'status': 'config_error', 'message': 'VAPID конфигурация неполная', 'results': []}
        logger.info("[PUSH_SERVICE] VAPID конфигурация в порядке.")

        logger.info(f"[PUSH_SERVICE] Получение активных подписок для пользователя {notification.user_id}...")
        user_subscriptions = self._get_user_subscriptions(notification.user_id)

        if not user_subscriptions:
            logger.info(f"[PUSH_SERVICE] Для пользователя {notification.user_id} не найдено активных подписок.")
            return {'status': 'no_subscriptions', 'message': 'Нет активных подписок', 'results': []}

        logger.info(f"[PUSH_SERVICE] Найдено {len(user_subscriptions)} активных подписок для пользователя {notification.user_id}.")
        total_subscriptions = len(user_subscriptions)

        # Формируем данные для Service Worker
        # Определяем иконку: сначала из data, потом дефолтная
        icon_url = None
        if notification.data and 'icon' in notification.data:
            icon_url = notification.data['icon']

        if not icon_url:
            # Генерируем абсолютный URL иконки
            try:
                from flask import url_for
                icon_url = url_for('static', filename='img/push-icon.png', _external=True)
            except Exception as e:
                logger.warning(f"[PUSH_SERVICE] Не удалось сгенерировать URL иконки: {e}")
                icon_url = '/static/img/push-icon.png'  # Относительный URL как запасной вариант

        # Формируем URL для клика по уведомлению
        action_url = '/'
        if notification.data and 'url' in notification.data:
            action_url = notification.data['url']
        elif notification.issue_id:
            try:
                from flask import url_for
                action_url = url_for('main.issue', issue_id=notification.issue_id, _external=True)
            except Exception:
                action_url = f'/my-issues/{notification.issue_id}'

        # Создаем дополнительные данные для Service Worker
        additional_data = {
            'issue_id': notification.issue_id,
            'notification_type': notification.notification_type.value,
            'url': action_url,
            'icon': icon_url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'soundUrl': '/static/sounds/notification.mp3'  # URL для звука уведомления
        }

        # Если у уведомления есть дополнительные данные, добавляем их
        if notification.data:
            # Избегаем перезаписи наших ключей
            for key, value in notification.data.items():
                if key not in ['issue_id', 'notification_type', 'url', 'icon', 'timestamp', 'soundUrl']:
                    additional_data[key] = value

        # Формируем финальный payload для Service Worker
        payload = {
            'title': notification.title,
            'message': notification.message,
            'icon': icon_url,
            'data': additional_data
        }
        logger.info(f"[PUSH_SERVICE] Сформирован основной payload: title='{payload['title']}', message='{payload['message']}', icon='{payload['icon']}'")
        logger.debug(f"[PUSH_SERVICE] Полные данные в payload.data: {additional_data}")

        # Преобразуем в JSON строку с поддержкой кириллицы
        try:
            payload_json_string = json.dumps(payload, ensure_ascii=False)
            logger.info(f"[PUSH_SERVICE] Сформирован payload JSON (первые 200 символов): {payload_json_string[:200]}...")
        except Exception as json_error:
            logger.error(f"[PUSH_SERVICE] Ошибка при создании JSON для payload: {json_error}", exc_info=True)
            return {'status': 'payload_error', 'message': f'Ошибка JSON: {json_error}', 'results': []}

        # Отправляем уведомления
        success_count = 0
        failure_count = 0
        results = []

        logger.info(f"[PUSH_SERVICE] Начало цикла отправки по {total_subscriptions} подпискам для пользователя {notification.user_id}")
        for i, subscription in enumerate(user_subscriptions):
            logger.info(f"[PUSH_SERVICE] Итерация {i+1}/{total_subscriptions}. Попытка отправки на подписку ID {subscription.id} (Endpoint: {subscription.endpoint[:50]}...)")
            try:
                self._send_to_subscription(subscription, payload_json_string)
                logger.info(f"[PUSH_SEND] Уведомление (предположительно) успешно отправлено на endpoint ID {subscription.id} для пользователя {notification.user_id}")
                results.append({'subscription_id': subscription.id, 'status': 'success'})
                success_count += 1
                # Обновляем время последнего использования подписки
                subscription.last_used = datetime.now(timezone.utc)
            except WebPushException as e:
                logger.error(f"[PUSH_SEND] WebPushException при отправке на endpoint ID {subscription.id} для пользователя {notification.user_id}: {e}", exc_info=True)
                response_status = None
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"WebPushException response status: {e.response.status_code}")
                    logger.error(f"WebPushException response text: {e.response.text}")
                    response_status = e.response.status_code
                else:
                    logger.error("WebPushException не содержит атрибута 'response' или e.response is None.")

                # Деактивируем подписку при определенных ошибках
                if response_status in [403, 404, 410]: # 403 (Forbidden - VAPID mismatch), 404 (Not Found), 410 (Gone)
                    logger.warning(f"Подписка ID {subscription.id} вернула статус {response_status}. Деактивируем ее.")
                    try:
                        self._deactivate_subscription(subscription.id)
                    except Exception as de_err:
                        logger.error(f"Ошибка при попытке деактивировать подписку ID {subscription.id}: {de_err}", exc_info=True)

                results.append({'subscription_id': subscription.id, 'status': 'failed', 'error': str(e)})
                failure_count += 1
            except Exception as e:
                logger.error(f"[PUSH_SEND] Непредвиденная ошибка при отправке на endpoint ID {subscription.id} для пользователя {notification.user_id}: {e}", exc_info=True)
                results.append({'subscription_id': subscription.id, 'status': 'failed', 'error': 'Непредвиденная ошибка'})
                failure_count += 1
        logger.info(f"[PUSH_SERVICE] Завершение цикла отправки. Успешно: {success_count}, Неудачно: {failure_count} из {total_subscriptions} для пользователя {notification.user_id}.")

        # Сохраняем обновления в БД (например, last_used)
        if success_count > 0 or failure_count > 0: # Если были какие-либо попытки
            try:
                db.session.commit()
            except Exception as db_error:
                logger.error(f"[PUSH_SERVICE] Ошибка сохранения изменений в БД: {db_error}")
                db.session.rollback()

        if failure_count == total_subscriptions and total_subscriptions > 0:
            logger.warning(f"[PUSH_SERVICE] Не удалось отправить уведомление ни на одну из {total_subscriptions} подписок для пользователя {notification.user_id}.")
            return {'status': 'all_failed', 'message': f'Не удалось отправить уведомление ни на одну из {total_subscriptions} подписок.', 'results': results}
        elif failure_count > 0:
            logger.warning(f"[PUSH_SERVICE] Частичный сбой отправки для пользователя {notification.user_id}. Успешно: {success_count}, Неудачно: {failure_count}.")
            return {'status': 'partial_failure', 'message': f'Успешно: {success_count}, Неудачно: {failure_count}.', 'results': results}
        elif success_count == total_subscriptions and total_subscriptions > 0:
            logger.info(f"[PUSH_SERVICE] Все {success_count} уведомлений успешно отправлены для пользователя {notification.user_id}.")
            return {'status': 'success', 'message': f'Все {success_count} уведомлений успешно отправлены.', 'results': results}
        elif total_subscriptions == 0: # Этот случай уже обработан выше, но для полноты
            logger.info(f"[PUSH_SERVICE] Нет активных подписок для отправки пользователю {notification.user_id} (повторная проверка).")
            return {'status': 'no_subscriptions', 'message': 'Нет активных подписок для отправки.', 'results': []}
        else: # Неожиданный случай, например, если total_subscriptions < 0 или другая логическая ошибка
            logger.error(f"[PUSH_SERVICE] Неожиданное состояние счетчиков для пользователя {notification.user_id}: success={success_count}, failure={failure_count}, total={total_subscriptions}")
            return {'status': 'unknown_error', 'message': 'Неизвестное состояние после отправки', 'results': results}

    def _get_user_subscriptions(self, user_id: int) -> List[PushSubscription]:
        """Получение активных подписок пользователя из базы данных"""
        try:
            subscriptions = db.session.query(PushSubscription).filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            return subscriptions

        except Exception as e:
            logger.error(f"Ошибка при получении подписок пользователя {user_id}: {e}")
            return []

    def _send_to_subscription(self, subscription: PushSubscription, payload_json_string: str):
        """Отправка уведомления конкретной подписке"""
        logger.critical(f"[!!!DEBUG_SEND_SUB_ENTRY!!!] Вызван _send_to_subscription для подписки ID {subscription.id}") # Очень заметный лог

        try:
            # Проверка критических условий
            if not WEBPUSH_AVAILABLE:
                logger.error("pywebpush не доступен")
                raise WebPushException("pywebpush не доступен")

            if not subscription or not subscription.endpoint or not subscription.p256dh_key or not subscription.auth_key:
                logger.error(f"Некорректная подписка ID {subscription.id if subscription else 'None'}")
                raise WebPushException(f"Некорректная подписка ID {subscription.id if subscription else 'None'}")

            # Получаем необходимые VAPID данные
            if not self._ensure_vapid_config():
                logger.error("Не удалось получить VAPID конфигурацию")
                raise WebPushException("Не удалось получить VAPID конфигурацию")

            # Адаптация endpoint для FCM, если необходимо
            endpoint_to_use = subscription.endpoint
            if endpoint_to_use.startswith("https://fcm.googleapis.com/fcm/send/"):
                new_endpoint = endpoint_to_use.replace("https://fcm.googleapis.com/fcm/send/", "https://fcm.googleapis.com/wp/")
                logger.info(f"[PUSH_ADAPT] Адаптирован FCM endpoint для подписки ID {subscription.id}: с {endpoint_to_use} на {new_endpoint}")
                endpoint_to_use = new_endpoint
            else:
                logger.info(f"[PUSH_ADAPT] Endpoint для подписки ID {subscription.id} не требует адаптации: {endpoint_to_use}")

            # Формируем данные подписки
            subscription_info = {
                "endpoint": endpoint_to_use,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key
                }
            }

            # Отправляем уведомление напрямую
            logger.info(f"Отправка push-уведомления на endpoint: {endpoint_to_use[:50]}...")
            logger.info(f"[DEBUG_SEND_SUB] Подписка ID {subscription.id}: Endpoint для webpush: {subscription_info.get('endpoint')}")
            logger.info(f"[DEBUG_SEND_SUB] Подписка ID {subscription.id}: VAPID Private Key (начало): {self.vapid_private_key[:20] if self.vapid_private_key else 'None'}")
            logger.info(f"[DEBUG_SEND_SUB] Подписка ID {subscription.id}: VAPID Claims: {self.vapid_claims}")
            logger.debug(f"[DEBUG_SEND_SUB] Подписка ID {subscription.id}: Payload JSON: {payload_json_string[:250]}...")

            webpush(
                subscription_info=subscription_info,
                data=payload_json_string,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
                headers={"TTL": "60"}
            )
            logger.critical(f"[!!!DEBUG_SEND_SUB_EXIT_SUCCESS!!!] webpush вызван УСПЕШНО для подписки ID {subscription.id}")

        except WebPushException as e:
            logger.error(f"WebPushException при отправке на подписку {subscription.id} (endpoint: {subscription.endpoint[:50]}...): {str(e)}", exc_info=True)
            response_status = None
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"WebPushException response status: {e.response.status_code}")
                logger.error(f"WebPushException response text: {e.response.text}")
                response_status = e.response.status_code
            else:
                logger.error("WebPushException не содержит атрибута 'response' или e.response is None.")

            if response_status in [403, 404, 410]:
                logger.warning(f"Подписка ID {subscription.id} вернула статус {response_status}. Деактивируем ее.")
                try:
                    self._deactivate_subscription(subscription.id)
                except Exception as de_err:
                    logger.error(f"Ошибка при попытке деактивировать подписку ID {subscription.id}: {de_err}", exc_info=True)

            raise
        except Exception as e:
            logger.error(f"Ошибка при отправке push-уведомления на подписку {subscription.id} (endpoint: {subscription.endpoint[:50]}...): {str(e)}", exc_info=True)
            raise WebPushException(f"Неожиданная ошибка при отправке: {str(e)}")

    def _deactivate_subscription(self, subscription_id: int):
        """Помечает подписку как неактивную в базе данных."""
        try:
            sub_to_deactivate = PushSubscription.query.get(subscription_id)
            if sub_to_deactivate:
                sub_to_deactivate.is_active = False
                db.session.commit()
                logger.info(f"[DB_UPDATE] Подписка ID {subscription_id} помечена как неактивная.")
            else:
                logger.warning(f"[DB_UPDATE] Попытка деактивировать несуществующую подписку ID {subscription_id}.")
        except Exception as e:
            logger.error(f"[DB_UPDATE] Ошибка при деактивации подписки ID {subscription_id}: {e}", exc_info=True)
            db.session.rollback()


# Глобальный экземпляр сервиса (ленивая инициализация)
_notification_service = None

def get_notification_service():
    """Получение экземпляра сервиса уведомлений с ленивой инициализацией"""
    global _notification_service
    logger.info("[get_notification_service] CALLED")
    if _notification_service is None:
        logger.info("[get_notification_service] _notification_service IS NONE, CREATING NEW INSTANCE")
        _notification_service = NotificationService()
    logger.info(f"[get_notification_service] RETURNING: {type(_notification_service)}")
    return _notification_service

# Создаем объект с ленивой инициализацией
class LazyNotificationService:
    def __init__(self):
        logger.info("[LazyNotificationService] CONSTRUCTOR CALLED")

    def __getattr__(self, name):
        logger.info(f"[LazyNotificationService] GETATTR CALLED FOR: {name}")
        service = get_notification_service()
        if name == 'push_service':
            logger.info(f"[LazyNotificationService] Accessing push_service, type: {type(service.push_service)}")
            return service.push_service
        return getattr(service, name)

notification_service = LazyNotificationService()


def check_notifications_improved(user_email: str, user_id: int) -> int:
    """
    Улучшенная функция проверки уведомлений

    Args:
        user_email: Email пользователя
        user_id: ID пользователя

    Returns:
        int: Количество обработанных уведомлений
    """
    return get_notification_service().process_notifications(user_email, user_id)
