#!/usr/bin/env python
"""
Скрипт для сброса и диагностики подписок на push-уведомления
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

    app = create_app()

    with app.app_context():
        print("Статус подписок на push-уведомления:")
        print("-" * 50)

        # Получаем всех пользователей с активированными уведомлениями
        users_with_notifications = User.query.filter_by(browser_notifications_enabled=True).all()
        print(f"Пользователей с активированными уведомлениями: {len(users_with_notifications)}")

        # Получаем все подписки
        all_subscriptions = PushSubscription.query.all()
        print(f"Всего подписок в системе: {len(all_subscriptions)}")

        active_subscriptions = PushSubscription.query.filter_by(is_active=True).all()
        print(f"Активных подписок: {len(active_subscriptions)}")

        inactive_subscriptions = PushSubscription.query.filter_by(is_active=False).all()
        print(f"Неактивных подписок: {len(inactive_subscriptions)}")

        # Сброс всех подписок в активное состояние
        print("\nСбрасываю состояние подписок...")

        for subscription in all_subscriptions:
            subscription.is_active = True
            subscription.last_used = datetime.now(timezone.utc)

        # Убедимся, что все пользователи имеют право получать уведомления
        for user in users_with_notifications:
            user_subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
            print(f"Пользователь {user.username} (ID: {user.id}): {len(user_subscriptions)} подписок")

            # Активируем все подписки для этого пользователя
            for sub in user_subscriptions:
                sub.is_active = True
                sub.last_used = datetime.now(timezone.utc)
                print(f"  - Подписка ID {sub.id}: установлена как активная")

            # Если у пользователя есть подписки, устанавливаем флаг browser_notifications_enabled
            if user_subscriptions:
                if not user.browser_notifications_enabled:
                    user.browser_notifications_enabled = True
                    print(f"  - Установлен флаг browser_notifications_enabled=True для пользователя {user.username}")
                else:
                    print(f"  - Флаг browser_notifications_enabled уже активен для пользователя {user.username}")

        # Сохраняем изменения
        db.session.commit()
        print("\nИзменения сохранены в базе данных!")

        # Проверяем текущего пользователя
        current_user = User.query.filter_by(username=input("Введите имя пользователя для проверки: ")).first()
        if current_user:
            print(f"\nИнформация о пользователе {current_user.username}:")
            print(f"ID: {current_user.id}")
            print(f"Email: {current_user.email}")
            print(f"browser_notifications_enabled: {current_user.browser_notifications_enabled}")

            user_subscriptions = PushSubscription.query.filter_by(user_id=current_user.id).all()
            print(f"Количество подписок: {len(user_subscriptions)}")

            for i, sub in enumerate(user_subscriptions):
                print(f"\nПодписка #{i+1}:")
                print(f"  ID: {sub.id}")
                print(f"  Активна: {sub.is_active}")
                print(f"  Создана: {sub.created_at}")
                print(f"  Последнее использование: {sub.last_used}")
                print(f"  Endpoint: {sub.endpoint[:50]}...")
                print(f"  p256dh_key: {sub.p256dh_key[:20]}...")
                print(f"  auth_key: {sub.auth_key[:10]}...")
        else:
            print(f"Пользователь не найден")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
