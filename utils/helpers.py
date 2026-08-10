import uuid
from database import Session, User, Restaurant, AnalyticsEvent
from config import ADMIN_IDS


import secrets

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def gen_code(n: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def get_lang(telegram_id: int) -> str:
    with Session() as s:
        u = s.query(User).filter_by(telegram_id=telegram_id).first()
        return u.language if u else "ru"
    
def get_owner_restaurants(uid: int):
    """Возвращает ВСЕ заведения владельца"""
    with Session() as s:
        rests = s.query(Restaurant).filter_by(owner_id=uid, active=True).all()
        for r in rests:
            s.expunge(r)
        return rests


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def is_owner(uid: int) -> bool:
    with Session() as s:
        return (
            s.query(Restaurant)
            .filter_by(owner_id=uid, active=True)
            .first() is not None
        )


def get_owner_restaurant(uid: int):
    """Возвращает Restaurant владельца, detached от сессии"""
    with Session() as s:
        r = s.query(Restaurant).filter_by(owner_id=uid, active=True).first()
        if r:
            s.expunge(r)
        return r


def log_event(event: str, user_id: int = None, district: str = None):
    """Записывает событие аналитики"""
    with Session() as s:
        s.add(AnalyticsEvent(event=event, user_id=user_id, district=district))
        s.commit()

def get_pickup_status(pickup_from: str, pickup_to: str, lang: str) -> str:
    """Возвращает статус времени выдачи для карточки пакета"""
    from datetime import datetime, date
    from texts import t

    now   = datetime.now()
    today = date.today()

    ph, pm = map(int, pickup_from.split(":"))
    eh, em = map(int, pickup_to.split(":"))

    pickup_start = datetime(today.year, today.month, today.day, ph, pm)
    pickup_end   = datetime(today.year, today.month, today.day, eh, em)

    # Уже идёт выдача
    if pickup_start <= now <= pickup_end:
        return t("time_open_now", lang, to=pickup_to)

    # До начала выдачи
    if now < pickup_start:
        diff    = pickup_start - now
        total   = int(diff.total_seconds())
        hours   = total // 3600
        mins    = (total % 3600) // 60

        if hours == 0 and mins <= 60:
            return t("time_opens_soon", lang, mins=mins)
        return t("time_opens_in", lang, hours=hours, mins=mins)

    # Выдача закончилась
    return ""

async def clear_prev_cancel(ctx, chat_id):
    """Убирает кнопку отмены с предыдущего шага диалога, чтобы на экране
    всегда была видна только одна, актуальная кнопка"""
    msg_id = ctx.user_data.pop("_cancel_msg_id", None)
    if msg_id:
        try:
            await ctx.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        except Exception:
            pass