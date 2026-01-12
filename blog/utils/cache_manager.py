"""
Enhanced cache manager for performance optimization
"""
import time
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from functools import wraps
from flask import g
try:
    import redis
except ImportError:
    redis = None
from threading import Lock

logger = logging.getLogger(__name__)

class CacheManager:
    """Enhanced cache manager with Redis backend and fallback to memory cache"""

    def __init__(self, redis_url: str = None, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_locks = {}
        self.lock = Lock()

        # Try to connect to Redis
        self.redis_client = None
        if redis_url and redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                logger.warning("⚠️ Redis connection failed, using memory cache: %s", e)
                self.redis_client = None

    def _generate_key(self, key: str, namespace: str = None) -> str:
        """Generate a cache key with optional namespace"""
        if namespace:
            key = f"{namespace}:{key}"

        # Hash long keys to avoid Redis key length limits
        if len(key) > 250:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"hash:{key_hash}"

        return key

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            logger.error("❌ Failed to serialize cache value: %s", e)
            return json.dumps(str(value))

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage"""
        try:
            return json.loads(value)
        except (TypeError, ValueError) as e:
            logger.error("❌ Failed to deserialize cache value: %s", e)
            return value

    def get(self, key: str, namespace: str = None) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(key, namespace)

        try:
            if self.redis_client:
                value = self.redis_client.get(cache_key)
                if value:
                    return self._deserialize_value(value)
            else:
                # Fallback to memory cache
                with self.lock:
                    if cache_key in self.memory_cache:
                        cached_item = self.memory_cache[cache_key]
                        if time.time() < cached_item['expires']:
                            return cached_item['value']
                        else:
                            # Expired, remove it
                            del self.memory_cache[cache_key]

            return None

        except Exception as e:
            logger.error("❌ Cache get error for key %s: %s", cache_key, e)
            return None

    def set(self, key: str, value: Any, ttl: int = None, namespace: str = None) -> bool:
        """Set value in cache"""
        cache_key = self._generate_key(key, namespace)
        ttl = ttl or self.default_ttl

        try:
            serialized_value = self._serialize_value(value)

            if self.redis_client:
                return self.redis_client.setex(cache_key, ttl, serialized_value)
            else:
                # Fallback to memory cache
                with self.lock:
                    self.memory_cache[cache_key] = {
                        'value': value,
                        'expires': time.time() + ttl
                    }
                return True

        except Exception as e:
            logger.error("❌ Cache set error for key %s: %s", cache_key, e)
            return False

    def delete(self, key: str, namespace: str = None) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(key, namespace)

        try:
            if self.redis_client:
                return bool(self.redis_client.delete(cache_key))
            else:
                # Fallback to memory cache
                with self.lock:
                    if cache_key in self.memory_cache:
                        del self.memory_cache[cache_key]
                        return True
                return False

        except Exception as e:
            logger.error("❌ Cache delete error for key %s: %s", cache_key, e)
            return False

    def exists(self, key: str, namespace: str = None) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(key, namespace)

        try:
            if self.redis_client:
                return bool(self.redis_client.exists(cache_key))
            else:
                # Fallback to memory cache
                with self.lock:
                    if cache_key in self.memory_cache:
                        cached_item = self.memory_cache[cache_key]
                        if time.time() < cached_item['expires']:
                            return True
                        else:
                            # Expired, remove it
                            del self.memory_cache[cache_key]
                return False

        except Exception as e:
            logger.error("❌ Cache exists error for key %s: %s", cache_key, e)
            return False

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        try:
            if self.redis_client:
                pattern = f"{namespace}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Fallback to memory cache
                with self.lock:
                    keys_to_delete = [
                        key for key in self.memory_cache.keys()
                        if key.startswith(f"{namespace}:")
                    ]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                    return len(keys_to_delete)

        except Exception as e:
            logger.error("❌ Cache clear namespace error for %s: %s", namespace, e)
            return 0

    def get_or_set(self, key: str, func, ttl: int = None, namespace: str = None) -> Any:
        """Get value from cache or set it using function"""
        cached_value = self.get(key, namespace)
        if cached_value is not None:
            return cached_value

        # Value not in cache, compute it
        try:
            value = func()
            self.set(key, value, ttl, namespace)
            return value
        except Exception as e:
            logger.error("❌ Error in get_or_set for key %s: %s", key, e)
            raise

    def invalidate_pattern(self, pattern: str, namespace: str = None) -> int:
        """Invalidate keys matching pattern"""
        try:
            if self.redis_client:
                search_pattern = f"{namespace}:{pattern}" if namespace else pattern
                keys = self.redis_client.keys(search_pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Fallback to memory cache
                with self.lock:
                    keys_to_delete = []
                    for key in self.memory_cache.keys():
                        if namespace and not key.startswith(f"{namespace}:"):
                            continue
                        if pattern in key:
                            keys_to_delete.append(key)

                    for key in keys_to_delete:
                        del self.memory_cache[key]
                    return len(keys_to_delete)

        except Exception as e:
            logger.error("❌ Cache invalidate pattern error for %s: %s", pattern, e)
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'backend': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            else:
                with self.lock:
                    return {
                        'backend': 'memory',
                        'total_keys': len(self.memory_cache),
                        'memory_usage': f"{len(str(self.memory_cache))} bytes"
                    }

        except Exception as e:
            logger.error("❌ Cache stats error: %s", e)
            return {'error': str(e)}

    def health_check(self) -> bool:
        """Check cache health"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
            else:
                # Memory cache is always "healthy"
                return True
        except Exception as e:
            logger.error("❌ Cache health check failed: %s", e)
            return False

# Cache decorator
def cached(ttl: int = 300, namespace: str = None, key_func=None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Get cache manager from app context
            cache_mgr = getattr(g, 'cache_manager', None)
            if not cache_mgr:
                cache_mgr = CacheManager()
                g.cache_manager = cache_mgr

            # Try to get from cache
            cached_result = cache_mgr.get(cache_key, namespace)
            if cached_result is not None:
                logger.debug("📦 Cache hit for %s", func.__name__)
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_mgr.set(cache_key, result, ttl, namespace)
            logger.debug("💾 Cached result for %s", func.__name__)

            return result

        return wrapper
    return decorator

# Global cache manager instance
cache_manager = CacheManager()

# Legacy classes for backward compatibility
class TasksCacheOptimizer:
    """Legacy cache optimizer for tasks - placeholder for backward compatibility"""
    def __init__(self):
        self.cache_manager = cache_manager

    def get_cached_tasks(self, user_id, *args, **kwargs):
        """Get cached tasks for user"""
        return self.cache_manager.get(f"tasks_{user_id}", namespace="tasks")

    def cache_tasks(self, user_id, tasks, ttl=300):
        """Cache tasks for user"""
        return self.cache_manager.set(f"tasks_{user_id}", tasks, ttl, namespace="tasks")

def cached_response(func):
    """Legacy decorator for cached responses"""
    return cached(ttl=300)(func)

def weekend_performance_optimizer(func=None):
    """Legacy weekend performance optimizer - decorator for backward compatibility"""
    if func is None:
        # Called as decorator without arguments
        def decorator(f):
            return cached(ttl=300)(f)
        return decorator
    else:
        # Called as decorator with function
        return cached(ttl=300)(func)

# Create instance for backward compatibility
tasks_cache_optimizer = TasksCacheOptimizer()

# Cache key generators
def user_cache_key(user_id: int, *args) -> str:
    """Generate cache key for user-specific data"""
    return f"user_{user_id}_{'_'.join(str(arg) for arg in args)}"

def api_cache_key(endpoint: str, **params) -> str:
    """Generate cache key for API responses"""
    param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
    return f"api_{endpoint}_{param_str}"

def database_cache_key(table: str, **conditions) -> str:
    """Generate cache key for database queries"""
    condition_str = "_".join(f"{k}_{v}" for k, v in sorted(conditions.items()))
    return f"db_{table}_{condition_str}"
