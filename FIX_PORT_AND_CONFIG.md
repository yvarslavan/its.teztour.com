# Исправление проблем с портом и конфигурацией

## Проблемы которые мы обнаружили

Из вашего лога видно две проблемы:

### 1. Приложение загружает `.env.development` вместо `.env` ❌

```
✅ Загружены переменные окружения из .env.development (режим: development)
```

**Проблема:** `.env.development` содержит `MYSQL_HOST=127.0.0.1` (порт-прокси Windows), а нужен `helpdesk.teztour.com`

**Решение:** Исправлен `app.py` - теперь автоматически определяет WSL и использует правильный `.env`

### 2. Порт 5000 занят ❌

```
Address already in use
Port 5000 is in use by another program.
```

**Решение:** Остановить старый процесс

## Применение исправлений

### Шаг 1: Остановить старый процесс Flask

```bash
# Найти процесс на порту 5000
lsof -i :5000

# Или найти все процессы Python
ps aux | grep python | grep app.py

# Остановить процесс (замените PID на номер процесса)
kill <PID>

# Или остановить все процессы Flask
pkill -f "python.*app.py"
```

### Шаг 2: Проверить конфигурацию

```bash
# Убедитесь что .env содержит правильные хосты
grep -E "MYSQL.*HOST" .env

# Должно быть:
# MYSQL_HOST=helpdesk.teztour.com
# MYSQL_QUALITY_HOST=quality.teztour.com
```

Если конфигурация неправильная, пересоздайте её:

```bash
python3 setup_wsl_config.py
```

### Шаг 3: Запустить приложение

```bash
python3 app.py
```

Теперь вы должны увидеть:

```
✅ Загружены переменные окружения из .env (режим: development) [WSL detected]
```

И больше не будет ошибок `Lost connection to MySQL server`!

## Проверка что всё работает

После запуска проверьте логи:

1. ✅ Должно быть: `[WSL detected]` - WSL определен
2. ✅ Должно быть: `из .env` - используется правильный файл
3. ✅ НЕ должно быть ошибок `(2013, 'Lost connection to MySQL server during query')`

## Если порт 5000 всё ещё занят

Запустите на другом порту:

```bash
# Вариант 1: Указать порт явно
flask run --port 5001

# Вариант 2: Изменить в app.py
# Найдите строку app.run(..., port=5000)
# Измените на app.run(..., port=5001)
```

## Альтернатива: Удалить .env.development

Если вы работаете только в WSL, можно удалить `.env.development`:

```bash
# Сделать резервную копию
cp .env.development .env.development.backup

# Удалить
rm .env.development
```

Теперь `app.py` всегда будет использовать `.env`.

## Что изменилось в app.py

Добавлено автоматическое определение WSL:

```python
# Проверяем что мы в WSL
is_wsl = False
try:
    with open('/proc/version', 'r') as f:
        is_wsl = 'microsoft' in f.read().lower()
except:
    pass

# В WSL всегда используем .env (создается setup_wsl_config.py)
if is_wsl and (BASE_DIR / ".env").exists():
    env_path = BASE_DIR / ".env"
else:
    env_path = BASE_DIR / ".env.development"
```

Это означает:
- **В WSL**: используется `.env` (с правильными хостами VPN)
- **В Windows**: используется `.env.development` (с порт-прокси)

