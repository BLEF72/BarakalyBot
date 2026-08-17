from datetime import datetime, timedelta
import logging
from utils.time_utils import get_now
from texts import md_escape
from database import Session, Package, Restaurant
from utils.helpers import get_lang

log = logging.getLogger(__name__)


def get_available(district: str = None):
    with Session() as s:
        today = get_now().date()
        q = (
            s.query(Package, Restaurant)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .filter(Package.active == True, Package.quantity > 0, Restaurant.active == True,
                    Package.available_date == today)
        )
        if district and district != "ALL":
            q = q.filter(Restaurant.district == district)
        rows = q.all()
        result = []
        for pkg, rest in rows:
            # Копируем данные вместо expunge
            result.append((pkg, rest))
        s.expunge_all()
        return result

def get_by_restaurant(restaurant_id: int):
    with Session() as s:
        pkgs = s.query(Package).filter_by(restaurant_id=restaurant_id, active=True).all()
        for p in pkgs:
            s.expunge(p)
        return pkgs


def create_package(restaurant_id: int, name: str, photo_file_id: str,
                   price: int, quantity: int, pickup_from: str, pickup_to: str) -> Package:
    with Session() as s:
        pkg = Package(
            restaurant_id=restaurant_id,
            name=name,
            photo_file_id=photo_file_id,
            price=price,
            quantity=quantity,
            pickup_from=pickup_from,
            pickup_to=pickup_to,
            available_date=get_now().date(),
            active=True,
        )
        s.add(pkg)
        s.commit()
        s.refresh(pkg)
        s.expunge(pkg)
        return pkg


def get_all_active():
    with Session() as s:
        today = get_now().date()
        rows = (
            s.query(Package, Restaurant)
            .join(Restaurant)
            .filter(Package.active == True, Package.available_date == today)
            .all()
        )
        result = []
        for pkg, rest in rows:
            s.expunge(pkg); s.expunge(rest)
            result.append((pkg, rest))
        return result


def count_active() -> int:
    with Session() as s:
        today = get_now().date()
        return (
            s.query(Package)
            .filter(Package.active == True, Package.available_date == today)
            .count()
        )


async def nightly_cleanup(bot):
    """Планировщик: деактивирует все вчерашние и более старые пакеты,
    независимо от остатка - "протухшие" листинги не должны воскресать"""
    with Session() as s:
        today = get_now().date()
        old = s.query(Package).filter(
            Package.available_date < today,
            Package.active == True,
        ).all()
        for p in old:
            p.active = False
        if old:
            s.commit()
            log.info(f"Deactivated {len(old)} stale packages")

def update_price(pkg_id: int, price: int):
    with Session() as s:
        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg.price = price
            s.commit()


def update_quantity(pkg_id: int, quantity: int):
    with Session() as s:
        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg.quantity = quantity
            s.commit()


def deactivate(pkg_id: int):
    with Session() as s:
        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg.active = False
            s.commit()

def search(query: str):
    """Поиск пакетов и заведений по названию"""
    with Session() as s:
        search_term = f"%{query.lower()}%"
        rows = (
            s.query(Package, Restaurant)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .filter(
                Package.active == True,
                Package.quantity > 0,
                Restaurant.active == True,
            )
            .filter(
                (Package.name.ilike(search_term)) |
                (Restaurant.name.ilike(search_term))
            )
            .all()
        )
        s.expunge_all()
        return rows
            
async def post_to_channel(bot, pkg, rest, rating):
    """Постим новый пакет в канал"""
    from config import CHANNEL_ID
    from texts import t
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from services.review_service import get_review_count

    try:
        rating_display = rating if rating is not None else "Новое"
        text = t("channel_post", "ru",
                 rest=rest.name, address=rest.address, district=rest.district,
                 rating=rating_display, name=pkg.name, price=pkg.price,
                 qty=pkg.quantity, from_=pkg.pickup_from, to=pkg.pickup_to)

        bot_username = bot.username
        deep_link_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🛒 Забронировать", url=f"https://t.me/{bot_username}?start=pkg_{pkg.id}")
        ]])

        photo = pkg.photo_file_id or rest.photo_file_id

        if photo:
            await bot.send_photo(
                CHANNEL_ID, photo,
                caption=text, parse_mode="Markdown", reply_markup=deep_link_kb
            )
        else:
            await bot.send_message(
                CHANNEL_ID, text, parse_mode="Markdown", reply_markup=deep_link_kb
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Channel post error: {e}")
        

def update_time(pkg_id: int, pickup_from: str, pickup_to: str):
    with Session() as s:
        pkg = s.query(Package).filter_by(id=pkg_id).first()
        if pkg:
            pkg.pickup_from = pickup_from
            pkg.pickup_to   = pickup_to
            s.commit()
            
def close_restaurant(restaurant_id: int):
    """Деактивирует все пакеты заведения на сегодня"""
    with Session() as s:
        rest = s.query(Restaurant).filter_by(id=restaurant_id).first()
        if rest:
            rest.is_closed = True
            pkgs = s.query(Package).filter_by(restaurant_id=restaurant_id, active=True).all()
            for pkg in pkgs:
                pkg.active = False
            s.commit()


def open_restaurant(restaurant_id: int):
    """Активирует заведение и его пакеты"""
    with Session() as s:
        rest = s.query(Restaurant).filter_by(id=restaurant_id).first()
        if rest:
            rest.is_closed = False
            pkgs = s.query(Package).filter_by(restaurant_id=restaurant_id).all()
            for pkg in pkgs:
                pkg.active = True
            s.commit()


async def auto_open_restaurants(bot):
    """Каждое утро в 06:00 автоматически открывает закрытые заведения"""
    from utils.helpers import get_lang
    from texts import t
    from config import ADMIN_IDS

    with Session() as s:
        today = get_now().date()
        closed = s.query(Restaurant).filter_by(is_closed=True, active=True).all()

        payload = []
        for rest in closed:
            rest.is_closed = False
            pkgs = s.query(Package).filter_by(
                restaurant_id=rest.id, available_date=today
            ).all()
            for pkg in pkgs:
                pkg.active = True
            if rest.owner_id:
                payload.append((rest.owner_id, rest.name))

        if closed:
            s.commit()

    for owner_id, rest_name in payload:
        try:
            lang = get_lang(owner_id)
            safe_name = md_escape(rest_name)
            await bot.send_message(
                owner_id,
                "🟢 " + (f"*{safe_name}* автоматически открыто!" if lang == "ru"
                         else f"*{safe_name}* avtomatik ochildi!"),
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def notify_subscribers(bot, subscribers, rest_name, pkg_name, price, qty, pfrom, pto, address):
    import asyncio
    from telegram.error import RetryAfter, Forbidden
    from utils.helpers import get_lang
    from texts import t

    for user_id in subscribers:
        try:
            user_lang = get_lang(user_id)
            msg = t("new_pkg_notify", user_lang,
                    rest=rest_name, name=pkg_name,
                    price=price, qty=qty,
                    from_=pfrom, to=pto, address=address)
            await bot.send_message(user_id, msg, parse_mode="Markdown")
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(user_id, msg, parse_mode="Markdown")
            except Exception:
                pass
        except Forbidden:
            pass
        except Exception:
            pass
        await asyncio.sleep(0.05)