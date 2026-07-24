from datetime import datetime, timedelta
import logging

from database import Session, Package, Restaurant

log = logging.getLogger(__name__)


def get_available(district: str = None):
    with Session() as s:
        q = (
            s.query(Package, Restaurant)
            .join(Restaurant, Package.restaurant_id == Restaurant.id)
            .filter(Package.active == True, Package.quantity > 0, Restaurant.active == True)
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
            active=True,
        )
        s.add(pkg)
        s.commit()
        s.refresh(pkg)
        s.expunge(pkg)
        return pkg


def get_all_active():
    with Session() as s:
        rows = (
            s.query(Package, Restaurant)
            .join(Restaurant)
            .filter(Package.active == True)
            .all()
        )
        result = []
        for pkg, rest in rows:
            s.expunge(pkg); s.expunge(rest)
            result.append((pkg, rest))
        return result


def count_active() -> int:
    with Session() as s:
        return s.query(Package).filter_by(active=True).count()


async def nightly_cleanup(bot):
    """Планировщик: деактивирует пустые пакеты старше 1 дня"""
    with Session() as s:
        cutoff  = datetime.utcnow() - timedelta(days=1)
        old     = s.query(Package).filter(
            Package.quantity == 0,
            Package.created_at < cutoff,
        ).all()
        for p in old:
            p.active = False
        if old:
            s.commit()
            log.info(f"Deactivated {len(old)} empty packages")

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
            
async def post_to_channel(bot, pkg, rest, rating: float):
    """Постим новый пакет в канал"""
    from config import CHANNEL_ID
    from texts import t
    from services.review_service import get_review_count

    try:
        text = t("channel_post", "ru",
                 rest=rest.name, address=rest.address, district=rest.district,
                 rating=rating, name=pkg.name, price=pkg.price,
                 qty=pkg.quantity, from_=pkg.pickup_from, to=pkg.pickup_to)

        photo = pkg.photo_file_id or rest.photo_file_id

        if photo:
            await bot.send_photo(
                CHANNEL_ID, photo,
                caption=text, parse_mode="Markdown"
            )
        else:
            await bot.send_message(
                CHANNEL_ID, text, parse_mode="Markdown"
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
        closed = s.query(Restaurant).filter_by(is_closed=True, active=True).all()
        for rest in closed:
            rest.is_closed = False
            pkgs = s.query(Package).filter_by(restaurant_id=rest.id).all()
            for pkg in pkgs:
                pkg.active = True
            # Уведомляем владельца
            if rest.owner_id:
                try:
                    lang = get_lang(rest.owner_id)
                    await bot.send_message(
                        rest.owner_id,
                        "🟢 " + (f"*{rest.name}* автоматически открыто!" if lang == "ru"
                                 else f"*{rest.name}* avtomatik ochildi!"),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        if closed:
            s.commit()
            

