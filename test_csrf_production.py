#!/usr/bin/env python3
"""
Скрипт для тестирования CSRF на продакшен сервере
Использование: python test_csrf_production.py
"""

import requests
from bs4 import BeautifulSoup
import sys

# Базовый URL вашего приложения
BASE_URL = "https://its.tez-tour.com"
LOGIN_URL = f"{BASE_URL}/login"

def test_csrf_production():
    """Тестирует CSRF защиту на продакшене"""

    print("="*80)
    print("🔍 Тестирование CSRF на продакшене")
    print("="*80)

    # Создаем сессию для сохранения cookies
    session = requests.Session()

    try:
        # Шаг 1: Получаем страницу логина
        print("\n📥 Шаг 1: Получение страницы логина...")
        response = session.get(LOGIN_URL, verify=True)
        print(f"✅ Статус: {response.status_code}")
        print(f"🍪 Cookies после GET: {list(session.cookies.keys())}")

        # Шаг 2: Парсим CSRF токен из HTML
        print("\n🔍 Шаг 2: Поиск CSRF токена в HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем CSRF токен в скрытом поле формы
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
            print(f"✅ CSRF токен найден в форме: {csrf_token[:20]}...")
        else:
            print("❌ CSRF токен НЕ найден в скрытом поле формы!")
            csrf_token = None

        # Ищем CSRF токен в мета-теге
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            csrf_meta_token = csrf_meta.get('content')
            print(f"✅ CSRF токен найден в meta: {csrf_meta_token[:20]}...")
        else:
            print("❌ CSRF токен НЕ найден в meta теге!")
            csrf_meta_token = None

        # Проверяем, есть ли форма логина
        login_form = soup.find('form', {'method': 'POST'})
        if login_form:
            print(f"✅ Форма логина найдена")
            print(f"   Action: {login_form.get('action', 'не указан')}")
        else:
            print("❌ Форма логина НЕ найдена!")

        # Шаг 3: Проверяем заголовки ответа
        print("\n📋 Шаг 3: Анализ заголовков ответа...")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Set-Cookie: {response.headers.get('Set-Cookie', 'нет')}")

        # Шаг 4: Пробуем отправить POST запрос с CSRF токеном
        if csrf_token:
            print("\n📤 Шаг 4: Тестовый POST запрос с CSRF токеном...")
            test_data = {
                'csrf_token': csrf_token,
                'username': 'test_user',
                'password': 'test_password',
                'remember': False
            }

            post_response = session.post(LOGIN_URL, data=test_data, verify=True)
            print(f"✅ Статус POST: {post_response.status_code}")

            if post_response.status_code == 400:
                print("❌ Получен Bad Request (400) - проблема с CSRF!")
                print(f"   Текст ошибки: {post_response.text[:500]}")
            elif post_response.status_code == 200:
                print("✅ Форма обработана (200)")
            else:
                print(f"ℹ️ Получен статус: {post_response.status_code}")
        else:
            print("\n⚠️ Шаг 4 пропущен: CSRF токен не найден")

        # Шаг 5: Диагностика сессии
        print("\n🍪 Шаг 5: Диагностика сессии и cookies...")
        for cookie in session.cookies:
            print(f"   Cookie: {cookie.name}")
            print(f"     - Value: {cookie.value[:30]}...")
            print(f"     - Domain: {cookie.domain}")
            print(f"     - Path: {cookie.path}")
            print(f"     - Secure: {cookie.secure}")
            print(f"     - HttpOnly: {cookie.has_nonstandard_attr('HttpOnly')}")

        # Итоговый вывод
        print("\n" + "="*80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("="*80)

        issues = []
        if not csrf_token and not csrf_meta_token:
            issues.append("❌ CSRF токен отсутствует в HTML")
        else:
            print("✅ CSRF токен присутствует в HTML")

        if not login_form:
            issues.append("❌ Форма логина не найдена")
        else:
            print("✅ Форма логина найдена")

        if not session.cookies:
            issues.append("❌ Cookies не установлены")
        else:
            print(f"✅ Cookies установлены: {len(session.cookies)} шт.")

        if issues:
            print("\n⚠️ Обнаружены проблемы:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ Базовые проверки пройдены")

        print("\n💡 Рекомендации:")
        print("  1. Проверьте логи сервера на наличие ошибок CSRF")
        print("  2. Убедитесь, что WTF_CSRF_ENABLED=True в продакшене")
        print("  3. Проверьте настройки SESSION_COOKIE_DOMAIN")
        print("  4. Проверьте, что приложение работает за HTTPS")
        print("  5. Убедитесь, что SECRET_KEY установлен корректно")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Ошибка подключения: {e}")
        print("   Проверьте доступность сервера и VPN соединение")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "="*80)
    return 0

if __name__ == "__main__":
    sys.exit(test_csrf_production())
