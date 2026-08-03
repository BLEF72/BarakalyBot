import logging
from datetime import datetime, timedelta

from database import Session, Order, Package, Restaurant
from config import RESERVE_MINUTES, ADMIN_IDS
from utils.helpers import gen_code, get_lang
from utils.time_utils import get_now
from texts import t

log = logging.getLogger(__name__)


def create_reservation(pkg_id: int, user_id: int, username: str) -> str:
    code = gen_code()

    stats = get_user_stats(user_id)
    with Session() as s:
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

        updated = s.query(Package).filter(
            Package.id == pkg_id,
            Package.active == True,
            Package.quantity > 0,
        ).update({Package.quantity: Package.quantity - 1}, synchronize_session=False)

        if not updated:
            raise ValueError("sold_out")

        order = Order(
            code=code, package_id=pkg_id, user_id=user_id,
            username=username, status="reserved",
            reserved_until=reserved_until,
        )
        s.add(order)
        s.commit()
    return code


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

        pkg.quantity -= 1
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
    """Статистика пользователя для рейтинга"""
    with Session() as s:
        total     = s.query(Order).filter_by(user_id=user_id).count()
        cancelled = s.query(Order).filter_by(user_id=user_id, status="cancelled").count()
        no_show   = s.query(Order).filter_by(user_id=user_id, status="expired").count()

        # Последний проблемный заказ - отмена ИЛИ неявка
        last_bad = s.query(Order).filter(
            Order.user_id == user_id,
            Order.status.in_(["cancelled", "expired"]),
        ).order_by(Order.created_at.desc()).first()

        unreliable  = cancelled + no_show
        cancel_rate = (unreliable / total * 100) if total > 0 else 0

        # Проверяем блокировку (последняя отмена/неявка менее 24 часов назад + rate > 80%)
        blocked = False
        if cancel_rate > 80 and total >= 3 and last_bad:
            hours_since = (get_now() - last_bad.created_at).total_seconds() / 3600
            if hours_since < 24:
                blocked = True

        return {
            "total":       total,
            "cancelled":   cancelled,
            "no_show":     no_show,
            "cancel_rate": cancel_rate,
            "blocked":     blocked,
        }

async def check_unblocked_users(bot):
    """Каждый час проверяем пользователей у которых истекла блокировка"""
    from utils.helpers import get_lang
    from texts import t

    with Session() as s:
        # Находим пользователей с отменами за последние 25 часов
        cutoff = get_now() - timedelta(hours=25)
        recent_cancels = s.query(Order.user_id).filter(
            Order.status.in_(["cancelled", "expired"]),
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
