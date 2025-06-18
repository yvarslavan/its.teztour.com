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
    source_id: Optional[int] = None

    def to_dict(self) -> Dict:
        """Преобразование в словарь для JSON"""
        return {
            'user_id': self.user_id,
            'issue_id': self.issue_id,
            'type': self.notification_type.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'source_id': self.source_id
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
        logger.info(f"[REQ_ID:{request_id}] _process_status_notifications для user_id={user_id}, user_email={user_email}")
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            query = """
                SELECT ID, IssueID, OldStatus, NewStatus, OldSubj, Body, RowDateCreated, Author
                FROM u_its_update_status
                WHERE LOWER(Author) = LOWER(%s)
                ORDER BY RowDateCreated DESC
                LIMIT 50
            """

            logger.info(f"[REQ_ID:{request_id}] MySQL Query (status): {query} с user_email: {user_email}")
            cursor.execute(query, (user_email,))
            rows = cursor.fetchall()
            source_ids = [row['ID'] for row in rows]
            logger.info(f"[REQ_ID:{request_id}] Получено {len(rows)} строк из u_its_update_status. IDs: {source_ids}")

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
        logger.info(f"[REQ_ID:{request_id}] _process_comment_notifications для user_id={user_id}, user_email={user_email}")
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            query = """
                SELECT ID, issue_id, Author, notes, date_created, RowDateCreated
                FROM u_its_add_notes
                WHERE LOWER(Author) = LOWER(%s)
                ORDER BY RowDateCreated DESC
                LIMIT 50
            """

            logger.info(f"[REQ_ID:{request_id}] MySQL Query (comment): {query} с user_email: {user_email}")
            cursor.execute(query, (user_email,))
            rows = cursor.fetchall()
            source_ids = [row['ID'] for row in rows]
            logger.info(f"[REQ_ID:{request_id}] Получено {len(rows)} строк из u_its_add_notes. IDs: {source_ids}")

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
                    created_at=row['date_created'],
                    source_id=row['ID']
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
        """Сохранение уведомлений об изменении статуса в базу данных"""
        logger.info(f"[REQ_ID:{request_id}] _save_status_notifications: {len(notifications)} уведомлений")
        saved_count = 0
        newly_created_notifications_for_push = []

        if not notifications:
            logger.info(f"[REQ_ID:{request_id}] Нет статус-уведомлений для сохранения.")
            return

        try:
            for notification_data in notifications:
                try:
                    existing_notification = Notifications.query.filter_by(
                        user_id=notification_data.user_id,
                        issue_id=notification_data.issue_id,
                        old_status=notification_data.data.get('old_status'),
                        new_status=notification_data.data.get('new_status'),
                        old_subj=notification_data.data.get('subject'),
                        date_created=notification_data.created_at
                    ).first()

                    if existing_notification:
                        logger.info(f"[REQ_ID:{request_id}] Статус-уведомление уже существует (ID: {existing_notification.id}). Пропуск.")
                        continue

                    new_notification_db = Notifications(
                        user_id=notification_data.user_id,
                        issue_id=notification_data.issue_id,
                        old_status=notification_data.data.get('old_status'),
                        new_status=notification_data.data.get('new_status'),
                        old_subj=notification_data.data.get('subject'),
                        date_created=notification_data.created_at
                    )
                    db.session.add(new_notification_db)
                    db.session.flush() # Для получения ID до коммита, если нужно
                    logger.info(f"[REQ_ID:{request_id}] Подготовлено к сохранению новое статус-уведомление (DB ID: {new_notification_db.id})")
                    newly_created_notifications_for_push.append(notification_data)
                    saved_count += 1

                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"[REQ_ID:{request_id}] Ошибка SQLAlchemy при сохранении статус-уведомления: {e}", exc_info=True)
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"[REQ_ID:{request_id}] Непредвиденная ошибка при подготовке статус-уведомления: {e}", exc_info=True)
                    continue

            if saved_count > 0:
                db.session.commit()
                logger.info(f"[REQ_ID:{request_id}] Успешно сохранено {saved_count} новых статус-уведомлений.")
            else:
                logger.info(f"[REQ_ID:{request_id}] Нет новых уникальных статус-уведомлений для сохранения.")

        except RuntimeError as e:
            if "Working outside of application context" in str(e):
                logger.error(f"[REQ_ID:{request_id}] КРИТИЧЕСКАЯ ОШИБКА КОНТЕКСТА в _save_status_notifications: {e}", exc_info=True)
            else:
                logger.error(f"[REQ_ID:{request_id}] Непредвиденная RuntimeError в _save_status_notifications: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Общая ошибка в _save_status_notifications: {e}", exc_info=True)
            try: db.session.rollback()
            except: pass

        if newly_created_notifications_for_push:
            logger.info(f"[REQ_ID:{request_id}] Отправка {len(newly_created_notifications_for_push)} PUSH о статусах.")
            for notification_data_to_push in newly_created_notifications_for_push:
                self.push_service.send_push_notification(notification_data_to_push)
        else:
            logger.info(f"[REQ_ID:{request_id}] Нет статус-уведомлений для PUSH.")

    def _save_comment_notifications(self, notifications: List[NotificationData], request_id: uuid.UUID):
        """Сохранение уведомлений о комментариях в базу данных"""
        logger.info(f"[REQ_ID:{request_id}] _save_comment_notifications: {len(notifications)} уведомлений")
        saved_count = 0
        newly_created_notifications_for_push = []

        if not notifications:
            logger.info(f"[REQ_ID:{request_id}] Нет коммент-уведомлений для сохранения.")
            return

        try:
            for notification_data in notifications:
                try:
                    existing_notification = NotificationsAddNotes.query.filter_by(
                        user_id=notification_data.user_id,
                        issue_id=notification_data.issue_id,
                        notes=notification_data.message,
                        author=notification_data.data.get('author'),
                        date_created=notification_data.created_at
                    ).first()

                    if existing_notification:
                        logger.info(f"[REQ_ID:{request_id}] Коммент-уведомление уже существует (ID: {existing_notification.id}). Пропуск.")
                        continue

                    new_notification_db = NotificationsAddNotes(
                        user_id=notification_data.user_id,
                        issue_id=notification_data.issue_id,
                        author=notification_data.data.get('author'),
                        notes=notification_data.message,
                        date_created=notification_data.created_at,
                        source_id=notification_data.source_id
                    )
                    db.session.add(new_notification_db)
                    db.session.flush() # Для получения ID до коммита
                    logger.info(f"[REQ_ID:{request_id}] Подготовлено к сохранению новое коммент-уведомление (DB ID: {new_notification_db.id})")
                    newly_created_notifications_for_push.append(notification_data)
                    saved_count += 1

                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"[REQ_ID:{request_id}] Ошибка SQLAlchemy при сохранении коммент-уведомления: {e}", exc_info=True)
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"[REQ_ID:{request_id}] Непредвиденная ошибка при подготовке коммент-уведомления: {e}", exc_info=True)
                    continue

            if saved_count > 0:
                db.session.commit()
                logger.info(f"[REQ_ID:{request_id}] Успешно сохранено {saved_count} новых коммент-уведомлений.")
            else:
                logger.info(f"[REQ_ID:{request_id}] Нет новых уникальных коммент-уведомлений для сохранения.")

        except RuntimeError as e:
            if "Working outside of application context" in str(e):
                logger.error(f"[REQ_ID:{request_id}] КРИТИЧЕСКАЯ ОШИБКА КОНТЕКСТА в _save_comment_notifications: {e}", exc_info=True)
            else:
                logger.error(f"[REQ_ID:{request_id}] Непредвиденная RuntimeError в _save_comment_notifications: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"[REQ_ID:{request_id}] Общая ошибка в _save_comment_notifications: {e}", exc_info=True)
            try: db.session.rollback()
            except: pass

        if newly_created_notifications_for_push:
            logger.info(f"[REQ_ID:{request_id}] Отправка {len(newly_created_notifications_for_push)} PUSH о комментариях.")
            for notification_data_to_push in newly_created_notifications_for_push:
                self.push_service.send_push_notification(notification_data_to_push)
        else:
            logger.info(f"[REQ_ID:{request_id}] Нет коммент-уведомлений для PUSH.")

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

            # Преобразуем SQLAlchemy объекты в словари для JSON сериализации
            status_data = []
            for notification in status_notifications:
                status_data.append({
                    'id': notification.id,
                    'issue_id': notification.issue_id,
                    'old_status': notification.old_status,
                    'new_status': notification.new_status,
                    'date_created': notification.date_created.isoformat() if notification.date_created else None,
                    'user_id': notification.user_id
                })

            comment_data = []
            for notification in comment_notifications:
                comment_data.append({
                    'id': notification.id,
                    'issue_id': notification.issue_id,
                    'author': notification.author,
                    'notes': notification.notes,
                    'date_created': notification.date_created.isoformat() if notification.date_created else None,
                    'user_id': notification.user_id
                })

            return {
                'status_notifications': status_data,
                'comment_notifications': comment_data,
                'total_count': len(status_data) + len(comment_data)
            }

        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомлений пользователя {user_id}: {e}")
            return {'status_notifications': [], 'comment_notifications': [], 'total_count': 0}
        except Exception as e:
            logger.error(f"Общая ошибка при получении уведомлений пользователя {user_id}: {e}")
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
        # Инициализируем VAPID ключи сразу в конструкторе
        self.vapid_private_key = None
        self.vapid_public_key = None
        self.vapid_claims = None

        # Попытаемся загрузить VAPID ключи сразу при инициализации
        try:
            # Проверяем наличие контекста приложения более безопасным способом
            from flask import has_app_context
            if has_app_context():
                self._ensure_vapid_config()
                logger.info("[BrowserPushService] VAPID ключи загружены при инициализации")
            else:
                logger.info("[BrowserPushService] Контекст приложения недоступен при инициализации")
        except RuntimeError as e:
            # Контекст приложения может быть недоступен при инициализации
            logger.info(f"[BrowserPushService] VAPID ключи будут загружены позже: {e}")
        except Exception as e:
            logger.warning(f"[BrowserPushService] Не удалось загрузить VAPID ключи при инициализации: {e}")

    def _ensure_vapid_config(self):
        """
        Гарантирует, что VAPID ключи загружены из конфигурации или сгенерированы.
        Возвращает True, если конфигурация VAPID в порядке, иначе False.
        """
        log_prefix = "[VAPID_CONFIG_ENSURE]"
        logger.info(f"{log_prefix} Вызов _ensure_vapid_config")

        if self.vapid_public_key and self.vapid_private_key:
            logger.info(f"{log_prefix} VAPID ключи уже инициализированы в экземпляре.")
            return True

        try:
            # Сначала пытаемся загрузить ключи напрямую из файла vapid_keys.py
            try:
                from blog.config.vapid_keys import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS

                if VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY:
                    logger.info(f"{log_prefix} VAPID ключи успешно загружены из blog.config.vapid_keys")
                    self.vapid_public_key = VAPID_PUBLIC_KEY
                    self.vapid_private_key = VAPID_PRIVATE_KEY
                    self.vapid_claims = VAPID_CLAIMS or {"sub": "mailto:admin@example.com"}

                    # Обновляем конфигурацию Flask для совместимости
                    current_app.config['VAPID_PUBLIC_KEY'] = VAPID_PUBLIC_KEY
                    current_app.config['VAPID_PRIVATE_KEY'] = VAPID_PRIVATE_KEY
                    current_app.config['VAPID_CLAIMS'] = self.vapid_claims

                    logger.info(f"{log_prefix} Firebase VAPID ключи установлены из файла")
                    return True
                else:
                    logger.warning(f"{log_prefix} VAPID ключи пусты в blog.config.vapid_keys")
            except ImportError as e:
                logger.warning(f"{log_prefix} Не удалось импортировать blog.config.vapid_keys: {e}")

            # Если не удалось загрузить из файла, пробуем из конфигурации Flask
            config_public_key = current_app.config.get('VAPID_PUBLIC_KEY')
            config_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            # vapid_claims должен быть здесь, внутри with current_app.app_context()
            if not hasattr(self, 'vapid_claims') or not self.vapid_claims:
                self.vapid_claims = current_app.config.get(
                    'VAPID_CLAIMS',
                    {"sub": "mailto:admin@example.com"}
                )
                logger.info(f"{log_prefix} VAPID_CLAIMS установлен: {self.vapid_claims}")

            if config_public_key and config_private_key:
                logger.info(f"{log_prefix} VAPID ключи получены из конфигурации Flask.")
                self.vapid_public_key = config_public_key
                self.vapid_private_key = config_private_key
                # Убедимся что vapid_claims установлен, если ключи из конфига
                if not self.vapid_claims:
                    self.vapid_claims = current_app.config.get(
                        'VAPID_CLAIMS',
                        {"sub": "mailto:admin@example.com"}
                    )
                    logger.info(f"{log_prefix} VAPID_CLAIMS (повторно для случая ключей из конфига): {self.vapid_claims}")
                return True
            else:
                logger.error(f"{log_prefix} VAPID ключи НЕ НАЙДЕНЫ в конфигурации Flask!")
                logger.error(f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Необходимо настроить Firebase VAPID ключи!")
                logger.error(f"{log_prefix} Инструкция:")
                logger.error(f"{log_prefix} 1. Перейдите в Firebase Console -> Project Settings -> Cloud Messaging")
                logger.error(f"{log_prefix} 2. Создайте новую пару Web Push certificates")
                logger.error(f"{log_prefix} 3. Обновите blog/config/vapid_keys.py обоими ключами")
                logger.error(f"{log_prefix} 4. Перезапустите Flask приложение")
                return False
        except RuntimeError as e:
            if "Working outside of application context" in str(e):
                logger.critical(
                    f"{log_prefix} КРИТИЧЕСКАЯ ОШИБКА: Нет контекста приложения Flask ('{e}') для VAPID.",
                    exc_info=True
                )
            else:
                logger.error(f"{log_prefix} Непредвиденная RuntimeError для VAPID: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"{log_prefix} Общая ошибка VAPID: {e}", exc_info=True)
            return False

    def force_reload_vapid_config(self):
        """Принудительная перезагрузка VAPID ключей"""
        logger.info("[FORCE_RELOAD_VAPID] Принудительная перезагрузка VAPID ключей")
        self.vapid_private_key = None
        self.vapid_public_key = None
        self.vapid_claims = None
        return self._ensure_vapid_config()

    def send_push_notification(self, notification: NotificationData, claims: Optional[Dict] = None):
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
                self._send_to_subscription(subscription, payload_json_string, claims=claims)
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
        """Получение активных подписок пользователя из БД"""
        try:
            return PushSubscription.query.filter_by(user_id=user_id, is_active=True).all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка БД при получении подписок для пользователя {user_id}: {e}", exc_info=True)
            return []

    def _send_to_subscription(self, subscription: PushSubscription, payload_json_string: str, claims: Optional[Dict] = None):
        request_id = uuid.uuid4() # Для трассировки этого конкретного вызова
        logger.critical(f"[!!!DEBUG_SEND_SUB_ENTRY!!!] REQ_ID: {request_id} Вызван _send_to_subscription для подписки ID {subscription.id}")

        if not self._ensure_vapid_config():
            logger.error(f"[REQ_ID:{request_id}] [PUSH_SEND_SUB] VAPID ключи не настроены. Отправка на подписку ID {subscription.id} отменена.")
            # Вместо возврата словаря, который будет проигнорирован, вызываем исключение
            raise WebPushException(f"VAPID keys not configured for subscription ID {subscription.id}")

        # Умная адаптация endpoint
        original_endpoint = subscription.endpoint

        if not original_endpoint:
            logger.error(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Пустой endpoint для подписки ID {subscription.id}. Отправка невозможна.")
            raise WebPushException(f"Пустой endpoint для подписки ID {subscription.id}")

        # Логируем исходный endpoint
        logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Исходный endpoint для подписки ID {subscription.id}: '{original_endpoint[:70]}...'")

        # Начинаем адаптацию endpoint
        endpoint_to_use = original_endpoint

        # 1. Проверяем наличие https:// и добавляем, если отсутствует
        if "fcm.googleapis.com" in endpoint_to_use and not endpoint_to_use.startswith("https://"):
            endpoint_to_use = f"https://{endpoint_to_use}"
            logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Добавлен протокол https://: '{endpoint_to_use[:70]}...'")

        # 2. Адаптируем старый формат FCM URL
        if "fcm.googleapis.com/fcm/send/" in endpoint_to_use:
            token = endpoint_to_use.split("/fcm/send/")[1]
            endpoint_to_use = f"https://fcm.googleapis.com/wp/{token}"
            logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Старый формат преобразован в новый: '{endpoint_to_use[:70]}...'")

        # 3. Проверяем наличие /wp/ для FCM и добавляем, если отсутствует
        if "fcm.googleapis.com" in endpoint_to_use and "/wp/" not in endpoint_to_use:
            # Делим URL на части и берем последнюю часть как токен
            parts = endpoint_to_use.split("/")
            if len(parts) > 0:
                token = parts[-1]
                # Если токен не пустой, формируем новый URL
                if token:
                    endpoint_to_use = f"https://fcm.googleapis.com/wp/{token}"
                    logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Добавлен префикс /wp/: '{endpoint_to_use[:70]}...'")

        # Если endpoint был изменен, логируем это
        if endpoint_to_use != original_endpoint:
            logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Endpoint адаптирован с '{original_endpoint[:50]}...' на '{endpoint_to_use[:50]}...'")

            # Проверяем наличие токена после /wp/ для FCM
            if "fcm.googleapis.com/wp/" in endpoint_to_use:
                token_parts = endpoint_to_use.split("/wp/")
                if len(token_parts) > 1 and not token_parts[1]:
                    logger.error(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Отсутствует токен после /wp/ в адаптированном URL: '{endpoint_to_use}'")
                    raise WebPushException(f"Некорректный FCM endpoint: отсутствует токен после /wp/")
        else:
            logger.info(f"[REQ_ID:{request_id}] [ADAPT_ENDPOINT_SEND_SUB] Endpoint не требует адаптации: '{endpoint_to_use[:70]}...'")

        # Определяем, какие VAPID claims использовать
        if claims:
            claims_to_use = claims
            logger.info(f"[REQ_ID:{request_id}] [DEBUG_SEND_SUB] Используются VAPID claims, переданные в функцию: {claims_to_use}")
        else:
            claims_to_use = self.vapid_claims
            logger.info(f"[REQ_ID:{request_id}] [DEBUG_SEND_SUB] Используются VAPID claims из экземпляра сервиса: {claims_to_use}")

        sub_info = {
            "endpoint": endpoint_to_use,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }

        # Отладочный лог перед самой отправкой
        logger.info(f"[REQ_ID:{request_id}] [DEBUG_SEND_SUB] Подписка ID {subscription.id}: Endpoint для webpush: {endpoint_to_use}")
        logger.info(f"[REQ_ID:{request_id}] [DEBUG_SEND_SUB] Подписка ID {subscription.id}: VAPID Private Key (начало): {self.vapid_private_key[:20] if self.vapid_private_key else 'NOT SET'}")
        logger.info(f"[REQ_ID:{request_id}] [DEBUG_SEND_SUB] Подписка ID {subscription.id}: VAPID Claims для отправки: {claims_to_use}")

        try:
            webpush(
                subscription_info=sub_info,
                data=payload_json_string,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=claims_to_use.copy() # Используем claims_to_use
            )
            logger.info(f"[REQ_ID:{request_id}] [SEND_SUCCESS] webpush() вызов успешен для подписки ID {subscription.id}")

            # Если endpoint был адаптирован успешно, обновляем его в базе данных
            if endpoint_to_use != original_endpoint:
                try:
                    subscription_db = PushSubscription.query.get(subscription.id)
                    if subscription_db:
                        logger.info(f"[REQ_ID:{request_id}] [ENDPOINT_UPDATE] Обновляем endpoint в БД для подписки ID {subscription.id}")
                        subscription_db.endpoint = endpoint_to_use
                        db.session.commit()
                        logger.info(f"[REQ_ID:{request_id}] [ENDPOINT_UPDATE] Успешно обновлен endpoint в БД")
                except Exception as db_err:
                    logger.error(f"[REQ_ID:{request_id}] [ENDPOINT_UPDATE] Ошибка обновления endpoint в БД: {db_err}", exc_info=True)

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

    def send_test_push(self, notification: NotificationData, claims: Dict):
        """Специализированная функция для отправки тестового уведомления с явными claims."""
        logger.info(f"[PUSH_SERVICE_TEST] Вызвана send_test_push для пользователя {notification.user_id} с claims: {claims}")

        if not WEBPUSH_AVAILABLE:
            logger.warning(f"[PUSH_SERVICE_TEST] pywebpush недоступна, отправка невозможна.")
            return {'status': 'service_unavailable', 'message': 'pywebpush не доступна'}

        if not self._ensure_vapid_config():
            logger.error("[PUSH_SERVICE_TEST] VAPID конфигурация неполная.")
            return {'status': 'config_error', 'message': 'VAPID конфигурация неполная'}

        user_subscriptions = self._get_user_subscriptions(notification.user_id)
        if not user_subscriptions:
            logger.info(f"[PUSH_SERVICE_TEST] Для пользователя {notification.user_id} не найдено активных подписок.")
            return {'status': 'no_subscriptions', 'message': 'Нет активных подписок'}

        # Детальное логирование подписок для отладки
        logger.info(f"[PUSH_SERVICE_TEST] Найдено {len(user_subscriptions)} активных подписок для пользователя {notification.user_id}")
        for i, sub in enumerate(user_subscriptions):
            logger.info(f"[PUSH_SERVICE_TEST] Подписка {i+1}/{len(user_subscriptions)} - ID: {sub.id}, Endpoint: {sub.endpoint}")

            # Анализ формата endpoint
            if "fcm.googleapis.com" in sub.endpoint:
                if "/fcm/send/" in sub.endpoint:
                    logger.warning(f"[PUSH_SERVICE_TEST] Подписка {sub.id} содержит старый формат FCM URL (/fcm/send/)")
                elif "/wp/" in sub.endpoint:
                    logger.info(f"[PUSH_SERVICE_TEST] Подписка {sub.id} содержит правильный формат FCM URL (/wp/)")
                else:
                    logger.warning(f"[PUSH_SERVICE_TEST] Подписка {sub.id} содержит неизвестный формат FCM URL")
            else:
                logger.info(f"[PUSH_SERVICE_TEST] Подписка {sub.id} не использует FCM")

        # Используем ту же логику формирования payload, что и в основной функции
        icon_url = notification.data.get('icon', url_for('static', filename='img/push-icon.png', _external=True))
        action_url = notification.data.get('url', url_for('main.home', _external=True))

        payload = {
            'title': notification.title,
            'message': notification.message,
            'icon': icon_url,
            'data': {'url': action_url}
        }
        payload_json_string = json.dumps(payload, ensure_ascii=False)

        # Отправляем только на первую активную подписку для теста
        subscription_to_test = user_subscriptions[0]
        logger.info(f"[PUSH_SERVICE_TEST] Попытка отправки на подписку ID {subscription_to_test.id}, Endpoint: {subscription_to_test.endpoint}")

        # Адаптируем endpoint для теста, если нужно
        original_endpoint = subscription_to_test.endpoint

        # Проверяем формат и исправляем его, если необходимо
        adapted_endpoint = original_endpoint

        # Для FCM проверяем необходимость адаптации
        if "fcm.googleapis.com" in original_endpoint:
            # Если старый формат - адаптируем
            if "/fcm/send/" in original_endpoint:
                token = original_endpoint.split("/fcm/send/")[1]
                adapted_endpoint = f"https://fcm.googleapis.com/wp/{token}"
                logger.info(f"[PUSH_SERVICE_TEST] Адаптирован endpoint старого формата: {adapted_endpoint}")
            # Если отсутствует wp/ - исправляем
            elif "/wp/" not in original_endpoint:
                # Получаем токен (последняя часть URL)
                token = original_endpoint.split("/")[-1]
                adapted_endpoint = f"https://fcm.googleapis.com/wp/{token}"
                logger.info(f"[PUSH_SERVICE_TEST] Добавлен префикс /wp/: {adapted_endpoint}")
            # Если нет https:// - добавляем
            if not adapted_endpoint.startswith("https://"):
                adapted_endpoint = f"https://{adapted_endpoint}"
                logger.info(f"[PUSH_SERVICE_TEST] Добавлен протокол https://: {adapted_endpoint}")

        # Временно изменяем endpoint в объекте подписки для тестовой отправки
        original_endpoint = subscription_to_test.endpoint
        subscription_to_test.endpoint = adapted_endpoint

        try:
            # Отправляем уведомление с адаптированным endpoint
            self._send_to_subscription(subscription_to_test, payload_json_string, claims=claims)
            logger.info(f"[PUSH_SERVICE_TEST] Тестовое уведомление успешно отправлено на подписку ID {subscription_to_test.id}")

            # Если отправка прошла успешно и endpoint был изменен, обновляем его в базе данных
            if original_endpoint != adapted_endpoint:
                logger.info(f"[PUSH_SERVICE_TEST] Обновляем endpoint в БД с '{original_endpoint}' на '{adapted_endpoint}'")
                try:
                    subscription_db = PushSubscription.query.get(subscription_to_test.id)
                    if subscription_db:
                        subscription_db.endpoint = adapted_endpoint
                        db.session.commit()
                        logger.info(f"[PUSH_SERVICE_TEST] Endpoint успешно обновлен в БД")
                except Exception as db_error:
                    logger.error(f"[PUSH_SERVICE_TEST] Ошибка обновления endpoint в БД: {db_error}", exc_info=True)

            return {'status': 'success', 'message': 'Тестовое уведомление успешно отправлено.'}
        except Exception as e:
            logger.error(f"[PUSH_SERVICE_TEST] Ошибка при отправке тестового уведомления: {e}", exc_info=True)

            # Восстанавливаем оригинальный endpoint в объекте
            subscription_to_test.endpoint = original_endpoint

            return {
                'status': 'send_error',
                'message': str(e),
                'details': {
                    'original_endpoint': original_endpoint,
                    'adapted_endpoint': adapted_endpoint
                }
            }
        finally:
            # В любом случае восстанавливаем оригинальный endpoint в объекте
            subscription_to_test.endpoint = original_endpoint


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
