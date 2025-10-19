# Исправление проблем после деплоя

## Описание проблем

После деплоя приложения на сервер возникли две основные проблемы:
1. **Bad Request - The CSRF session token is missing** на странице входа
2. **Internal Server Error** на главной странице

## Причины проблем

1. **CSRF проблема**: CSRF защита была отключена в коде для продакшена, но шаблон входа всё ещё пытался сгенерировать токен.
2. **Internal Server Error**: Неправильная конфигурация сессий в продакшене и отсутствие необходимых директорий.

## Выполненные исправления

### 1. Включение CSRF защиты

- В файле `blog/__init__.py` изменена строка 97:
  ```python
  WTF_CSRF_ENABLED=True  # Включаем CSRF защиту
  ```
- Добавлена инициализация CSRF в приложении (строка 139):
  ```python
  csrf.init_app(app)
  ```
- Удалены декораторы `@csrf.exempt` из функций входа в `blog/user/routes.py`

### 2. Настройка сессий

- В файле `wsgi.py` добавлена конфигурация для файловых сессий:
  ```python
  SESSION_TYPE='filesystem',
  SESSION_FILE_DIR='/tmp/flask_sessions',
  SESSION_PERMANENT=True,
  PERMANENT_SESSION_LIFETIME=86400,  # 24 часа
  ```
- Создан файл `.env.production` с необходимыми переменными окружения
- Создан скрипт `setup_prod_dirs.sh` для настройки директорий

## Инструкции по развертыванию исправлений

### 1. Подготовка сервера

Выполните на сервере следующие команды:

```bash
# Сделайте скрипт исполняемым
chmod +x setup_prod_dirs.sh

# Запустите скрипт для создания директорий
sudo ./setup_prod_dirs.sh
```

### 2. Развертывание изменений

1. Разместите измененные файлы на сервере через Git или другой способ:
   - `blog/__init__.py`
   - `blog/user/routes.py`
   - `wsgi.py`
   - `.env.production`
   - `setup_prod_dirs.sh`

2. Убедитесь, что файл `.env.production` находится в корне проекта и имеет правильные права:
   ```bash
   # Перейдите в директорию проекта
   cd /opt/www/its.teztour.com/

   # Установите правильные права для пользователя yvarslavan
   chown yvarslavan:yvarslavan .env.production
   chmod 600 .env.production
   ```

### 3. Перезапуск сервисов

```bash
# Перезапустите Gunicorn
sudo systemctl restart flask-helpdesk

# Проверьте статус
sudo systemctl status flask-helpdesk

# Проверьте логи
sudo journalctl -u flask-helpdesk -f
```

### 4. Проверка работоспособности

1. Проверьте главную страницу:
   ```bash
   curl -I https://its.tez-tour.com/
   ```

2. Проверьте страницу входа:
   ```bash
   curl -I https://its.tez-tour.com/login
   ```

3. Откройте сайт в браузере и проверьте функциональность

## Диагностика проблем

Если проблемы остаются:

1. **Проверьте логи ошибок:**
   ```bash
   sudo tail -f /var/log/nginx/flask-helpdesk-error.log
   ```

2. **Проверьте логи приложения:**
   ```bash
   sudo tail -f /var/www/flask_helpdesk/logs/error.log
   ```

3. **Проверьте права доступа:**
   ```bash
   ls -la /tmp/flask_sessions
   ls -la /var/www/flask_helpdesk/blog/db
   ```

4. **Проверьте конфигурацию Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Дополнительные рекомендации

1. **Используйте сильный SECRET_KEY** в `.env.production`
2. **Регулярно проверяйте логи** на наличие ошибок
3. **Настройте мониторинг** работы приложения
4. **Сделайте резервную копию** базы данных перед внесением изменений

## Контакты для поддержки

Если проблемы не решены, обратитесь к администратору системы или создайте обращение в техподдержку.
