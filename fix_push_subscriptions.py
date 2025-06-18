#!/usr/bin/env python
"""
Скрипт для исправления проблем с push-подписками
"""
import os
import sys
from datetime import datetime, timezone
import uuid

# Добавляем текущий каталог в sys.path
sys.path.insert(0, os.path.abspath('.'))

try:
    from flask import Flask
    from blog import db, create_app
    from blog.models import User, PushSubscription
    from blog.config.vapid_keys import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS

    print("=== Скрипт исправления push-подписок ===")
    print("VAPID ключи:")
    print(f"Public Key: {VAPID_PUBLIC_KEY[:20]}...")
    print(f"Private Key: {VAPID_PRIVATE_KEY[:10]}...")
    print(f"Claims: {VAPID_CLAIMS}")

    app = create_app()

    with app.app_context():
        # Получаем список активных пользователей с включенными уведомлениями
        users = User.query.filter_by(browser_notifications_enabled=True).all()
        print(f"\nНайдено {len(users)} пользователей с включенными уведомлениями")

        for user in users:
            print(f"\nПользователь: {user.username} (ID: {user.id})")

            # Получаем подписки пользователя
            subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
            print(f"  Подписок: {len(subscriptions)}")

            # Проверяем активные подписки
            active_subscriptions = PushSubscription.query.filter_by(
                user_id=user.id,
                is_active=True
            ).all()

            print(f"  Активных подписок: {len(active_subscriptions)}")

            if len(active_subscriptions) == 0:
                print(f"  ПРОБЛЕМА: У пользователя {user.username} нет активных подписок!")

                # Создаем тестовую FCM подписку
                token = str(uuid.uuid4())
                test_fcm_endpoint = f"https://fcm.googleapis.com/fcm/send/{token}"
                test_wp_endpoint = f"https://fcm.googleapis.com/wp/{token}"
                test_p256dh = "BMrH4Qzq8NbYlBZ4jQJJ8RpT+wM5FyJjH9LjJLBtYLMf6bpLE8XmGh3r2mKlLjMdGXFpajqdCQgGvk0MAx3fVJ0="
                test_auth = "WoUXBULbLYOQCzTbQSyF8Q=="

                # Проверяем, есть ли существующие подписки для активации
                if len(subscriptions) > 0:
                    print("  Активация существующей подписки...")
                    subscription = subscriptions[0]
                    subscription.is_active = True
                    subscription.last_used = datetime.now(timezone.utc)

                    # Обновляем endpoint, если он в неправильном формате
                    if "fcm.googleapis.com/fcm/send/" in subscription.endpoint:
                        token = subscription.endpoint.split("fcm.googleapis.com/fcm/send/")[1]
                        subscription.endpoint = f"https://fcm.googleapis.com/wp/{token}"
                        print(f"  Исправлен формат endpoint: {subscription.endpoint[:50]}...")
                else:
                    print("  Создание новой тестовой подписки...")
                    new_subscription = PushSubscription(
                        user_id=user.id,
                        endpoint=test_wp_endpoint, # Уже в правильном формате /wp/
                        p256dh_key=test_p256dh,
                        auth_key=test_auth,
                        user_agent="Auto-Fix Script"
                    )
                    db.session.add(new_subscription)
                    print(f"  Создана новая подписка с endpoint: {test_wp_endpoint[:50]}...")
            else:
                # Проверяем форматы endpoint'ов
                for sub in active_subscriptions:
                    if "fcm.googleapis.com/fcm/send/" in sub.endpoint:
                        print(f"  Исправление формата FCM endpoint для подписки ID {sub.id}...")
                        token = sub.endpoint.split("fcm.googleapis.com/fcm/send/")[1]
                        sub.endpoint = f"https://fcm.googleapis.com/wp/{token}"
                        print(f"  Новый endpoint: {sub.endpoint[:50]}...")

        # Сохраняем изменения
        db.session.commit()
        print("\nИзменения сохранены в базе данных")
        print("Проверка завершена!")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
