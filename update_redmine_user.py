#!/usr/bin/env python3
"""
Скрипт для обновления флага is_redmine_user для пользователей
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import create_app
from blog.models import User
from blog.db_config import db

def update_user_redmine_flag(username, is_redmine_user=True, id_redmine_user=None):
    """Обновляет флаг is_redmine_user для указанного пользователя"""

    app = create_app()

    with app.app_context():
        try:
            # Находим пользователя
            user = User.query.filter_by(username=username).first()

            if not user:
                print(f"❌ Пользователь '{username}' не найден")
                return False

            print(f"📋 Текущие настройки пользователя '{username}':")
            print(f"   is_redmine_user: {user.is_redmine_user}")
            print(f"   id_redmine_user: {user.id_redmine_user}")

            # Обновляем флаг
            user.is_redmine_user = is_redmine_user

            if id_redmine_user is not None:
                user.id_redmine_user = id_redmine_user

            # Сохраняем изменения
            db.session.commit()

            print(f"✅ Настройки пользователя '{username}' обновлены:")
            print(f"   is_redmine_user: {user.is_redmine_user}")
            print(f"   id_redmine_user: {user.id_redmine_user}")

            return True

        except Exception as e:
            print(f"❌ Ошибка при обновлении пользователя: {e}")
            db.session.rollback()
            return False

def list_users():
    """Выводит список всех пользователей с их настройками Redmine"""

    app = create_app()

    with app.app_context():
        try:
            users = User.query.all()

            print("📋 Список пользователей:")
            print("-" * 80)
            print(f"{'Username':<20} {'is_redmine_user':<15} {'id_redmine_user':<15} {'Full Name':<30}")
            print("-" * 80)

            for user in users:
                full_name = user.full_name or "Не указано"
                print(f"{user.username:<20} {str(user.is_redmine_user):<15} {str(user.id_redmine_user):<15} {full_name:<30}")

        except Exception as e:
            print(f"❌ Ошибка при получении списка пользователей: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python update_redmine_user.py list                    - показать всех пользователей")
        print("  python update_redmine_user.py enable <username>       - включить Redmine для пользователя")
        print("  python update_redmine_user.py disable <username>      - отключить Redmine для пользователя")
        print("  python update_redmine_user.py set <username> <id>     - установить ID пользователя Redmine")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_users()

    elif command == "enable":
        if len(sys.argv) < 3:
            print("❌ Укажите имя пользователя")
            sys.exit(1)

        username = sys.argv[2]
        update_user_redmine_flag(username, True)

    elif command == "disable":
        if len(sys.argv) < 3:
            print("❌ Укажите имя пользователя")
            sys.exit(1)

        username = sys.argv[2]
        update_user_redmine_flag(username, False)

    elif command == "set":
        if len(sys.argv) < 4:
            print("❌ Укажите имя пользователя и ID Redmine")
            sys.exit(1)

        username = sys.argv[2]
        try:
            redmine_id = int(sys.argv[3])
            update_user_redmine_flag(username, True, redmine_id)
        except ValueError:
            print("❌ ID Redmine должен быть числом")
            sys.exit(1)

    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)
