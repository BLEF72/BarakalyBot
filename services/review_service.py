from database import Session, Review, Restaurant
from sqlalchemy import func


def add_review(user_id: int, restaurant_id: int, order_code: str, rating: int):
    with Session() as s:
        # Проверяем что не оценивал этот заказ раньше
        existing = s.query(Review).filter_by(order_code=order_code).first()
        if existing:
            return False
        s.add(Review(
            user_id=user_id,
            restaurant_id=restaurant_id,
            order_code=order_code,
            rating=rating,
        ))
        s.commit()
        return True


def get_rating(restaurant_id: int):
    """Средний рейтинг заведения. None, если отзывов ещё нет - не выдумываем цифру."""
    with Session() as s:
        result = s.query(func.avg(Review.rating)).filter_by(
            restaurant_id=restaurant_id
        ).scalar()
        return round(float(result), 1) if result else None


def get_review_count(restaurant_id: int) -> int:
    with Session() as s:
        return s.query(Review).filter_by(restaurant_id=restaurant_id).count()


def already_reviewed(order_code: str) -> bool:
    with Session() as s:
        return s.query(Review).filter_by(order_code=order_code).first() is not None
    

def get_ratings_batch(restaurant_ids) -> dict:
    """Средний рейтинг сразу для нескольких заведений, одним запросом"""
    if not restaurant_ids:
        return {}
    with Session() as s:
        rows = (
            s.query(Review.restaurant_id, func.avg(Review.rating))
            .filter(Review.restaurant_id.in_(restaurant_ids))
            .group_by(Review.restaurant_id)
            .all()
        )
        return {rid: round(float(avg), 1) for rid, avg in rows}


def get_review_counts_batch(restaurant_ids) -> dict:
    """Количество отзывов сразу для нескольких заведений, одним запросом"""
    if not restaurant_ids:
        return {}
    with Session() as s:
        rows = (
            s.query(Review.restaurant_id, func.count(Review.id))
            .filter(Review.restaurant_id.in_(restaurant_ids))
            .group_by(Review.restaurant_id)
            .all()
        )
        return dict(rows)