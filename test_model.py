#!/usr/bin/env python3
"""
Тестовый скрипт для проверки модели User
"""

from blog import create_app
from blog.models import User
from blog import db

def test_user_model():
    """Тестирует модель User на наличие атрибута notifications_widget_enabled"""
    try:
        app = create_app()
        with app.app_context():
            # Проверяем, есть ли атрибут в модели
            if hasattr(User, 'notifications_widget_enabled'):
                print("✅ Атрибут notifications_widget_enabled найден в модели User")
                print(f"   Тип: {type(User.notifications_widget_enabled)}")
                print(f"   Значение: {User.notifications_widget_enabled}")
            else:
                print("❌ Атрибут notifications_widget_enabled НЕ найден в модели User")

            # Проверяем все атрибуты модели
            print("\n📋 Все атрибуты модели User:")
            for attr in dir(User):
                if not attr.startswith('_') and not callable(getattr(User, attr)):
                    print(f"   {attr}")

            # Проверяем, есть ли столбец в базе данных
            try:
                user = User.query.first()
                if user:
                    print(f"\n✅ Пользователь найден: {user.username}")
                    if hasattr(user, 'notifications_widget_enabled'):
                        print(f"   notifications_widget_enabled = {user.notifications_widget_enabled}")
                    else:
                        print("❌ У объекта пользователя нет атрибута notifications_widget_enabled")
                else:
                    print("❌ Пользователи не найдены в базе данных")
            except Exception as e:
                print(f"❌ Ошибка при запросе пользователя: {e}")

    except Exception as e:
        print(f"❌ Ошибка при создании приложения: {e}")

if __name__ == "__main__":
    test_user_model()
