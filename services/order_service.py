import logging
from datetime import datetime, timedelta

from database import Session, Order, Package, Restaurant
from config import RESERVE_MINUTES
from utils.helpers import gen_code, get_lang
from texts import t

from datetime import datetime, timedelta, timezone

TASHKENT = timezone(timedelta(hours=5))

def get_now():
    """Текущее время в Ташкенте"""
    return datetime.now(TASHKENT).replace(tzinfo=None)

log = logging.getLogger(__name__)


def create_reservation(pkg_id: int, user_id: int, username: str) -> str:
    from datetime import date
    code = gen_code()
    with Session() as s:
        # Проверяем блокировку и рейтинг
        stats = get_user_stats(user_id)
        if stats["blocked"]:
            raise ValueError("user_blocked")
        
        # Лимит броней зависит от рейтинга
        max_reservations = 1 if stats["cancel_rate"] > 50 and stats["total"] >= 3 else 2

        active_count = s.query(Order).filter(
            Order.user_id == user_id,
            Order.status == "reserved"
        ).count()
        if active_count >= max_reservations:
            if stats["cancel_rate"] > 50:
                raise ValueError("user_limited")
            raise ValueError("max_reservations")

        pkg = s.query(Package).filter_by(id=pkg_id, active=True).first()
        if not pkg or pkg.quantity <= 0:
            raise ValueError("Package not available")

        now   = get_now()
        today = now.date()

        ph, pm     = map(int, pkg.pickup_from.split(":"))
        eh, em     = map(int, pkg.pickup_to.split(":"))
        pickup_dt  = datetime(today.year, today.month, today.day, ph, pm)
        pickup_end = datetime(today.year, today.month, today.day, eh, em)

        time_to_pickup = (pickup_dt - now).total_seconds()

        if time_to_pickup > 3600:
            reserved_until = pickup_dt + timedelta(minutes=30)
        else:
            reserved_until = now + timedelta(hours=1)

        pkg.quantity -= 1
        order = Order(
            code=code, package_id=pkg_id, user_id=user_id,
            username=username, status="reserved",
            reserved_until=reserved_until,
        )
        s.add(order)
        s.commit()
    return code


def mark_done(code: str) -> str:
    """
    Отмечает заказ выданным.
    Возвращает: 'ok' | 'already' | 'not_found' | 'cancelled'
    """
    with Session() as s:
        order = s.query(Order).filter_by(code=code).first()
        if not order:
            return "not_found"
        if order.status == "used":
            return "already"
        if order.status == "cancelled":
            return "cancelled"
        order.status       = "used"
        order.completed_at = get_now()
        s.commit()
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

        pkg_id   = order.package_id
        order.status = "cancelled"
        s.commit()

   
        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg.quantity += 1
            rest_name = pkg.name
            owner_id  = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first()
            owner_id  = owner_id.owner_id if owner_id else None
            s.commit()
            return f"ok|{rest_name}|{owner_id or ''}"

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

        for o in expired:
            o.status = "cancelled"
            pkg = s.query(Package).filter_by(id=o.package_id).first()
            if pkg:
                pkg.quantity += 1
            try:
                lang = get_lang(o.user_id)
                await bot.send_message(
                    o.user_id,
                    t("reservation_expired", lang, code=o.code),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

        if expired:
            s.commit()
            log.info(f"Expired {len(expired)} reservations")

        return len(expired)

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

        for order in orders:
            pkg  = s.query(Package).filter_by(id=order.package_id).first()
            rest = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first() if pkg else None
            if not rest:
                continue

            try:
                lang = get_lang(order.user_id)
                await bot.send_message(
                    order.user_id,
                    t("pickup_reminder", lang,
                      code=order.code, rest=rest.name,
                      until=order.reserved_until.strftime("%H:%M"),
                      address=rest.address),
                    parse_mode="Markdown",
                )
                order.reminder_sent = True
            except Exception:
                pass

        s.commit()
def create_reservation(pkg_id: int, user_id: int, username: str) -> str:
    from datetime import date
    code = gen_code()
    with Session() as s:
        # Проверяем блокировку и рейтинг
        stats = get_user_stats(user_id)
        if stats["blocked"]:
            raise ValueError("user_blocked")

        # Лимит броней зависит от рейтинга
        max_reservations = 1 if stats["cancel_rate"] > 50 and stats["total"] >= 3 else 2

        active_count = s.query(Order).filter(
            Order.user_id == user_id,
            Order.status == "reserved"
        ).count()

        if active_count >= max_reservations:
            if stats["cancel_rate"] > 50:
                raise ValueError("user_limited")
            raise ValueError("max_reservations")

        pkg = s.query(Package).filter_by(id=pkg_id, active=True).first()
        if not pkg or pkg.quantity <= 0:
            raise ValueError("Package not available")

        now   = get_now()
        today = now.date()

        ph, pm     = map(int, pkg.pickup_from.split(":"))
        eh, em     = map(int, pkg.pickup_to.split(":"))
        pickup_dt  = datetime(today.year, today.month, today.day, ph, pm)
        pickup_end = datetime(today.year, today.month, today.day, eh, em)

        time_to_pickup = (pickup_dt - now).total_seconds()

        if time_to_pickup > 3600:
            reserved_until = pickup_dt + timedelta(minutes=30)
        else:
            reserved_until = now + timedelta(hours=1)

        pkg.quantity -= 1
        order = Order(
            code=code,
            package_id=pkg_id,
            user_id=user_id,
            username=username,
            status="reserved",
            reserved_until=reserved_until,
        )
        s.add(order)
        s.commit()
    return code

def get_user_stats(user_id: int) -> dict:
    """Статистика пользователя для рейтинга"""
    with Session() as s:
        total = s.query(Order).filter_by(user_id=user_id).count()
        cancelled = s.query(Order).filter_by(user_id=user_id, status="cancelled").count()
        
        # Последняя отмена
        last_cancel = s.query(Order).filter_by(
            user_id=user_id, status="cancelled"
        ).order_by(Order.created_at.desc()).first()
        
        cancel_rate = (cancelled / total * 100) if total > 0 else 0
        
        # Проверяем блокировку (последняя отмена менее 24 часов назад + rate > 80%)
        from datetime import date
        blocked = False
        if cancel_rate > 80 and total >= 3 and last_cancel:
            from datetime import timezone
            hours_since = (get_now() - last_cancel.created_at).total_seconds() / 3600
            if hours_since < 24:
                blocked = True
        
        return {
            "total":       total,
            "cancelled":   cancelled,
            "cancel_rate": cancel_rate,
            "blocked":     blocked,
        }

async def check_unblocked_users(bot):
    """Каждый час проверяем пользователей у которых истекла блокировка"""
    from utils.helpers import get_lang
    from texts import t

    with Session() as s:
        # Находим пользователей с отменами за последние 25 часов
        from datetime import timezone
        cutoff = get_now() - timedelta(hours=25)
        recent_cancels = s.query(Order.user_id).filter(
            Order.status == "cancelled",
            Order.created_at >= cutoff
        ).distinct().all()

        for (user_id,) in recent_cancels:
            stats = get_user_stats(user_id)
            # Если блокировка только что истекла (rate > 80% но уже 24+ часов)
            if stats["cancel_rate"] > 80 and not stats["blocked"] and stats["total"] >= 3:
                try:
                    lang = get_lang(user_id)
                    await bot.send_message(
                        user_id,
                        t("user_unblocked", lang),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
