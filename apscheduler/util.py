import datetime  # Полный импорт модуля datetime


def astimezone(obj):
    """
    Interprets ``obj`` as a timezone.

    :rtype: datetime.tzinfo or None
    """
    if obj is None:
        return None
    if isinstance(obj, datetime.tzinfo):  # Используем полное имя
        return obj
    if isinstance(obj, str):
        # Пытаемся использовать pytz вместо ZoneInfo
        try:
            import pytz
            return pytz.timezone(obj)
        except (ImportError, pytz.exceptions.UnknownTimeZoneError):
            # Если pytz не сработал, используем стандартный путь
            try:
                from zoneinfo import ZoneInfo
                return ZoneInfo(obj)
            except (ImportError, Exception):
                return None
    raise TypeError('Expected tzinfo, got %s instead' % obj.__class__.__name__)
