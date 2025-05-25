#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы страницы контакт-центра Москвы
"""

import requests
import sys

def test_moscow_contact_center():
    """Тестирует доступность страницы контакт-центра Москвы"""

    # URL для тестирования
    base_url = "http://localhost:5000"
    login_url = f"{base_url}/login"
    moscow_url = f"{base_url}/contact-center/moscow"

    print("🔍 Тестирование страницы контакт-центра Москвы...")

    # Создаем сессию для сохранения cookies
    session = requests.Session()

    try:
        # 1. Проверяем, что сервер запущен
        print("1. Проверка доступности сервера...")
        response = session.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Сервер доступен")
        else:
            print(f"   ❌ Сервер недоступен (код: {response.status_code})")
            return False

        # 2. Проверяем страницу логина
        print("2. Проверка страницы логина...")
        response = session.get(login_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Страница логина доступна")
        else:
            print(f"   ❌ Страница логина недоступна (код: {response.status_code})")
            return False

        # 3. Пытаемся получить доступ к странице Москвы (должен быть редирект на логин)
        print("3. Проверка страницы контакт-центра Москвы...")
        response = session.get(moscow_url, timeout=5, allow_redirects=False)

        if response.status_code == 302:
            print("   ✅ Страница защищена авторизацией (редирект на логин)")
            return True
        elif response.status_code == 200:
            print("   ⚠️  Страница доступна без авторизации")
            # Проверяем, что в ответе есть ожидаемый контент
            if "TEZ Контакт-центр | Москва" in response.text:
                print("   ✅ Содержимое страницы корректно")
                return True
            else:
                print("   ❌ Содержимое страницы некорректно")
                return False
        else:
            print(f"   ❌ Неожиданный код ответа: {response.status_code}")
            print(f"   Ответ сервера: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Не удалось подключиться к серверу")
        print("   Убедитесь, что Flask сервер запущен на localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Таймаут при подключении к серверу")
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {str(e)}")
        return False

def main():
    """Главная функция"""
    print("🚀 Запуск тестирования страницы контакт-центра Москвы")
    print("=" * 60)

    success = test_moscow_contact_center()

    print("=" * 60)
    if success:
        print("✅ Тестирование завершено успешно!")
        print("📝 Страница контакт-центра Москвы работает корректно")
        sys.exit(0)
    else:
        print("❌ Тестирование завершено с ошибками!")
        print("📝 Проверьте логи сервера для получения дополнительной информации")
        sys.exit(1)

if __name__ == "__main__":
    main()
