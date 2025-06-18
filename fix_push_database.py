#!/usr/bin/env python
"""
Скрипт для исправления проблем с подписками на push-уведомления в базе данных
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
        print("ИСПРАВЛЕНИЕ ПРОБЛЕМ С PUSH-УВЕДОМЛЕНИЯМИ")
        print("=" * 50)

        # 1. Активируем все подписки в таблице PushSubscription
        print("\n1. Активация подписок...")
        all_subscriptions = PushSubscription.query.all()

        for sub in all_subscriptions:
            sub.is_active = True
            sub.last_used = datetime.now(timezone.utc)
            print(f"  ✅ Подписка ID {sub.id} активирована")

        # 2. Связываем каждую подписку с соответствующим пользователем
        print("\n2. Проверка связей с пользователями...")

        user_ids = set([sub.user_id for sub in all_subscriptions])
        users = User.query.filter(User.id.in_(user_ids)).all()

        for user in users:
            user_subs = PushSubscription.query.filter_by(user_id=user.id).all()
            if user_subs:
                user.browser_notifications_enabled = True
                print(f"  ✅ Пользователь {user.username} (ID: {user.id}) имеет {len(user_subs)} подписок - флаг включен")
            else:
                user.browser_notifications_enabled = False
                print(f"  ❌ Пользователь {user.username} (ID: {user.id}) не имеет подписок - флаг выключен")

        # 3. Проверяем пользователей с включенным флагом, но без подписок
        print("\n3. Проверка пользователей с включенным флагом, но без подписок...")

        users_with_flag = User.query.filter_by(browser_notifications_enabled=True).all()
        for user in users_with_flag:
            user_subs = PushSubscription.query.filter_by(user_id=user.id).all()
            if not user_subs:
                user.browser_notifications_enabled = False
                print(f"  ❌ Пользователь {user.username} (ID: {user.id}) имеет включенный флаг, но не имеет подписок - флаг выключен")

        # 4. Удаление дублирующих подписок (если несколько подписок с одинаковым endpoint)
        print("\n4. Проверка дублирующих подписок...")

        # Группируем подписки по endpoint
        endpoint_to_subs = {}
        for sub in all_subscriptions:
            if sub.endpoint not in endpoint_to_subs:
                endpoint_to_subs[sub.endpoint] = []
            endpoint_to_subs[sub.endpoint].append(sub)

        # Проверяем на дубликаты
        for endpoint, subs in endpoint_to_subs.items():
            if len(subs) > 1:
                print(f"  ⚠️ Обнаружено {len(subs)} подписок с одинаковым endpoint: {endpoint[:30]}...")
                # Оставляем самую новую подписку, удаляем остальные
                sorted_subs = sorted(subs, key=lambda s: s.created_at, reverse=True)
                for sub in sorted_subs[1:]:
                    db.session.delete(sub)
                    print(f"    ❌ Удаляем дублирующую подписку ID {sub.id}")

        # 5. Проверка на подписки с пустыми полями
        print("\n5. Проверка на подписки с пустыми полями...")

        invalid_subs = PushSubscription.query.filter(
            (PushSubscription.endpoint == None) |
            (PushSubscription.endpoint == '') |
            (PushSubscription.p256dh_key == None) |
            (PushSubscription.p256dh_key == '') |
            (PushSubscription.auth_key == None) |
            (PushSubscription.auth_key == '')
        ).all()

        for sub in invalid_subs:
            db.session.delete(sub)
            print(f"  ❌ Удаляем неполную подписку ID {sub.id}")

        # 6. Адаптация FCM endpoint для совместимости
        print("\n6. Адаптация FCM endpoint для совместимости...")

        fcm_send_url = "https://fcm.googleapis.com/fcm/send/"
        wp_url = "https://fcm.googleapis.com/wp/"

        for sub in PushSubscription.query.filter(PushSubscription.endpoint.like("%fcm.googleapis.com/fcm/send/%")).all():
            old_endpoint = sub.endpoint
            token = old_endpoint[len(fcm_send_url):]
            sub.endpoint = f"{wp_url}{token}"
            print(f"  ✅ Адаптирован endpoint ID {sub.id}: '{old_endpoint[:30]}...' -> '{sub.endpoint[:30]}...'")

        # 7. Сохраняем изменения
        db.session.commit()
        print("\n✅ Все изменения сохранены в базе данных!")

        # 8. Сводка
        print("\n8. Итоговая сводка:")

        all_subscriptions = PushSubscription.query.all()
        active_subscriptions = PushSubscription.query.filter_by(is_active=True).count()
        users_with_flag = User.query.filter_by(browser_notifications_enabled=True).count()

        print(f"  📊 Всего подписок в системе: {len(all_subscriptions)}")
        print(f"  📊 Активных подписок: {active_subscriptions}")
        print(f"  📊 Пользователей с включенным флагом: {users_with_flag}")

        # 9. Конкретный пользователь
        username = input("\nВведите имя пользователя для проверки (или нажмите Enter, чтобы пропустить): ")
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                print(f"\nИнформация о пользователе {user.username}:")
                print(f"  ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  browser_notifications_enabled: {user.browser_notifications_enabled}")

                user_subs = PushSubscription.query.filter_by(user_id=user.id).all()
                print(f"  Количество подписок: {len(user_subs)}")

                for i, sub in enumerate(user_subs):
                    print(f"\n  Подписка #{i+1}:")
                    print(f"    ID: {sub.id}")
                    print(f"    Активна: {sub.is_active}")
                    print(f"    Создана: {sub.created_at}")
                    print(f"    Последнее использование: {sub.last_used}")
                    print(f"    Endpoint: {sub.endpoint[:50]}...")
                    print(f"    p256dh_key: {sub.p256dh_key[:20]}...")
                    print(f"    auth_key: {sub.auth_key[:10]}...")
            else:
                print(f"Пользователь {username} не найден")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
