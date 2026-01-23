# Gunicorn configuration file
# Используется для production запуска

# Привязка к сокету
bind = "unix:/run/its-teztour/gunicorn.sock"

# Количество воркеров
workers = 3

# Таймаут воркера (в секундах)
# Увеличен для обработки медленных Oracle подключений
timeout = 120

# Graceful timeout
graceful_timeout = 30

# Keep-alive
keepalive = 5

# Логирование
accesslog = None
errorlog = "-"
loglevel = "info"

# Preload приложение для экономии памяти
preload_app = False

# Максимальное количество запросов перед перезапуском воркера
max_requests = 1000
max_requests_jitter = 50
