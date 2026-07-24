from datetime import datetime, timedelta
from sqlalchemy import func
from database import Session, Order, Package, Restaurant
from services.review_service import get_rating


def get_restaurant_report(restaurant_id: int) -> dict:
    """Полный отчёт по заведению"""
    now       = datetime.utcnow()
    week_ago  = now - timedelta(days=7)

    with Session() as s:
        rest = s.query(Restaurant).filter_by(id=restaurant_id).first()
        if not rest:
            return {}

        # За прошлую неделю
        week_orders = (
            s.query(Order)
            .join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == restaurant_id,
                    Order.created_at >= week_ago)
            .all()
        )
        week_done      = sum(1 for o in week_orders if o.status == "used")
        week_cancelled = sum(1 for o in week_orders if o.status == "cancelled")
        week_revenue   = (
            s.query(func.sum(Package.price))
            .join(Order, Order.package_id == Package.id)
            .filter(Package.restaurant_id == restaurant_id,
                    Order.status == "used",
                    Order.created_at >= week_ago)
            .scalar()
        ) or 0

        # За всё время
        total_orders = (
            s.query(Order)
            .join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == restaurant_id)
            .count()
        )
        total_revenue = (
            s.query(func.sum(Package.price))
            .join(Order, Order.package_id == Package.id)
            .filter(Package.restaurant_id == restaurant_id,
                    Order.status == "used")
            .scalar()
        ) or 0

        return {
            "rest_name":     rest.name,
            "orders":        len(week_orders),
            "done":          week_done,
            "cancelled":     week_cancelled,
            "revenue":       week_revenue,
            "rating":        get_rating(restaurant_id),
            "total":         total_orders,
            "total_revenue": total_revenue,
        }


def get_all_restaurants():
    """Список всех активных заведений"""
    with Session() as s:
        rests = s.query(Restaurant).filter_by(active=True).all()
        result = []
        for r in rests:
            result.append({"id": r.id, "name": r.name, "district": r.district, "owner_id": r.owner_id})
        return result

def get_top_restaurants(limit: int = 5) -> list:
    """
    Топ заведений по комбинированному скору:
    - Новые заведения (0 заказов) всегда внизу
    - Учитывается и рейтинг и количество заказов
    - Минимум 3 отзыва для честного рейтинга
    """
    from services.review_service import get_rating, get_review_count
    from database import Order, Package

    with Session() as s:
        rests = s.query(Restaurant).filter_by(active=True).all()
        result = []
        for rest in rests:
            total_orders = (
                s.query(Order)
                .join(Package, Order.package_id == Package.id)
                .filter(Package.restaurant_id == rest.id, Order.status == "used")
                .count()
            )
            rating       = get_rating(rest.id)
            review_count = get_review_count(rest.id)

            # Честный рейтинг — если меньше 3 отзывов показываем 0
            fair_rating = rating if review_count >= 3 else 0

        
            if total_orders == 0:
                score = 0
            else:
                score = (fair_rating * 0.6) + (min(total_orders, 100) / 100 * 5 * 0.4)

            result.append({
                "id":           rest.id,
                "name":         rest.name,
                "district":     rest.district,
                "orders":       total_orders,
                "rating":       rating,
                "review_count": review_count,
                "score":        score,
            })

    result.sort(key=lambda x: x["score"], reverse=True)
    return result[:limit]