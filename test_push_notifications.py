#!/usr/bin/env python3
"""
Тестовый скрипт для проверки браузерных пуш-уведомлений
"""

import requests
import json

def test_push_notifications():
    """Тестирование пуш-уведомлений"""

    # URL вашего приложения
    base_url = "http://localhost:5000"

    print("🔔 Тестирование браузерных пуш-уведомлений")
    print("=" * 50)

    # 1. Проверяем получение VAPID ключа
    print("1. Проверка VAPID ключа...")
    try:
        response = requests.get(f"{base_url}/api/vapid-public-key")
        if response.status_code == 200:
            vapid_data = response.json()
            print(f"✅ VAPID ключ получен: {vapid_data['publicKey'][:20]}...")
        else:
            print(f"❌ Ошибка получения VAPID ключа: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return

    # 2. Проверяем статус подписки (требует авторизации)
    print("\n2. Проверка статуса подписки...")
    try:
        response = requests.get(f"{base_url}/api/push/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Статус получен: {status_data}")
        elif response.status_code == 401:
            print("⚠️  Требуется авторизация для проверки статуса")
        else:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

    print("\n" + "=" * 50)
    print("📋 Инструкции для тестирования:")
    print("1. Откройте браузер и перейдите на http://localhost:5000")
    print("2. Авторизуйтесь в системе")
    print("3. Перейдите в профиль пользователя")
    print("4. Найдите раздел 'Браузерные уведомления'")
    print("5. Нажмите 'Включить' и разрешите уведомления")
    print("6. Нажмите 'Тест' для отправки тестового уведомления")
    print("\n🔍 Проверьте логи приложения для детальной информации")

if __name__ == "__main__":
    test_push_notifications()
