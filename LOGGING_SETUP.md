# Настройка логирования в production

## 📋 Обзор проблемы

Серверное дисковое пространство заполнялось логами критически быстро из-за:
- Отсутствия ротации для `app_err.log`
- Избыточного логирования на уровне INFO в часто вызываемых функциях
- Принудительной установки DEBUG уровня в некоторых модулях
- Дублирования логгеров в разных файлах
- Множественных лог-файлов с перекрывающейся функциональностью

## 🔧 Выполненные исправления

### 1. Централизация логирования
- **Файл:** `blog/utils/logger.py` - единая точка настройки логирования
- **Удалено дублирование:** `app.py` теперь использует только `configure_blog_logger()`
- **Консолидированы файлы:** `wsgi.py` пишет в `logs/app.log` вместо `flask_debug.log`

### 2. Добавлена ротация для всех лог-файлов

| Файл | Макс. размер | Бэкапов | Итого макс. |
|------|-------------|---------|-------------|
| `logs/app.log` | 10 MB | 7 | 80 MB |
| `logs/stat.log` | 5 MB | 3 | 20 MB |
| `logs/error.log` | 10 MB | 5 | 60 MB |

### 3. Убрано избыточное логирование
- Удалены вызовы `logger.setLevel(logging.DEBUG)` в `blog/call/routes.py`
- Функция `write_log()` теперь использует DEBUG уровень по умолчанию
- Консольный вывод отключён в production режиме

### 4. Переменные окружения для настройки

```bash
# Основной уровень логирования
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR/CRITICAL

# Основной лог app.log
LOG_MAX_BYTES=10485760      # 10 MB
LOG_BACKUP_COUNT=7          # 7 архивных файлов

# Лог статистики звонков stat.log
STAT_LOG_MAX_BYTES=5242880      # 5 MB
STAT_LOG_BACKUP_COUNT=3         # 3 архивных файла

# Лог ошибок error.log (app_err.log)
ERROR_LOG_MAX_BYTES=10485760    # 10 MB
ERROR_LOG_BACKUP_COUNT=5        # 5 архивных файлов
```

## 📊 Рекомендуемая конфигурация для production

### Минимальное логирование (экономия места)
```bash
LOG_LEVEL=WARNING
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```
**Максимальный размер:** ~50 MB

### Стандартное логирование (баланс)
```bash
LOG_LEVEL=INFO
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=7
```
**Максимальный размер:** ~80 MB

### Расширенное логирование (отладка проблем)
```bash
LOG_LEVEL=DEBUG
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10
```
**Максимальный размер:** ~110 MB

## 🔍 Мониторинг заполнения логов

### Проверка размера логов
```bash
# Linux/Mac
du -sh logs/*
ls -lh logs/

# Windows PowerShell
Get-ChildItem logs\ | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
```

### Просмотр последних ошибок
```bash
# Последние 100 строк лога ошибок
tail -100 logs/error.log

# Поиск ошибок за сегодня
grep "$(date +%Y-%m-%d)" logs/app.log | grep ERROR
```

## 📁 Структура лог-файлов

```
logs/
├── app.log              # Основное приложение + werkzeug
├── app.log.1            # Архив 1
├── app.log.2            # Архив 2
├── ...
├── stat.log             # Статистика звонков (только INFO)
├── stat.log.1           # Архив статистики
├── ...
├── error.log            # Только ошибки (ERROR+)
└── error.log.1          # Архив ошибок
```

## ⚙️ Настройка logrotate (Linux)

Для дополнительной защиты от заполнения диска рекомендуется настроить системный logrotate:

`/etc/logrotate.d/flask-helpdesk`:
```
/path/to/project/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload flask-helpdesk > /dev/null 2>&1 || true
    endscript
}
```

## 🚀 Развёртывание изменений

### 1. Обновление переменных окружения
```bash
# Production сервер
export LOG_LEVEL=INFO
export LOG_MAX_BYTES=10485760
export LOG_BACKUP_COUNT=7
export STAT_LOG_MAX_BYTES=5242880
export STAT_LOG_BACKUP_COUNT=3
export ERROR_LOG_MAX_BYTES=10485760
export ERROR_LOG_BACKUP_COUNT=5
```

### 2. Перезапуск приложения
```bash
# Systemd
sudo systemctl restart flask-helpdesk

# Или для WSGI
sudo systemctl restart nginx
sudo systemctl restart uwsgi
```

### 3. Очистка старых логов (при необходимости)
```bash
# Удалить файлы старше 30 дней
find logs/ -name "*.log.*" -mtime +30 -delete

# Архивировать текущие логи
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

## 📈 Ожидаемый результат

| До оптимизации | После оптимизации |
|---------------|-------------------|
| ~1 GB/день | ~50-100 MB/день |
| Нет ротации | Автоматическая ротация |
| DEBUG в production | INFO в production |
| 5+ лог-файлов | 3 лог-файла |

## 🔧 Отладка проблем с логированием

### Включить подробное логирование временно
```bash
# Без перезапуска (если поддерживается)
export LOG_LEVEL=DEBUG

# С перезапуском
export LOG_LEVEL=DEBUG
sudo systemctl restart flask-helpdesk
```

### Проверка работы ротации
```python
# Тестовый скрипт
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/test.log', maxBytes=1024, backupCount=3)
logger = logging.getLogger('test')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

for i in range(1000):
    logger.info(f"Test message {i}" * 100)
```

## 📝 Примечания

1. **Не используйте DEBUG в production** - это приводит к быстрому заполнению диска
2. **Мониторьте место на диске** - настройте алерты при 80% заполнении
3. **Централизуйте логи** - рассмотрите отправку в ELK/Splunk для production
4. **Регулярная архивация** - настройте ежедневную архивацию старых логов
