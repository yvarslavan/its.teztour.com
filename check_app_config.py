#!/usr/bin/env python
"""
Скрипт для проверки конфигурации приложения Flask с VAPID ключами
"""
import os
import sys
from flask import Flask

# Создаем простое тестовое приложение Flask
app = Flask(__name__)
app.config.from_object('blog.settings.Config')

# Проверяем VAPID ключи в конфигурации
with app.app_context():
    print("\nVAPID ключи в конфигурации приложения:")
    print("-" * 50)

    vapid_public_key = app.config.get('VAPID_PUBLIC_KEY')
    vapid_private_key = app.config.get('VAPID_PRIVATE_KEY')
    vapid_claims = app.config.get('VAPID_CLAIMS')

    if vapid_public_key:
        print(f"✅ VAPID_PUBLIC_KEY: {vapid_public_key[:10]}...{vapid_public_key[-10:]}")
    else:
        print("❌ VAPID_PUBLIC_KEY отсутствует в конфигурации")

    if vapid_private_key:
        print(f"✅ VAPID_PRIVATE_KEY: {vapid_private_key[:5]}...{vapid_private_key[-5:]}")
    else:
        print("❌ VAPID_PRIVATE_KEY отсутствует в конфигурации")

    if vapid_claims:
        print(f"✅ VAPID_CLAIMS: {vapid_claims}")
    else:
        print("❌ VAPID_CLAIMS отсутствует в конфигурации")

    print("-" * 50)

    # Проверка итогового статуса
    if all([vapid_public_key, vapid_private_key, vapid_claims]):
        print("✅ Все VAPID ключи найдены в конфигурации приложения!")
    else:
        print("❌ Не все VAPID ключи найдены в конфигурации приложения!")

    print("\nПроверка завершена!")
