import secrets

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # без 0/O, 1/I/L - их путают на слух и глаз
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

def gen_code(n: int = 6) -> str:
    """Генерирует код брони из символов, которые не путаются между собой на слух/глаз"""
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

from database import Session, Order, Package, Restaurant
from config import RESERVE_MINUTES, ADMIN_IDS
from utils.helpers import gen_code, get_lang
from utils.time_utils import get_now
from texts import t

log = logging.getLogger(__name__)


def mark_done(code: str, actor_id: int) -> str:
    """
    Отмечает заказ выданным.
    Возвращает: 'ok' | 'already' | 'not_found' | 'cancelled' | 'not_yours'
    """
    with Session() as s:
        row = (
            s.query(Order, Restaurant)
            .join(Package, Order.package_id == Package.id)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .filter(Order.code == code)
            .first()
        )
        if not row:
            return "not_found"
        order, rest = row

        if rest.owner_id != actor_id and actor_id not in ADMIN_IDS:
            return "not_yours"

        if order.status == "used":
            return "already"
        if order.status == "cancelled":
            return "cancelled"
        if order.status == "expired":
            return "expired"
        order.status       = "used"
        order.completed_at = get_now()
        buyer_id = order.user_id
        s.commit()

    from utils.helpers import log_event
    log_event("complete", buyer_id)

    return "ok"


def get_buyer_id(code: str) -> int:
    with Session() as s:
        order = s.query(Order).filter_by(code=code).first()
        return order.user_id if order else None


def get_user_orders(user_id: int, limit: int = 7):
    with Session() as s:
        rows = (
            s.query(Order, Package, Restaurant)
            .join(Package,    Order.package_id      == Package.id)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .all()
        )
        s.expunge_all()
        return rows


def get_restaurant_orders_today(restaurant_id: int):
    today = get_now().date()
    with Session() as s:
        rows = (
            s.query(Order, Package)
            .join(Package, Order.package_id == Package.id)
            .filter(
                Package.restaurant_id == restaurant_id,
                Order.created_at >= datetime(today.year, today.month, today.day),
            )
            .order_by(Order.created_at.desc())
            .all()
        )
        result = []
        for order, pkg in rows:
            s.expunge(order); s.expunge(pkg)
            result.append((order, pkg))
        return result


def count_today_orders(restaurant_id: int) -> int:
    today = get_now().date()
    with Session() as s:
        return (
            s.query(Order)
            .join(Package, Order.package_id == Package.id)
            .filter(
                Package.restaurant_id == restaurant_id,
                Order.created_at >= datetime(today.year, today.month, today.day),
            )
            .count()
        )


def get_last_orders(limit: int = 20):
    with Session() as s:
        rows = (
            s.query(Order, Package, Restaurant)
            .join(Package,    Order.package_id      == Package.id)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .all()
        )
        s.expunge_all()
        return rows


def count_all() -> int:
    with Session() as s:
        return s.query(Order).count()


def count_done() -> int:
    with Session() as s:
        return s.query(Order).filter_by(status="used").count()
    
def cancel_by_user(code: str, user_id: int) -> str:
    """
    Отмена брони покупателем.
    Возвращает: 'ok' | 'not_found' | 'not_yours' | 'too_late'
    """
    with Session() as s:
        order = s.query(Order).filter_by(code=code).first()
        if not order:
            return "not_found"
        if order.user_id != user_id:
            return "not_yours"
        if order.status == "used":
            return "too_late"
        if order.status == "cancelled":
            return "not_found"

        pkg_id = order.package_id

        # Атомарно отменяем ТОЛЬКО если статус всё ещё "reserved" - если он уже
        # успел смениться параллельно (выдан/истёк), ничего не перезаписываем
        updated = s.query(Order).filter(
            Order.code == code,
            Order.status == "reserved",
        ).update({Order.status: "cancelled"}, synchronize_session=False)

        if not updated:
            s.commit()
            return "too_late"

        s.query(Package).filter(Package.id == pkg_id).update(
            {Package.quantity: Package.quantity + 1}, synchronize_session=False
        )

        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg_name = pkg.name
            rest     = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first()
            owner_id = rest.owner_id if rest else None
            s.commit()
            return f"ok|{pkg_name}|{owner_id or ''}"

        s.commit()
        return "ok||"
    
async def notify_rating_change(bot, user_id: int):
    """Уведомляет пользователя если его рейтинг изменился критически"""
    from utils.helpers import get_lang
    from texts import t

    stats = get_user_stats(user_id)
    lang  = get_lang(user_id)

    if stats["total"] < 3:
        return

    try:
        if stats["cancel_rate"] > 80:
            await bot.send_message(
                user_id,
                t("user_blocked_warning", lang),
                parse_mode="Markdown"
            )
        elif stats["cancel_rate"] > 50:
            await bot.send_message(
                user_id,
                t("user_limited_warning", lang),
                parse_mode="Markdown"
            )
    except Exception:
        pass


async def expire_old_reservations(bot) -> int:
    """
    Планировщик: каждые 2 мин отменяет просроченные брони,
    возвращает quantity и уведомляет покупателей.
    """
    with Session() as s:
        expired = s.query(Order).filter(
            Order.status == "reserved",
            Order.reserved_until < get_now(),
        ).all()

        payload = []
        for o in expired:
            o.status = "expired"
            s.query(Package).filter(Package.id == o.package_id).update(
                {Package.quantity: Package.quantity + 1}, synchronize_session=False
            )
            payload.append((o.user_id, o.code))

        if payload:
            s.commit()

    
    for user_id, code in payload:
        try:
            lang = get_lang(user_id)
            await bot.send_message(
                user_id,
                t("reservation_expired", lang, code=code),
                parse_mode="Markdown",
            )
        except Exception:
            pass

    if payload:
        log.info(f"Expired {len(payload)} reservations")

    return len(payload)

async def send_pickup_reminders(bot):

    from database import Restaurant
    from utils.helpers import get_lang
    from texts import t

    with Session() as s:
        now           = get_now()
        reminder_time = now + timedelta(minutes=15)
        orders = s.query(Order).filter(
            Order.status == "reserved",
            Order.reserved_until <= reminder_time,
            Order.reserved_until > now,
            Order.reminder_sent == False,
        ).all()

        payload = []
        for order in orders:
            pkg  = s.query(Package).filter_by(id=order.package_id).first()
            rest = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first() if pkg else None
            if not rest:
                continue
            payload.append((
                order.id, order.user_id, order.code, rest.name,
                order.reserved_until.strftime("%H:%M"), rest.address,
            ))

    # Сетевые вызовы - без открытой транзакции
    sent_ids = []
    for order_id, user_id, code, rest_name, until_str, address in payload:
        try:
            lang = get_lang(user_id)
            await bot.send_message(
                user_id,
                t("pickup_reminder", lang, code=code, rest=rest_name,
                  until=until_str, address=address),
                parse_mode="Markdown",
            )
            sent_ids.append(order_id)
        except Exception:
            pass

    if sent_ids:
        with Session() as s:
            s.query(Order).filter(Order.id.in_(sent_ids)).update(
                {Order.reminder_sent: True}, synchronize_session=False
            )
            s.commit()
            
def create_reservation(pkg_id: int, user_id: int, username: str) -> str:
    for attempt in range(5):
        code = gen_code()
        try:
            return _create_reservation_attempt(pkg_id, user_id, username, code)
        except IntegrityError:
            continue
    raise ValueError("sold_out")


def _create_reservation_attempt(pkg_id: int, user_id: int, username: str, code: str) -> str:
    with Session() as s:
        # Проверяем блокировку и рейтинг
        stats = get_user_stats(user_id)
        if stats["blocked"]:
            days_left = 1
            if stats["unblock_at"]:
                days_left = max(1, int((stats["unblock_at"] - get_now()).total_seconds() // 86400) + 1)
            raise ValueError(f"user_blocked|{days_left}")

        # Лимит броней зависит от количества неявок за окно
        from config import NO_SHOW_CAP_THRESHOLD
        max_reservations = 1 if stats["no_show"] >= NO_SHOW_CAP_THRESHOLD else 2

        active_count = s.query(Order).filter(
            Order.user_id == user_id,
            Order.status == "reserved"
        ).count()

        if active_count >= max_reservations:
            if stats["no_show"] >= NO_SHOW_CAP_THRESHOLD:
                raise ValueError("user_limited")
            raise ValueError("max_reservations")

        pkg = s.query(Package).filter_by(id=pkg_id, active=True).first()
        if not pkg or pkg.quantity <= 0:
            raise ValueError("Package not available")

        now   = get_now()
        today = pkg.available_date or now.date()

        ph, pm     = map(int, pkg.pickup_from.split(":"))
        eh, em     = map(int, pkg.pickup_to.split(":"))
        pickup_dt  = datetime(today.year, today.month, today.day, ph, pm)
        pickup_end = datetime(today.year, today.month, today.day, eh, em)
        if pickup_end <= pickup_dt:
            # окно выдачи переходит через полночь (например, 23:00-01:00)
            pickup_end += timedelta(days=1)

        if now >= pickup_end:
            raise ValueError("pickup_closed")

        time_to_pickup = (pickup_dt - now).total_seconds()

        if time_to_pickup > 3600:
            reserved_until = pickup_dt + timedelta(minutes=30)
        else:
            reserved_until = now + timedelta(hours=1)

        # Бронь не может обещать больше времени, чем реально открыто окно выдачи
        reserved_until = min(reserved_until, pickup_end)

        updated = s.query(Package).filter(
            Package.id == pkg_id,
            Package.active == True,
            Package.quantity > 0,
        ).update({Package.quantity: Package.quantity - 1}, synchronize_session=False)

        if not updated:
            raise ValueError("sold_out")

        from config import COMMISSION_RATE
        order = Order(
            code=code,
            package_id=pkg_id,
            user_id=user_id,
            username=username,
            status="reserved",
            price=pkg.price,
            commission=round(pkg.price * COMMISSION_RATE),
            reserved_until=reserved_until,
        )
        s.add(order)
        s.commit()
    return code

def get_user_stats(user_id: int) -> dict:
    """Статистика пользователя - скользящее окно NO_SHOW_WINDOW_DAYS дней,
    блокировка зависит только от количества настоящих неявок, не отмен"""
    from config import (
        NO_SHOW_WINDOW_DAYS, NO_SHOW_BLOCK_THRESHOLD, NO_SHOW_BLOCK_DAYS,
        NO_SHOW_REVIEW_THRESHOLD, NO_SHOW_REVIEW_BLOCK_DAYS,
    )
    window_start = get_now() - timedelta(days=NO_SHOW_WINDOW_DAYS)

    with Session() as s:
        total     = s.query(Order).filter_by(user_id=user_id).count()
        cancelled = s.query(Order).filter_by(user_id=user_id, status="cancelled").count()

        no_shows = s.query(Order).filter(
            Order.user_id == user_id,
            Order.status == "expired",
            Order.created_at >= window_start,
        ).order_by(Order.created_at.desc()).all()

        no_show_count = len(no_shows)
        last_no_show  = no_shows[0] if no_shows else None
        cancel_rate   = ((cancelled + no_show_count) / total * 100) if total > 0 else 0

        blocked      = False
        block_days   = 0
        needs_review = False

        if no_show_count >= NO_SHOW_REVIEW_THRESHOLD:
            block_days, needs_review = NO_SHOW_REVIEW_BLOCK_DAYS, True
        elif no_show_count >= NO_SHOW_BLOCK_THRESHOLD:
            block_days = NO_SHOW_BLOCK_DAYS

        if block_days and last_no_show:
            days_since = (get_now() - last_no_show.created_at).total_seconds() / 86400
            if days_since < block_days:
                blocked = True

        unblock_at = None
        if blocked and last_no_show:
            unblock_at = last_no_show.created_at + timedelta(days=block_days)

        return {
            "total":        total,
            "cancelled":    cancelled,
            "no_show":      no_show_count,
            "cancel_rate":  cancel_rate,
            "blocked":      blocked,
            "needs_review": needs_review,
            "unblock_at":   unblock_at,
        }

async def check_unblocked_users(bot):
    """Каждый час: оповещает админов о пользователях, которым нужна ручная
    проверка (много неявок), и сообщает пользователю, если блокировка истекла"""
    from utils.helpers import get_lang
    from texts import t
    from config import ADMIN_IDS, NO_SHOW_WINDOW_DAYS

    with Session() as s:
        cutoff = get_now() - timedelta(days=NO_SHOW_WINDOW_DAYS)
        recent_no_shows = s.query(Order.user_id).filter(
            Order.status == "expired",
            Order.created_at >= cutoff
        ).distinct().all()

    for (user_id,) in recent_no_shows:
        stats = get_user_stats(user_id)

        if stats["needs_review"]:
            for aid in ADMIN_IDS:
                try:
                    await bot.send_message(
                        aid,
                        f"⚠️ Пользователь {user_id}: {stats['no_show']} неявок "
                        f"за {NO_SHOW_WINDOW_DAYS} дней - нужна ручная проверка."
                    )
                except Exception:
                    pass
            continue

        if not stats["blocked"] and stats["no_show"] >= 3:
            try:
                lang = get_lang(user_id)
                await bot.send_message(
                    user_id,
                    t("user_unblocked", lang),
                    parse_mode="Markdown"
                )
            except Exception:
                pass