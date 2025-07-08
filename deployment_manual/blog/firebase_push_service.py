"""
Современный сервис для отправки push-уведомлений через Firebase Admin SDK
Заменяет устаревший pywebpush + Legacy FCM API
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# Импорты для Firebase Admin SDK (будут установлены отдельно)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK не установлен. Используйте: pip install firebase-admin")

logger = logging.getLogger(__name__)

class FirebasePushService:
    """Современный сервис для отправки push уведомлений через Firebase Admin SDK"""

    def __init__(self):
        self.app = None
        self.initialized = False

    def initialize(self, service_account_path: str, project_id: str) -> bool:
        """
        Инициализация Firebase Admin SDK

        Args:
            service_account_path: Путь к JSON файлу Service Account
            project_id: ID проекта Firebase

        Returns:
            bool: True если инициализация успешна
        """
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK не установлен")
            return False

        try:
            # Проверяем, не инициализирован ли уже
            if not self.initialized:
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': project_id
                })
                self.initialized = True
                logger.info(f"Firebase Admin SDK инициализирован для проекта {project_id}")

            return True

        except Exception as e:
            logger.error(f"Ошибка инициализации Firebase Admin SDK: {e}")
            return False

    def send_to_token(self, token: str, title: str, message: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Отправка push уведомления на конкретный токен

        Args:
            token: FCM токен устройства
            title: Заголовок уведомления
            message: Текст уведомления
            data: Дополнительные данные

        Returns:
            Dict с результатом отправки
        """
        if not self.initialized:
            return {
                'success': False,
                'error': 'Firebase Admin SDK не инициализирован'
            }

        try:
            # Создаем сообщение
            notification = messaging.Notification(
                title=title,
                body=message
            )

            web_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=message,
                    icon='/static/img/push-icon.png'
                )
            )

            if data:
                web_config.data = data

            message_obj = messaging.Message(
                notification=notification,
                webpush=web_config,
                token=token
            )

            # Отправляем
            response = messaging.send(message_obj)

            logger.info(f"Push уведомление отправлено успешно: {response}")

            return {
                'success': True,
                'message_id': response,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except messaging.UnregisteredError:
            logger.warning(f"Токен не зарегистрирован: {token[:20]}...")
            return {
                'success': False,
                'error': 'unregistered_token',
                'should_remove_token': True
            }

        except messaging.InvalidArgumentError as e:
            logger.error(f"Неверные аргументы для FCM: {e}")
            return {
                'success': False,
                'error': f'invalid_arguments: {str(e)}'
            }

        except Exception as e:
            logger.error(f"Ошибка отправки push уведомления: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_to_multiple_tokens(self, tokens: List[str], title: str, message: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Отправка push уведомления на несколько токенов

        Args:
            tokens: Список FCM токенов
            title: Заголовок уведомления
            message: Текст уведомления
            data: Дополнительные данные

        Returns:
            Dict с результатами отправки
        """
        if not self.initialized:
            return {
                'success': False,
                'error': 'Firebase Admin SDK не инициализирован'
            }

        if not tokens:
            return {
                'success': False,
                'error': 'Список токенов пуст'
            }

        try:
            # Создаем multicast сообщение
            notification = messaging.Notification(
                title=title,
                body=message
            )

            web_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=message,
                    icon='/static/img/push-icon.png'
                )
            )

            if data:
                web_config.data = data

            multicast_message = messaging.MulticastMessage(
                notification=notification,
                webpush=web_config,
                tokens=tokens
            )

            # Отправляем
            response = messaging.send_multicast(multicast_message)

            logger.info(f"Multicast отправка: {response.success_count}/{len(tokens)} успешно")

            # Обрабатываем ответы
            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append({
                        'token': tokens[idx][:20] + '...',
                        'error': resp.exception.code if resp.exception else 'unknown'
                    })

            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка multicast отправки: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Глобальный экземпляр сервиса
firebase_push_service = FirebasePushService()

def get_firebase_push_service() -> FirebasePushService:
    """Получить глобальный экземпляр Firebase Push Service"""
    return firebase_push_service
