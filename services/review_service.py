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


def get_rating(restaurant_id: int) -> float:
    """Средний рейтинг заведения. 5.0 если отзывов нет."""
    with Session() as s:
        result = s.query(func.avg(Review.rating)).filter_by(
            restaurant_id=restaurant_id
        ).scalar()
        return round(float(result), 1) if result else 5.0


def get_review_count(restaurant_id: int) -> int:
    with Session() as s:
        return s.query(Review).filter_by(restaurant_id=restaurant_id).count()


def already_reviewed(order_code: str) -> bool:
    with Session() as s:
        return s.query(Review).filter_by(order_code=order_code).first() is not None