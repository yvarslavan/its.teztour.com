#!/usr/bin/env python3
"""
Скрипт для очистки неактивных пуш-подписок
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cleanup_push_subscriptions.log')
    ]
)

logger = logging.getLogger(__name__)

def create_minimal_app():
    """Создание минимального приложения Flask без планировщика"""
    from flask import Flask
    from blog.models import db
    from blog.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализируем только базу данных, без планировщика
    db.init_app(app)

    return app

def cleanup_invalid_subscriptions():
    """Очистка неактивных и недействительных подписок"""
    app = create_minimal_app()

    with app.app_context():
        from blog.models import PushSubscription, db

        logger.info("=== Начало очистки пуш-подписок ===")

        # Получаем все подписки
        all_subscriptions = PushSubscription.query.all()
        logger.info(f"Всего подписок в базе: {len(all_subscriptions)}")

        # Статистика
        deleted_count = 0
        deactivated_count = 0

        # Критерии для удаления/деактивации
        cutoff_date = datetime.now() - timedelta(days=30)  # Используем datetime.now() вместо utcnow()

        for subscription in all_subscriptions:
            should_delete = False
            should_deactivate = False
            reason = ""

            # Проверяем endpoint
            if not subscription.endpoint or subscription.endpoint.strip() == "":
                should_delete = True
                reason = "Пустой endpoint"

            # Проверяем ключи
            elif not subscription.p256dh_key or not subscription.auth_key:
                should_delete = True
                reason = "Отсутствуют ключи шифрования"

            # Проверяем дату последнего использования
            elif subscription.last_used and subscription.last_used < cutoff_date:
                should_deactivate = True
                reason = f"Не использовалась с {subscription.last_used}"

            # Проверяем на недействительные endpoints
            elif "fcm.googleapis.com" in subscription.endpoint and len(subscription.endpoint) < 100:
                should_delete = True
                reason = "Недействительный FCM endpoint"

            if should_delete:
                logger.info(f"Удаляем подписку ID {subscription.id}: {reason}")
                db.session.delete(subscription)
                deleted_count += 1

            elif should_deactivate:
                logger.info(f"Деактивируем подписку ID {subscription.id}: {reason}")
                subscription.is_active = False
                deactivated_count += 1

        # Сохраняем изменения
        try:
            db.session.commit()
            logger.info(f"✅ Очистка завершена:")
            logger.info(f"  - Удалено подписок: {deleted_count}")
            logger.info(f"  - Деактивировано подписок: {deactivated_count}")
            logger.info(f"  - Осталось активных: {len(all_subscriptions) - deleted_count - deactivated_count}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка при сохранении изменений: {str(e)}")
            return False

        return True

def analyze_push_errors():
    """Анализ ошибок пуш-уведомлений"""
    app = create_minimal_app()

    with app.app_context():
        from blog.models import PushSubscription

        logger.info("=== Анализ пуш-подписок ===")

        # Активные подписки
        active_subscriptions = PushSubscription.query.filter_by(is_active=True).all()
        logger.info(f"Активных подписок: {len(active_subscriptions)}")

        # Группировка по типам endpoint
        endpoint_types = {}
        for sub in active_subscriptions:
            if sub.endpoint:
                if "fcm.googleapis.com" in sub.endpoint:
                    endpoint_types["FCM"] = endpoint_types.get("FCM", 0) + 1
                elif "mozilla.com" in sub.endpoint:
                    endpoint_types["Mozilla"] = endpoint_types.get("Mozilla", 0) + 1
                elif "microsoft.com" in sub.endpoint:
                    endpoint_types["Microsoft"] = endpoint_types.get("Microsoft", 0) + 1
                else:
                    endpoint_types["Другие"] = endpoint_types.get("Другие", 0) + 1

        logger.info("Распределение по типам:")
        for endpoint_type, count in endpoint_types.items():
            logger.info(f"  {endpoint_type}: {count}")

        # Проверяем подписки без последнего использования
        never_used = PushSubscription.query.filter_by(is_active=True, last_used=None).count()
        logger.info(f"Подписок без использования: {never_used}")

        # Старые подписки
        cutoff_date = datetime.now() - timedelta(days=7)  # Используем datetime.now()
        old_subscriptions = PushSubscription.query.filter(
            PushSubscription.is_active == True,
            PushSubscription.last_used < cutoff_date
        ).count()
        logger.info(f"Подписок старше 7 дней: {old_subscriptions}")

def test_vapid_keys():
    """Проверка VAPID ключей"""
    logger.info("=== Проверка VAPID ключей ===")

    try:
        from pywebpush import webpush
        logger.info("✅ Библиотека pywebpush доступна")

        # Проверяем наличие ключей в конфигурации
        app = create_minimal_app()
        with app.app_context():
            vapid_private_key = app.config.get('VAPID_PRIVATE_KEY')
            vapid_public_key = app.config.get('VAPID_PUBLIC_KEY')

            if vapid_private_key and vapid_public_key:
                logger.info("✅ VAPID ключи найдены в конфигурации")
                logger.info(f"Публичный ключ: {vapid_public_key[:20]}...")
            else:
                logger.warning("⚠️ VAPID ключи не найдены в конфигурации")

    except ImportError:
        logger.error("❌ Библиотека pywebpush не установлена")

def get_subscription_stats():
    """Получение статистики подписок"""
    app = create_minimal_app()

    with app.app_context():
        from blog.models import PushSubscription
        from sqlalchemy import or_

        logger.info("=== Статистика подписок ===")

        # Общая статистика
        total = PushSubscription.query.count()
        active = PushSubscription.query.filter_by(is_active=True).count()
        inactive = PushSubscription.query.filter_by(is_active=False).count()

        # Подписки с ошибками
        error_subscriptions = PushSubscription.query.filter(
            or_(
                PushSubscription.endpoint == None,
                PushSubscription.endpoint == '',
                PushSubscription.p256dh_key == None,
                PushSubscription.auth_key == None
            )
        ).count()

        # Старые подписки
        cutoff_date = datetime.now() - timedelta(days=30)
        old_subscriptions = PushSubscription.query.filter(
            or_(
                PushSubscription.last_used < cutoff_date,
                PushSubscription.last_used == None
            )
        ).count()

        logger.info(f"Всего подписок: {total}")
        logger.info(f"Активных: {active}")
        logger.info(f"Неактивных: {inactive}")
        logger.info(f"С ошибками данных: {error_subscriptions}")
        logger.info(f"Старых (>30 дней): {old_subscriptions}")

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'error_subscriptions': error_subscriptions,
            'old_subscriptions': old_subscriptions
        }

def main():
    """Основная функция"""
    logger.info(f"Начало очистки пуш-подписок - {datetime.now()}")
    logger.info("=" * 60)

    try:
        # Получаем статистику
        stats = get_subscription_stats()

        # Анализируем текущее состояние
        analyze_push_errors()

        # Проверяем VAPID ключи
        test_vapid_keys()

        # Спрашиваем подтверждение на очистку
        print("\n" + "=" * 60)
        print("ВНИМАНИЕ: Будет выполнена очистка неактивных пуш-подписок")
        print("Это может удалить подписки, которые больше не работают")
        print(f"Найдено проблемных подписок: {stats['error_subscriptions'] + stats['old_subscriptions']}")
        print("=" * 60)

        response = input("Продолжить очистку? (y/N): ").strip().lower()

        if response == 'y':
            success = cleanup_invalid_subscriptions()
            if success:
                logger.info("🎉 Очистка успешно завершена!")
                return 0
            else:
                logger.error("❌ Очистка завершилась с ошибками")
                return 1
        else:
            logger.info("Очистка отменена пользователем")
            return 0

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
