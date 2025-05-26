"""
Улучшенный сервис уведомлений с поддержкой браузерных пуш-уведомлений
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import threading
from contextlib import contextmanager
from flask import current_app, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from blog import db
from blog.models import User, Notifications, NotificationsAddNotes, PushSubscription
import redmine

# Попытка импорта pywebpush
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logging.warning("pywebpush не установлен. Браузерные пуш-уведомления будут недоступны.")


# Настройка логгера
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Типы уведомлений"""
    STATUS_CHANGE = "status_change"
    COMMENT_ADDED = "comment_added"
    ISSUE_ASSIGNED = "issue_assigned"
    ISSUE_CREATED = "issue_created"


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

    def is_duplicate(self, notification: NotificationData) -> bool:
        """Проверка на дублирование"""
        with self._lock:
            hash_key = notification.get_hash()
            now = datetime.now()

            # Очищаем устаревшие записи
            self._cleanup_expired(now)

            # Проверяем наличие дубликата
            if hash_key in self._cache:
                return True

            # Добавляем новую запись
            self._cache[hash_key] = now
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
        try:
            logger.info(f"Начало обработки уведомлений для пользователя {user_id}")

            # Получаем подключение к MySQL
            connection = redmine.get_connection(
                redmine.db_redmine_host,
                redmine.db_redmine_user_name,
                redmine.db_redmine_password,
                redmine.db_redmine_name
            )

            if not connection:
                logger.error(f"Не удалось подключиться к MySQL для пользователя {user_id}")
                return 0

            total_processed = 0

            try:
                # Обрабатываем уведомления о статусах
                status_count = self._process_status_notifications(
                    connection, user_email, user_id
                )
                total_processed += status_count

                # Обрабатываем уведомления о комментариях
                comment_count = self._process_comment_notifications(
                    connection, user_email, user_id
                )
                total_processed += comment_count

                logger.info(f"Обработано {total_processed} уведомлений для пользователя {user_id}")
                return total_processed

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"Ошибка при обработке уведомлений для пользователя {user_id}: {e}")
            return 0

    def _process_status_notifications(self, connection, user_email: str, user_id: int) -> int:
        """Обработка уведомлений об изменении статуса"""
        try:
            cursor = connection.cursor(dictionary=True)
            email_part = user_email.lower().split("@")[0]

            query = """
                SELECT ID, IssueID, OldStatus, NewStatus, OldSubj, Body, RowDateCreated
                FROM u_its_update_status
                WHERE LOWER(SUBSTRING_INDEX(Author, '@', 1)) = LOWER(%s)
                ORDER BY RowDateCreated DESC
                LIMIT 50
            """

            cursor.execute(query, (email_part,))
            rows = cursor.fetchall()

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
                if not self.deduplicator.is_duplicate(notification_data):
                    notifications_to_save.append(notification_data)
                    ids_to_delete_from_mysql.append(row['ID'])
                    processed_count += 1

            # Сохраняем уведомления в базу
            if notifications_to_save:
                self._save_status_notifications(notifications_to_save)

                # Отправляем браузерные пуш-уведомления
                for notification in notifications_to_save:
                    self.push_service.send_push_notification(notification)

                # Удаляем успешно обработанные записи из MySQL по их ID
                if ids_to_delete_from_mysql:
                    self._delete_processed_status_notifications(connection, ids_to_delete_from_mysql)

            cursor.close()
            return processed_count

        except Exception as e:
            logger.error(f"Ошибка при обработке уведомлений о статусах: {e}")
            return 0

    def _process_comment_notifications(self, connection, user_email: str, user_id: int) -> int:
        """Обработка уведомлений о комментариях"""
        try:
            cursor = connection.cursor(dictionary=True)
            email_part = user_email.lower().split("@")[0]

            query = """
                SELECT ID, issue_id, Author, notes, date_created
                FROM u_its_add_notes
                WHERE LOWER(SUBSTRING_INDEX(Author, '@', 1)) = LOWER(%s)
                ORDER BY date_created DESC
                LIMIT 50
            """

            cursor.execute(query, (email_part,))
            rows = cursor.fetchall()

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
                if not self.deduplicator.is_duplicate(notification_data):
                    notifications_to_save.append(notification_data)
                    ids_to_delete_from_mysql.append(row['ID'])
                    processed_count += 1

            # Сохраняем уведомления в базу
            if notifications_to_save:
                self._save_comment_notifications(notifications_to_save)

                # Отправляем браузерные пуш-уведомления
                for notification in notifications_to_save:
                    self.push_service.send_push_notification(notification)

                # Удаляем успешно обработанные записи из MySQL по их ID
                if ids_to_delete_from_mysql:
                    self._delete_processed_comment_notifications(connection, ids_to_delete_from_mysql)

            cursor.close()
            return processed_count

        except Exception as e:
            logger.error(f"Ошибка при обработке уведомлений о комментариях: {e}")
            return 0

    def _save_status_notifications(self, notifications: List[NotificationData]):
        """Сохранение уведомлений о статусах в базу данных"""
        try:
            for notification in notifications:
                # Проверяем, нет ли уже такого уведомления в базе
                existing = db.session.query(Notifications).filter(
                    and_(
                        Notifications.user_id == notification.user_id,
                        Notifications.issue_id == notification.issue_id,
                        Notifications.old_status == notification.data['old_status'],
                        Notifications.new_status == notification.data['new_status']
                    )
                ).first()

                if not existing:
                    db_notification = Notifications(
                        user_id=notification.user_id,
                        issue_id=notification.issue_id,
                        old_status=notification.data['old_status'],
                        new_status=notification.data['new_status'],
                        old_subj=notification.data['subject'],
                        date_created=notification.created_at
                    )
                    db.session.add(db_notification)

            db.session.commit()
            logger.info(f"Сохранено {len(notifications)} уведомлений о статусах")

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при сохранении уведомлений о статусах: {e}")
            raise

    def _save_comment_notifications(self, notifications: List[NotificationData]):
        """Сохранение уведомлений о комментариях в базу данных"""
        try:
            for notification in notifications:
                # Проверяем, нет ли уже такого уведомления в базе
                existing = db.session.query(NotificationsAddNotes).filter(
                    and_(
                        NotificationsAddNotes.user_id == notification.user_id,
                        NotificationsAddNotes.issue_id == notification.issue_id,
                        NotificationsAddNotes.author == notification.data['author'],
                        NotificationsAddNotes.notes == notification.data['notes']
                    )
                ).first()

                if not existing:
                    db_notification = NotificationsAddNotes(
                        user_id=notification.user_id,
                        issue_id=notification.issue_id,
                        author=notification.data['author'],
                        notes=notification.data['notes'],
                        date_created=notification.created_at
                    )
                    db.session.add(db_notification)

            db.session.commit()
            logger.info(f"Сохранено {len(notifications)} уведомлений о комментариях")

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Ошибка при сохранении уведомлений о комментариях: {e}")
            raise

    def _delete_processed_status_notifications(self, connection, ids_to_delete: List[int]):
        """Удаление обработанных уведомлений о статусах из MySQL по списку ID"""
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
            logger.info(f"Удалено {cursor.rowcount} записей о статусах из MySQL (IDs: {ids_to_delete})")
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при удалении обработанных уведомлений о статусах (IDs: {ids_to_delete}): {e}")
            # Важно: не откатывать транзакцию здесь, если она управляется выше по стеку,
            # но для DELETE это обычно атомарная операция для данного cursor.execute.

    def _delete_processed_comment_notifications(self, connection, ids_to_delete: List[int]):
        """Удаление обработанных уведомлений о комментариях из MySQL по списку ID"""
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
            logger.info(f"Удалено {cursor.rowcount} записей о комментариях из MySQL (IDs: {ids_to_delete})")
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при удалении обработанных уведомлений о комментариях (IDs: {ids_to_delete}): {e}")

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
        if self.vapid_private_key is None:
            try:
                from flask import current_app
                self.vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
                self.vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY')
                self.vapid_claims = current_app.config.get('VAPID_CLAIMS', {
                    "sub": "mailto:admin@tez-tour.com"
                })
            except RuntimeError:
                # Если нет контекста приложения, используем значения по умолчанию
                logger.warning("Нет контекста приложения для получения VAPID конфигурации")
                self.vapid_private_key = None
                self.vapid_public_key = None
                self.vapid_claims = {"sub": "mailto:admin@tez-tour.com"}

    def send_push_notification(self, notification: NotificationData):
        # logger.info("[PUSH_SERVICE] ВХОД В send_push_notification") # Закомментируем пока
        # logger.info(f"[PUSH_SERVICE] WEBPUSH_AVAILABLE: {WEBPUSH_AVAILABLE}")
        print(f"DEBUGGING_SEND_PUSH: ENTERED send_push_notification. WEBPUSH_AVAILABLE={WEBPUSH_AVAILABLE}", flush=True)

        try:
            if not WEBPUSH_AVAILABLE:
                print("[DEBUGGING_SEND_PUSH] pywebpush недоступен, ВЫХОД", flush=True)
                logger.warning("[PUSH_SERVICE] pywebpush недоступен, пропускаем отправку пуш-уведомления")
                return

            print("[DEBUGGING_SEND_PUSH] Проверка WEBPUSH_AVAILABLE пройдена", flush=True)
            logger.info("[PUSH_SERVICE] ВХОД В send_push_notification - ПОСЛЕ ПРОВЕРКИ WEBPUSH_AVAILABLE") # Новый лог

            logger.debug("[PUSH_SERVICE] Инициализация VAPID конфигурации...")
            self._ensure_vapid_config()
            logger.info("[PUSH_SERVICE] VAPID конфигурация инициализирована.")
            logger.info(f"[PUSH_SERVICE] VAPID Private Key Loaded: {bool(self.vapid_private_key)}")
            logger.info(f"[PUSH_SERVICE] VAPID Public Key Loaded: {bool(self.vapid_public_key)}")
            logger.info(f"[PUSH_SERVICE] VAPID Claims: {self.vapid_claims}")

            logger.debug(f"[PUSH_SERVICE] Получение подписок для пользователя {notification.user_id}...")
            subscriptions = self._get_user_subscriptions(notification.user_id)

            if not subscriptions:
                logger.warning(f"[PUSH_SERVICE] Нет подписок для пользователя {notification.user_id}")
                print(f"[DEBUGGING_SEND_PUSH] Нет подписок для пользователя {notification.user_id}, ВЫХОД", flush=True)
                return

            logger.info(f"[PUSH_SERVICE] Найдено {len(subscriptions)} подписок для пользователя {notification.user_id}")
            print(f"[DEBUGGING_SEND_PUSH] Найдено {len(subscriptions)} подписок", flush=True)

            push_data = {
                'title': notification.title,
                'body': notification.message,
                'icon': '/static/img/notification_icon.png',
                'badge': '/static/img/notification_badge.png',
                'tag': f"{notification.notification_type.value}_{notification.issue_id}",
                'data': {
                    'issue_id': notification.issue_id,
                    'type': notification.notification_type.value,
                    'url': f'/my-issues/{notification.issue_id}',
                    'timestamp': notification.created_at.isoformat()
                },
                'actions': [
                    {
                        'action': 'view',
                        'title': 'Просмотреть',
                        'icon': '/static/img/view_icon.png'
                    },
                    {
                        'action': 'close',
                        'title': 'Закрыть'
                    }
                ],
                'requireInteraction': True,
                'vibrate': [200, 100, 200]
            }
            logger.debug(f"[PUSH_SERVICE] Данные уведомления: {push_data}")
            print(f"[DEBUGGING_SEND_PUSH] Данные уведомления сформированы: {push_data.get('title')}", flush=True)

            successful_sends = 0
            failed_subscriptions = []
            subscriptions_to_deactivate = []

            for i, subscription_item in enumerate(subscriptions):
                logger.debug(f"[PUSH_SERVICE] Отправка подписке {i+1}/{len(subscriptions)} (ID: {subscription_item.id})")
                print(f"[DEBUGGING_SEND_PUSH] Отправка подписке ID: {subscription_item.id}", flush=True)
                try:
                    self._send_to_subscription(subscription_item, push_data)
                    successful_sends += 1
                    logger.debug(f"[PUSH_SERVICE] Успешная отправка подписке {subscription_item.id}")
                    print(f"[DEBUGGING_SEND_PUSH] Успешная отправка подписке ID: {subscription_item.id}", flush=True)
                    subscription_item.last_used = datetime.utcnow()
                except WebPushException as e_webpush:
                    logger.warning(f"[PUSH_SERVICE] WebPush ошибка для подписки {subscription_item.id}: {e_webpush}")
                    print(f"[DEBUGGING_SEND_PUSH] WebPushException для подписки ID {subscription_item.id}: {str(e_webpush)}", flush=True)

                    # Обработка различных типов ошибок
                    should_deactivate = False
                    if hasattr(e_webpush, 'response') and e_webpush.response:
                        status_code = e_webpush.response.status_code
                        response_text = e_webpush.response.text

                        logger.warning(f"[PUSH_SERVICE] Статус ответа: {status_code}")
                        logger.warning(f"[PUSH_SERVICE] Тело ответа: {response_text}")

                        # Деактивируем подписку при критических ошибках
                        if status_code in [401, 403, 404, 410, 413]:
                            should_deactivate = True
                            logger.info(f"[PUSH_SERVICE] Планируем деактивацию подписки {subscription_item.id} из-за ошибки {status_code}")

                        # Специальная обработка для FCM ошибок
                        if status_code == 404 and "fcm.googleapis.com" in subscription_item.endpoint:
                            if "valid push subscription endpoint should be specified" in response_text:
                                should_deactivate = True
                                logger.info(f"[PUSH_SERVICE] FCM подписка {subscription_item.id} недействительна, планируем деактивацию")

                    if should_deactivate:
                        subscriptions_to_deactivate.append(subscription_item)

                    failed_subscriptions.append(subscription_item)

                except Exception as e_generic:
                    logger.error(f"[PUSH_SERVICE] Неожиданная ошибка при отправке подписке {subscription_item.id}: {e_generic}")
                    print(f"[DEBUGGING_SEND_PUSH] НЕОЖИДАННАЯ ОШИБКА для подписки ID: {subscription_item.id}: {e_generic}", flush=True)
                    failed_subscriptions.append(subscription_item)

            # Деактивируем проблемные подписки
            if subscriptions_to_deactivate:
                for sub in subscriptions_to_deactivate:
                    sub.is_active = False
                    logger.info(f"[PUSH_SERVICE] Деактивирована подписка {sub.id}")

            # Сохраняем изменения в базе данных
            if successful_sends > 0 or subscriptions_to_deactivate:
                try:
                    db.session.commit()
                    logger.debug("[PUSH_SERVICE] Изменения подписок сохранены в БД")
                    if subscriptions_to_deactivate:
                        logger.info(f"[PUSH_SERVICE] Деактивировано {len(subscriptions_to_deactivate)} подписок")
                except Exception as e_db_commit:
                    logger.error(f"[PUSH_SERVICE] Ошибка при сохранении изменений подписок: {e_db_commit}")
                    db.session.rollback()

            logger.info(f"[PUSH_SERVICE] Отправлено {successful_sends} пуш-уведомлений для пользователя {notification.user_id}")
            if failed_subscriptions:
                logger.warning(f"[PUSH_SERVICE] Неудачных отправок: {len(failed_subscriptions)}")
            print(f"[DEBUGGING_SEND_PUSH] Отправлено {successful_sends}, неудачно {len(failed_subscriptions)}. ВЫХОД.", flush=True)

            # Если слишком много неудачных подписок, запускаем очистку
            if len(failed_subscriptions) > 10:
                logger.info("[PUSH_SERVICE] Обнаружено много неудачных подписок, запускаем фоновую очистку")
                self._schedule_cleanup()

        except Exception as e_outer:
            print(f"DEBUGGING_SEND_PUSH: ГЛОБАЛЬНАЯ ОШИБКА в send_push_notification: {str(e_outer)}", flush=True)
            import traceback
            print(f"DEBUGGING_SEND_PUSH: Traceback: {traceback.format_exc()}", flush=True)
            logger.error(f"[PUSH_SERVICE] Глобальная ошибка при отправке пуш-уведомления: {e_outer}")
            logger.error(f"[PUSH_SERVICE] Traceback: {traceback.format_exc()}")

    def _schedule_cleanup(self):
        """Планирование фоновой очистки неактивных подписок"""
        try:
            import threading
            cleanup_thread = threading.Thread(target=self._cleanup_inactive_subscriptions)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            logger.info("[PUSH_SERVICE] Запущена фоновая очистка подписок")
        except Exception as e:
            logger.error(f"[PUSH_SERVICE] Ошибка запуска фоновой очистки: {e}")

    def _cleanup_inactive_subscriptions(self):
        """Фоновая очистка неактивных подписок"""
        try:
            from flask import current_app
            with current_app.app_context():
                # Удаляем подписки, которые неактивны более 7 дней
                cutoff_date = datetime.utcnow() - timedelta(days=7)

                inactive_subscriptions = db.session.query(PushSubscription).filter(
                    PushSubscription.is_active == False,
                    PushSubscription.last_used < cutoff_date
                ).all()

                if inactive_subscriptions:
                    for sub in inactive_subscriptions:
                        db.session.delete(sub)

                    db.session.commit()
                    logger.info(f"[PUSH_SERVICE] Удалено {len(inactive_subscriptions)} неактивных подписок")

        except Exception as e:
            logger.error(f"[PUSH_SERVICE] Ошибка при очистке неактивных подписок: {e}")
            try:
                db.session.rollback()
            except:
                pass

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

    def _send_to_subscription(self, subscription: PushSubscription, data: Dict):
        """Отправка уведомления конкретной подписке"""
        logger.debug(f"[PUSH_SEND] Начало отправки подписке {subscription.id}")

        if not WEBPUSH_AVAILABLE:
            logger.error("[PUSH_SEND] pywebpush не установлен")
            raise Exception("pywebpush не установлен")

        # Проверяем наличие VAPID ключей
        if not self.vapid_private_key:
            logger.warning("[PUSH_SEND] VAPID ключи не настроены, пропускаем отправку пуш-уведомления")
            return

        try:
            # Подготавливаем данные подписки для pywebpush
            logger.debug(f"[PUSH_SEND] Подготовка данных подписки {subscription.id}")
            subscription_info = subscription.to_dict()
            logger.debug(f"[PUSH_SEND] Данные подписки: endpoint={subscription_info.get('endpoint', 'N/A')[:50]}...")

            # Отправляем уведомление
            logger.debug(f"[PUSH_SEND] Отправка через webpush для подписки {subscription.id}")
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(data),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )

            logger.info(f"[PUSH_SEND] Пуш-уведомление отправлено: {data['title']}, статус: {response.status_code}")

        except WebPushException as e:
            logger.warning(f"[PUSH_SEND] WebPush ошибка для подписки {subscription.id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.warning(f"[PUSH_SEND] Статус ответа: {e.response.status_code}")
                logger.warning(f"[PUSH_SEND] Тело ответа: {e.response.text}")
            raise

        except Exception as e:
            logger.error(f"[PUSH_SEND] Ошибка при отправке пуш-уведомления подписке {subscription.id}: {e}")
            import traceback
            logger.error(f"[PUSH_SEND] Traceback: {traceback.format_exc()}")
            raise


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
