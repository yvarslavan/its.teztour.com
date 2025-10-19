"""
Декораторы для различных утилитарных функций
"""

from functools import wraps
from flask import current_app, abort
import logging

logger = logging.getLogger(__name__)


def debug_only(f):
    """
    Декоратор, который разрешает выполнение функции только в режиме отладки.
    В продакшене возвращает ошибку 404.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.debug:
            logger.warning(f"Попытка доступа к отладочному эндпоинту {f.__name__} в продакшене")
            abort(404)  # Возвращаем 404, чтобы не раскрывать информацию о существовании эндпоинта
        return f(*args, **kwargs)
    return decorated_function


def development_only(f):
    """
    Декоратор, который разрешает выполнение функции только в окружении разработки.
    Более строгая версия debug_only, проверяющая переменные окружения.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_development = (
            current_app.debug or
            current_app.config.get('ENV') == 'development' or
            current_app.config.get('FLASK_ENV') == 'development'
        )

        if not is_development:
            logger.warning(f"Попытка доступа к эндпоинту для разработки {f.__name__} в продакшене")
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


def admin_required_in_production(f):
    """
    Декоратор, который требует прав администратора для доступа в продакшене,
    но разрешает доступ в режиме отладки.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # В режиме отладки разрешаем доступ всем
        if current_app.debug:
            return f(*args, **kwargs)

        # В продакшене проверяем права администратора
        from flask_login import current_user
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            logger.warning(f"Попытка несанкционированного доступа к эндпоинту {f.__name__} пользователем {current_user.username if current_user.is_authenticated else 'anonymous'}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
