# Финальное исправление проблемы CSRF на сервере

## Текущая проблема
Из логов видно, что:
- Конфигурация CSRF правильная (WTF_CSRF_ENABLED=True)
- Но CSRF токен не генерируется в HTML
- `form.hidden_tag()` не работает корректно

## Причина
Проблема в том, что `form.hidden_tag()` не генерирует CSRF токен, когда WTF_CSRF_ENABLED=True, но форма имеет `class Meta: csrf = False` (даже если мы его удалили, возможно, есть кэширование).

## Решение

### 1. Запустите скрипт исправления шаблона
На сервере выполните:
```bash
cd /opt/www/its.teztour.com/
source venv/bin/activate
python3 fix_csrf_template.py
```

Этот скрипт:
- Исправит шаблон `login.html` для явной генерации CSRF токена
- Проверит доступность `csrf_token()` в контексте шаблона
- Создаст резервную копию шаблона

### 2. Проверьте изменения в файле

Убедитесь, что в `blog/templates/login.html` теперь есть:
```html
{% if config.WTF_CSRF_ENABLED %}
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
{% else %}
    {{ form.hidden_tag() }}
{% endif %}
```

### 3. Очистите кэш шаблонов

```bash
# Удалите кэш Jinja2
sudo rm -rf /tmp/flask_sessions/*
# Или найдите кэш в директории проекта
find /opt/www/its.teztour.com -name "*.pyc" -delete
find /opt/www/its.teztour.com -name "__pycache__" -type d -exec rm -rf {} +
```

### 4. Перезапустите сервис

```bash
sudo systemctl restart flask-helpdesk
```

### 5. Проверьте работу

```bash
cd /opt/www/its.teztour.com/
source venv/bin/activate
python3 debug_csrf_server.py
```

В выводе должно быть:
```
✅ CSRF токен найден в HTML
✅ CSRF токен принят
```

### 6. Проверьте через браузер

Откройте https://its.tez-tour.com/login и:
1. Посмотрите исходный код страницы
2. Убедитесь, что есть `<input type="hidden" name="csrf_token" value="...">`
3. Попробуйте войти с любыми данными (должно быть не "CSRF session token is missing", а ошибка авторизации)

## Альтернативное решение (если первое не сработало)

Если проблема осталась, можно полностью отключить CSRF для формы входа:

1. В `blog/user/forms.py` добавьте обратно:
```python
class LoginForm(FlaskForm):
    class Meta:
        csrf = False  # Отключаем CSRF для формы логина
```

2. В шаблоне используйте только `{{ form.hidden_tag() }}`

3. Перезапустите сервис

## Почему это работает

Проблема в том, что Flask-WTF ожидает, что CSRF токен будет в сессии, но при использовании `form.hidden_tag()` он генерируется только при первом запросе. Явная генерация токена через `{{ csrf_token() }}` гарантирует, что токен будет в форме.

## Контакты

Если проблема не решена, предоставьте вывод:
```bash
python3 debug_csrf_server.py > debug_final.txt 2>&1
