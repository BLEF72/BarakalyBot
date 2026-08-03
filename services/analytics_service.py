from datetime import datetime
from sqlalchemy import func

from utils.time_utils import get_now

from database import Session, AnalyticsEvent, Order, User, Restaurant
from services import order_service, package_service


def get_stats() -> dict:
    """Возвращает общую статистику для админ-панели"""
    with Session() as s:
        total_commission = (
            s.query(func.sum(Order.commission))
            .filter(Order.status == "used")
            .scalar()
        ) or 0
        return {
            "restaurants": s.query(Restaurant).filter_by(active=True).count(),
            "packages":    package_service.count_active(),
            "orders":      order_service.count_all(),
            "done":        order_service.count_done(),
            "users":       s.query(User).count(),
            "commission":  total_commission,
        }


def get_district_stats():
    """Популярность районов по просмотрам"""
    with Session() as s:
        return (
            s.query(AnalyticsEvent.district, func.count().label("cnt"))
            .filter(AnalyticsEvent.event == "browse", AnalyticsEvent.district != None)
            .group_by(AnalyticsEvent.district)
            .order_by(func.count().desc())
            .all()
        )


def count_today_orders() -> int:
    today = get_now().date()
    with Session() as s:
        return s.query(Order).filter(
            Order.created_at >= datetime(today.year, today.month, today.day)
        ).count()
