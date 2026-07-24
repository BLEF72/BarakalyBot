from database import Session, Subscription


def toggle_restaurant(user_id: int, restaurant_id: int) -> bool:
    with Session() as s:
        existing = s.query(Subscription).filter_by(
            user_id=user_id, restaurant_id=restaurant_id
        ).first()
        if existing:
            s.delete(existing)
            s.commit()
            return False
        s.add(Subscription(user_id=user_id, restaurant_id=restaurant_id))
        s.commit()
        return True


def toggle_district(user_id: int, district: str) -> bool:

    with Session() as s:
        existing = s.query(Subscription).filter_by(
            user_id=user_id, district=district
        ).first()
        if existing:
            s.delete(existing)
            s.commit()
            return False
        s.add(Subscription(user_id=user_id, district=district))
        s.commit()
        return True


def is_subscribed_restaurant(user_id: int, restaurant_id: int) -> bool:
    with Session() as s:
        return s.query(Subscription).filter_by(
            user_id=user_id, restaurant_id=restaurant_id
        ).first() is not None


def is_subscribed_district(user_id: int, district: str) -> bool:
    with Session() as s:
        return s.query(Subscription).filter_by(
            user_id=user_id, district=district
        ).first() is not None


def get_subscribers_for_restaurant(restaurant_id: int):
    with Session() as s:
        subs = s.query(Subscription).filter_by(restaurant_id=restaurant_id).all()
        return [sub.user_id for sub in subs]


def get_subscribers_for_district(district: str):
    with Session() as s:
        subs = s.query(Subscription).filter_by(district=district).all()
        return [sub.user_id for sub in subs]


def get_user_subscriptions(user_id: int):
    with Session() as s:
        subs = s.query(Subscription).filter_by(user_id=user_id).all()
        result = []
        for sub in subs:
            result.append({
                "restaurant_id": sub.restaurant_id,
                "district":      sub.district,
            })
        return result