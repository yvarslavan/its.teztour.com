"""
Модуль управления кэшированием для оптимизации производительности задач
"""
import json
import time
import hashlib
from typing import Optional, Dict, Any, Tuple
from functools import wraps
import threading
import weakref
from datetime import datetime, timedelta


def safe_log(level: str, message: str):
    """Безопасное логирование без требования контекста Flask приложения"""
    try:
        from flask import current_app
        if hasattr(current_app, 'logger'):
            getattr(current_app.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    except:
        print(f"[{level.upper()}] {message}")


class CacheManager:
    """Менеджер кэширования для задач пользователей"""

    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_lock = threading.RLock()
        self._max_cache_size = 100  # Максимальное количество записей в кэше
        self._default_ttl = 300  # Время жизни кэша по умолчанию (5 минут)

    def _generate_cache_key(self, user_id: int, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Генерирует ключ кэша на основе ID пользователя, эндпоинта и параметров"""
        key_data = {
            'user_id': user_id,
            'endpoint': endpoint,
            'params': params or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str, ttl: int) -> bool:
        """Проверяет валидность кэша по времени"""
        if cache_key not in self._cache_timestamps:
            return False

        timestamp = self._cache_timestamps[cache_key]
        return (time.time() - timestamp) < ttl

    def _cleanup_cache(self):
        """Очищает устаревшие записи кэша"""
        current_time = time.time()
        expired_keys = []

        for key, timestamp in self._cache_timestamps.items():
            if (current_time - timestamp) > self._default_ttl * 2:  # Двойное время для очистки
                expired_keys.append(key)

        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def _evict_lru(self):
        """Удаляет наименее недавно использованные записи при превышении лимита"""
        if len(self._cache) <= self._max_cache_size:
            return

        # Сортируем по времени и удаляем самые старые
        sorted_items = sorted(self._cache_timestamps.items(), key=lambda x: x[1])
        items_to_remove = len(self._cache) - self._max_cache_size + 10  # Удаляем 10 дополнительных

        for i in range(min(items_to_remove, len(sorted_items))):
            key = sorted_items[i][0]
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def get(self, user_id: int, endpoint: str, params: Dict[str, Any] = None, ttl: int = None) -> Optional[Any]:
        """Получает данные из кэша"""
        ttl = ttl or self._default_ttl
        cache_key = self._generate_cache_key(user_id, endpoint, params)

        with self._cache_lock:
            if self._is_cache_valid(cache_key, ttl):
                safe_log('debug', f"Cache HIT для ключа: {cache_key[:8]}...")
                return self._cache.get(cache_key)
            else:
                safe_log('debug', f"Cache MISS для ключа: {cache_key[:8]}...")
                return None

    def set(self, user_id: int, endpoint: str, data: Any, params: Dict[str, Any] = None, ttl: int = None):
        """Сохраняет данные в кэш"""
        cache_key = self._generate_cache_key(user_id, endpoint, params)

        with self._cache_lock:
            # Очистка и проверка размера кэша
            self._cleanup_cache()
            self._evict_lru()

            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = time.time()

            safe_log('debug', f"Данные сохранены в кэш для ключа: {cache_key[:8]}...")

    def invalidate_user_cache(self, user_id: int):
        """Инвалидирует весь кэш для конкретного пользователя"""
        with self._cache_lock:
            keys_to_remove = []
            for key in self._cache.keys():
                # Проверяем, принадлежит ли ключ пользователю
                try:
                    for endpoint in ['tasks', 'statistics', 'filters']:
                        test_key = self._generate_cache_key(user_id, endpoint)
                        if key.startswith(test_key[:16]):  # Проверяем префикс
                            keys_to_remove.append(key)
                            break
                except:
                    continue

            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

            safe_log('info', f"Инвалидировано {len(keys_to_remove)} записей кэша для пользователя {user_id}")

    def clear_all(self):
        """Полностью очищает весь кэш"""
        with self._cache_lock:
            entries_count = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            safe_log('info', f"Полностью очищен кэш - удалено {entries_count} записей")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        with self._cache_lock:
            return {
                'entries_count': len(self._cache),
                'oldest_entry': min(self._cache_timestamps.values()) if self._cache_timestamps else None,
                'newest_entry': max(self._cache_timestamps.values()) if self._cache_timestamps else None,
                'memory_usage_estimate': sum(len(str(data)) for data in self._cache.values())
            }


# Глобальный экземпляр менеджера кэша
cache_manager = CacheManager()


def cached_response(endpoint: str, ttl: int = 300, use_params: bool = True):
    """
    Декоратор для кэширования ответов API

    Args:
        endpoint: Название эндпоинта для кэширования
        ttl: Время жизни кэша в секундах
        use_params: Учитывать ли параметры запроса в ключе кэша
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask_login import current_user
            from flask import request

            # Пропускаем кэширование для неаутентифицированных пользователей
            if not current_user.is_authenticated:
                return func(*args, **kwargs)

            # Собираем параметры для ключа кэша
            params = {}
            if use_params:
                params.update(request.args.to_dict())
                params.update(kwargs)

            # Пытаемся получить из кэша
            cached_data = cache_manager.get(
                user_id=current_user.id,
                endpoint=endpoint,
                params=params,
                ttl=ttl
            )

            if cached_data is not None:
                return cached_data

            # Если кэша нет, выполняем функцию
            result = func(*args, **kwargs)

            # Сохраняем результат в кэш (только успешные ответы)
            if hasattr(result, 'status_code'):
                if result.status_code == 200:
                    cache_manager.set(
                        user_id=current_user.id,
                        endpoint=endpoint,
                        data=result,
                        params=params,
                        ttl=ttl
                    )
            else:
                # Для прямых возвратов данных
                cache_manager.set(
                    user_id=current_user.id,
                    endpoint=endpoint,
                    data=result,
                    params=params,
                    ttl=ttl
                )

            return result
        return wrapper
    return decorator


class TasksCacheOptimizer:
    """Специализированный оптимизатор кэша для задач"""

    def __init__(self):
        self._user_connection_cache = {}
        self._connection_timestamps = {}
        self._connection_lock = threading.RLock()
        self.CONNECTION_TTL = 1800  # 30 минут для соединений

    def cache_user_connection(self, user_id: int, redmine_connector, password: str):
        """Кэширует соединение пользователя с Redmine"""
        with self._connection_lock:
            self._user_connection_cache[user_id] = {
                'connector': redmine_connector,
                'password': password
            }
            self._connection_timestamps[user_id] = time.time()

    def get_cached_connection(self, user_id: int) -> Optional[Tuple[Any, str]]:
        """Получает кэшированное соединение пользователя"""
        with self._connection_lock:
            if user_id not in self._user_connection_cache:
                return None

            timestamp = self._connection_timestamps.get(user_id, 0)
            if (time.time() - timestamp) > self.CONNECTION_TTL:
                # Соединение устарело
                self._user_connection_cache.pop(user_id, None)
                self._connection_timestamps.pop(user_id, None)
                return None

            cached_data = self._user_connection_cache[user_id]
            return cached_data['connector'], cached_data['password']

    def invalidate_user_connection(self, user_id: int):
        """Инвалидирует кэшированное соединение пользователя"""
        with self._connection_lock:
            self._user_connection_cache.pop(user_id, None)
            self._connection_timestamps.pop(user_id, None)

    def cleanup_expired_connections(self):
        """Очищает устаревшие соединения"""
        current_time = time.time()
        expired_users = []

        with self._connection_lock:
            for user_id, timestamp in self._connection_timestamps.items():
                if (current_time - timestamp) > self.CONNECTION_TTL:
                    expired_users.append(user_id)

            for user_id in expired_users:
                self._user_connection_cache.pop(user_id, None)
                self._connection_timestamps.pop(user_id, None)


# Глобальный экземпляр оптимизатора задач
tasks_cache_optimizer = TasksCacheOptimizer()


def weekend_performance_optimizer(func):
    """
    Декоратор для оптимизации производительности в выходные дни
    Увеличивает время кэширования и снижает частоту обновлений
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from datetime import datetime

        now = datetime.now()
        is_weekend = now.weekday() >= 5  # Суббота (5) и воскресенье (6)

        if is_weekend:
            # В выходные увеличиваем время кэширования
            if hasattr(func, '__cache_ttl__'):
                func.__cache_ttl__ *= 2

            safe_log('info', "Применена оптимизация для выходных дней")

        return func(*args, **kwargs)
    return wrapper
