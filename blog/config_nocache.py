"""
Конфигурация для отключения кэширования статических файлов
Используется для разработки
"""

from datetime import timedelta

class NoCacheConfig:
    """Конфигурация без кэширования для разработки"""

    # Отключаем кэширование статических файлов
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=0)

    # Дополнительные заголовки для отключения кэша
    CACHE_CONTROL_HEADERS = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    # Отключаем кэширование шаблонов
    TEMPLATES_AUTO_RELOAD = True

    # Включаем режим отладки
    DEBUG = True

    # Отключаем минификацию
    MINIFY_HTML = False
