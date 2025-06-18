#!/usr/bin/env python3
"""
Скрипт для очистки кэша статистики задач
"""

import requests
import json

def clear_cache():
    """Очищает кэш статистики"""
    try:
        # URL вашего Flask приложения
        base_url = "http://localhost:5000"  # Измените на ваш URL

        print("🔧 Пробуем очистить кэш через административный эндпоинт...")

        # Используем административный эндпоинт без CSRF
        response = requests.get(f"{base_url}/admin/debug/clear-cache-no-csrf")

        if response.status_code == 200:
            print("✅ Кэш успешно очищен через административный эндпоинт")
            print("   📋 Детали:")
            if 'application/json' in response.headers.get('content-type', ''):
                try:
                    result = response.json()
                    print(f"      • Пользователь: {result.get('user', 'N/A')}")
                    print(f"      • Время: {result.get('timestamp', 'N/A')}")
                    print(f"      • Сообщение: {result.get('message', 'N/A')}")
                except:
                    pass
            else:
                print("      • Ответ получен в формате HTML")
        else:
            print(f"❌ Ошибка очистки кэша: HTTP {response.status_code}")
            print(f"   Ответ: {response.text[:200]}...")

    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу")
        print("   Убедитесь, что Flask приложение запущено")
        print("   и вы авторизованы в системе через браузер")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

def manual_clear_instructions():
    """Выводит инструкции для ручной очистки"""
    print("\n" + "="*60)
    print("📖 АЛЬТЕРНАТИВНЫЕ СПОСОБЫ ОЧИСТКИ КЭША:")
    print("="*60)
    print("1. 🌐 Через браузер:")
    print("   Откройте: http://localhost:5000/admin/debug/clear-cache-no-csrf")
    print("   (требуется авторизация в системе)")
    print()
    print("2. ⏰ Автоматическая очистка:")
    print("   Кэш статистики автоматически очистится через 10 минут")
    print("   после последнего обновления")
    print()
    print("3. 🔄 Обновление страницы:")
    print("   Просто обновите страницу 'Мои задачи' через 10 минут")
    print()
    print("4. 🧪 Принудительное обновление:")
    print("   В браузере нажмите Ctrl+F5 (или Cmd+Shift+R на Mac)")
    print("   для обновления с очисткой локального кэша")

if __name__ == "__main__":
    print("🔧 Очистка кэша статистики задач...")
    clear_cache()
    manual_clear_instructions()
    print("\n💡 После очистки кэша обновите страницу 'Мои задачи' в браузере")
    print("   для проверки исправленной статистики")
