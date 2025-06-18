#!/usr/bin/env python
"""
Скрипт для проверки статуса подписок на push-уведомления и их активации
"""
import os
import sys
from datetime import datetime, timezone

# Добавляем текущий каталог в sys.path
sys.path.insert(0, os.path.abspath('.'))

try:
    from flask import Flask
    from blog import db, create_app
    from blog.models import User, PushSubscription
    from blog.config.vapid_keys import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS

    app = create_app()

    with app.app_context():
        # Запрашиваем имя пользователя
        username = input("Введите имя пользователя: ")

        # Находим пользователя
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"Пользователь '{username}' не найден!")
            sys.exit(1)

        print(f"\nИнформация о пользователе {user.username}:")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"browser_notifications_enabled: {user.browser_notifications_enabled}")

        # Получаем подписки пользователя
        user_subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
        print(f"Количество подписок: {len(user_subscriptions)}")

        if len(user_subscriptions) == 0:
            print("У пользователя нет подписок на push-уведомления")

            # Спрашиваем, хочет ли пользователь создать тестовую подписку
            create_test = input("\nСоздать тестовую подписку? (y/n): ")
            if create_test.lower() == 'y':
                # Создаем тестовую подписку
                test_endpoint = "https://fcm.googleapis.com/wp/test-endpoint-for-user-" + str(user.id)
                test_p256dh = "BMrH4Qzq8NbYlBZ4jQJJ8RpT+wM5FyJjH9LjJLBtYLMf6bpLE8XmGh3r2mKlLjMdGXFpajqdCQgGvk0MAx3fVJ0="
                test_auth = "WoUXBULbLYOQCzTbQSyF8Q=="

                new_subscription = PushSubscription(
                    user_id=user.id,
                    endpoint=test_endpoint,
                    p256dh_key=test_p256dh,
                    auth_key=test_auth,
                    user_agent="Test Browser"
                )
                db.session.add(new_subscription)

                # Активируем флаг уведомлений для пользователя
                user.browser_notifications_enabled = True
                db.session.commit()

                print(f"Тестовая подписка создана для пользователя {user.username}")
            sys.exit(0)

        # Выводим информацию о подписках и предлагаем их активировать
        active_count = 0
        inactive_count = 0

        for i, sub in enumerate(user_subscriptions):
            print(f"\nПодписка #{i+1}:")
            print(f"  ID: {sub.id}")
            print(f"  Активна: {sub.is_active}")
            print(f"  Создана: {sub.created_at}")
            print(f"  Последнее использование: {sub.last_used}")
            print(f"  Endpoint: {sub.endpoint[:50]}...")

            if sub.is_active:
                active_count += 1
            else:
                inactive_count += 1

        print(f"\nАктивных подписок: {active_count}")
        print(f"Неактивных подписок: {inactive_count}")

        # Проверяем VAPID ключи
        print("\nVAPID ключи:")
        print(f"Public Key: {VAPID_PUBLIC_KEY[:20]}...")
        print(f"Private Key: {VAPID_PRIVATE_KEY[:10]}...")
        print(f"Claims: {VAPID_CLAIMS}")

        # Активируем подписки и флаг для пользователя, если есть неактивные
        if inactive_count > 0:
            activate = input("\nАктивировать неактивные подписки? (y/n): ")
            if activate.lower() == 'y':
                for sub in user_subscriptions:
                    if not sub.is_active:
                        sub.is_active = True
                        sub.last_used = datetime.now(timezone.utc)
                        print(f"Подписка ID {sub.id} активирована")

                user.browser_notifications_enabled = True
                db.session.commit()
                print(f"Все подписки активированы для пользователя {user.username}")

        # Предлагаем создать тестовую подписку с FCM endpoint
        create_fcm = input("\nСоздать тестовую подписку в формате FCM? (y/n): ")
        if create_fcm.lower() == 'y':
            # Создаем тестовую подписку с FCM endpoint
            test_fcm_endpoint = f"https://fcm.googleapis.com/fcm/send/test-fcm-token-{user.id}"
            test_p256dh = "BMrH4Qzq8NbYlBZ4jQJJ8RpT+wM5FyJjH9LjJLBtYLMf6bpLE8XmGh3r2mKlLjMdGXFpajqdCQgGvk0MAx3fVJ0="
            test_auth = "WoUXBULbLYOQCzTbQSyF8Q=="

            # Деактивируем все существующие подписки, чтобы активной была только новая
            PushSubscription.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})

            new_subscription = PushSubscription(
                user_id=user.id,
                endpoint=test_fcm_endpoint,
                p256dh_key=test_p256dh,
                auth_key=test_auth,
                user_agent="Test FCM Browser"
            )
            db.session.add(new_subscription)

            # Активируем флаг уведомлений для пользователя
            user.browser_notifications_enabled = True
            db.session.commit()

            print(f"Тестовая FCM подписка создана для пользователя {user.username}")
            print(f"Endpoint: {test_fcm_endpoint}")

        print("\nГотово!")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
