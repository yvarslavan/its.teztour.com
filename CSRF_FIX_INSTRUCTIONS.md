# Инструкция по исправлению проблемы CSRF на сервере

## Проблема
После деплоя на Linux сервер при попытке авторизации на https://its.tez-tour.com/login возникает ошибка:
```
Bad Request
The CSRF session token is missing.
```

## Причина
Проблема связана с неправильной конфигурацией CSRF защиты в продакшн-режиме, а именно с несоответствием домена в настройках cookies.

## ВАЖНОЕ ЗАМЕЧАНИЕ
Если ваш сайт работает на поддомене (например, its.tez-tour.com), то в настройках SESSION_COOKIE_DOMAIN должен быть указан именно этот поддомен, а не основной домен.

## Решение

### 1. Проверьте переменные окружения

На сервере выполните команду:
```bash
python3 debug_csrf_server.py
```

Этот скрипт покажет текущую конфигурацию и поможет выявить проблему.

### 2. Убедитесь, что в файле `.env.production` установлены следующие переменные:

```bash
# Обязательные переменные для CSRF
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа
WTF_CSRF_ENABLED=True
FLASK_ENV=production
FLASK_DEBUG=False

# Настройки сессий
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_sessions
PERMANENT_SESSION_LIFETIME=86400

# Настройки cookies для HTTPS
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_DOMAIN=its.tez-tour.com  # ВАЖНО: укажите точный домен вашего сайта
```

### 3. Создайте директорию для сессий:

```bash
sudo mkdir -p /tmp/flask_sessions
sudo chmod 777 /tmp/flask_sessions
```

### 4. Перезапустите сервис:

```bash
sudo systemctl restart flask-helpdesk
```

### 5. Проверьте работу:

```bash
python3 debug_csrf_server.py
```

## Дополнительные шаги

Если проблема осталась:

1. **Проверьте права доступа**:
   ```bash
   ls -la /tmp/flask_session
   ```

2. **Проверьте логи сервиса**:
   ```bash
   sudo journalctl -u flask-helpdesk -f
   ```

3. **Проверьте конфигурацию Nginx**:
   Убедитесь, что Nginx правильно передает заголовки.

## Изменения в коде

Были внесены следующие изменения:

1. **Форма входа** (`blog/user/forms.py`):
   - Удален `class Meta: csrf = False`
   - Теперь форма использует глобальную настройку CSRF

2. **Шаблон входа** (`blog/templates/login.html`):
   - Упрощена обработка CSRF токена
   - Теперь используется стандартный `{{ form.hidden_tag() }}`

3. **Добавлены скрипты для отладки**:
   - `test_csrf.py` - базовый тест CSRF
   - `test_csrf_simple.py` - простой тест
   - `test_csrf_browser.py` - тест с имитацией браузера
   - `debug_csrf_server.py` - отладка на сервере

## Контакты

Если проблема не решена, обратитесь в поддержку с выводом команды:
```bash
python3 debug_csrf_server.py > debug_output.txt 2>&1
