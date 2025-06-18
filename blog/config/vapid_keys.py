"""
Настройки VAPID ключей для push-уведомлений

ВАЖНО: 404 ошибка означает, что эти ключи НЕ СВЯЗАНЫ с FCM проектом!

Для исправления выполните следующие шаги:

1. Перейдите в https://console.firebase.google.com/
2. Создайте новый проект или выберите существующий
3. Перейдите в Project Settings (⚙️) → Cloud Messaging
4. В разделе "Web Push certificates" нажмите "Generate key pair"
5. Скопируйте полученный VAPID public key
6. Замените VAPID_PUBLIC_KEY ниже на новый ключ из Firebase
7. Перезапустите приложение Flask
8. Очистите все подписки браузера и создайте новые

ВНИМАНИЕ: После смены ключей все существующие подписки станут недействительными!
"""

# Ключи для VAPID (Voluntary Application Server Identification)
# Эти значения используются для аутентификации сервера при отправке push-уведомлений

# 🔥 ЗАМЕНИТЕ КЛЮЧИ НА ПАРУ ИЗ FIREBASE CONSOLE:
# 1. Перейдите: https://console.firebase.google.com/project/flaskhelpdesk/settings/cloudmessaging/web
# 2. В "Web Push certificates" → "Generate key pair"
# 3. Скопируйте ОБА ключа из одной пары:

# Публичный ключ из Firebase Console (Current pair)
VAPID_PUBLIC_KEY = "BKU7RR4-1Bkkjbb6TGRWVIqaT9I5z0LpZeagMa_YjiAXbR9Q4bXcd1AYUALZ0BE4BOit8Lj5fL1vRYsGo1r_eXQ"

# Приватный ключ из Firebase Console (Current pair - точная копия с модального окна)
VAPID_PRIVATE_KEY = "64ydV9qrGdwlsEpYcBAMSlwOUbf3PjtPatjghIM2Fxc"


# Данные для VAPID claims
VAPID_CLAIMS = {
    "sub": "mailto:y.varslavan@tez-tour.com",
    "aud": "https://fcm.googleapis.com"
}

# Firebase Admin SDK настройки (современный подход)
# Project ID из Firebase Console
FIREBASE_PROJECT_ID = "flaskhelpdesk"

# Service Account для Firebase Admin SDK
FIREBASE_SERVICE_ACCOUNT_PATH = "flaskhelpdesk-firebase-adminsdk-ug4ux-b719e2c246.json"
