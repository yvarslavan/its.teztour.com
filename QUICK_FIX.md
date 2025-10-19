# Быстрое исправление CSRF проблемы

## Краткое описание проблемы
После деплоя на https://its.tez-tour.com/ возникает ошибка:
- **"Bad Request: The CSRF session token is missing"** при попытке авторизации

## Что было исправлено

### 1. В файле `blog/__init__.py` (строки 88-101):

**Было:**
```python
SESSION_COOKIE_DOMAIN='its.tez-tour.com',  # БЕЗ точки
WTF_CSRF_ENABLED=True
```

**Стало:**
```python
SESSION_COOKIE_DOMAIN='.tez-tour.com',  # С ТОЧКОЙ в начале
WTF_CSRF_ENABLED=True,
WTF_CSRF_TIME_LIMIT=None,  # Отключаем ограничение времени
WTF_CSRF_SSL_STRICT=False  # Отключаем строгую проверку SSL
```

### 2. Добавлена отладка CSRF в `blog/user/routes.py`

Детальное логирование при POST запросе на /login для диагностики проблем.

## Что нужно сделать на сервере

### Минимальный набор команд:

```bash
# 1. Подключитесь к серверу
ssh user@its.tez-tour.com

# 2. Перейдите в директорию проекта
cd /path/to/its.teztour.com

# 3. Обновите код
git pull origin main

# 4. Создайте директорию для сессий (если нет)
sudo mkdir -p /tmp/flask_sessions
sudo chmod 777 /tmp/flask_sessions

# 5. Перезапустите приложение
sudo systemctl restart flask-helpdesk.service

# 6. Проверьте логи
sudo journalctl -u flask-helpdesk.service -f
```

### Что должно быть в логах:

```
✅ [INIT] Продакшен режим активен - настройки безопасности применены
🔒 [INIT] CSRF Protection: WTF_CSRF_ENABLED = True
🔒 [INIT] CSRF Time Limit: None
🔒 [INIT] CSRF SSL Strict: False
```

## Проверка работы

### Вариант 1: Через браузер
1. Откройте https://its.tez-tour.com/login
2. Нажмите F12 (Developer Tools)
3. Проверьте наличие cookie `helpdesk_session` в Application -> Cookies
4. Попробуйте авторизоваться

### Вариант 2: Через скрипт
```bash
# С локальной машины
python test_csrf_production.py
```

### Вариант 3: API эндпоинт
```bash
curl https://its.tez-tour.com/session_debug
```

## Если не помогло

### 1. Проверьте переменные окружения

```bash
cat .env.production
```

Должно быть:
```
WTF_CSRF_ENABLED=True
SESSION_COOKIE_DOMAIN=.tez-tour.com
SECRET_KEY=<какой-то-секретный-ключ>
```

### 2. Проверьте права на директорию сессий

```bash
ls -la /tmp/flask_sessions
```

Должна быть доступна для записи.

### 3. Проверьте конфигурацию nginx

```bash
sudo cat /etc/nginx/sites-available/its.tez-tour.com
```

Должны быть заголовки:
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host $host;
```

## Откат (если нужен)

```bash
# Если вы сделали backup
sudo cp blog/__init__.py.backup blog/__init__.py
sudo systemctl restart flask-helpdesk.service

# Или через git
git revert HEAD
sudo systemctl restart flask-helpdesk.service
```

## Контакты
- Email: help@tez-tour.com
- Подробная документация: см. `CSRF_SOLUTION.md`
- Чек-лист развертывания: см. `DEPLOYMENT_CHECKLIST.md`

---
**Время выполнения:** 5-10 минут
**Требуется перезагрузка:** Да
**Простой сервиса:** ~10-30 секунд
