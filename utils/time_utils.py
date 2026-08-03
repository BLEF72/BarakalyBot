from datetime import datetime, timezone, timedelta

TASHKENT = timezone(timedelta(hours=5))


def get_now():
    """Текущее время в Ташкенте (наивный datetime, единый для всего проекта)"""
    return datetime.now(TASHKENT).replace(tzinfo=None)