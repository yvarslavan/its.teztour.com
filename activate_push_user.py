#!/usr/bin/env python
"""
Скрипт для активации подписок на push-уведомления для конкретного пользователя
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

        for i, sub in enumerate(user_subscriptions):
            print(f"\nПодписка #{i+1}:")
            print(f"  ID: {sub.id}")
            print(f"  Активна: {sub.is_active}")
            print(f"  Создана: {sub.created_at}")
            print(f"  Последнее использование: {sub.last_used}")
            print(f"  Endpoint: {sub.endpoint[:50]}...")

        # Активируем подписки и флаг для пользователя
        print("\nАктивация подписок...")

        user.browser_notifications_enabled = True
        print(f"✅ Флаг browser_notifications_enabled установлен в True для {user.username}")

        for sub in user_subscriptions:
            sub.is_active = True
            sub.last_used = datetime.now(timezone.utc)
            print(f"✅ Подписка ID {sub.id}: активирована")

        # Сохраняем изменения
        db.session.commit()
        print("\n✅ Изменения сохранены в базе данных!")
        print(f"\n🔔 Пользователь {user.username} теперь может получать push-уведомления!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
