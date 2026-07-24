from database import Session, Favorite, Restaurant, Package


def toggle(user_id: int, restaurant_id: int) -> bool:
    """Добавляет или убирает из избранного. Возвращает True если добавил."""
    with Session() as s:
        existing = s.query(Favorite).filter_by(
            user_id=user_id, restaurant_id=restaurant_id
        ).first()
        if existing:
            s.delete(existing)
            s.commit()
            return False
        s.add(Favorite(user_id=user_id, restaurant_id=restaurant_id))
        s.commit()
        return True


def is_favorite(user_id: int, restaurant_id: int) -> bool:
    with Session() as s:
        return s.query(Favorite).filter_by(
            user_id=user_id, restaurant_id=restaurant_id
        ).first() is not None


def get_user_favorites(user_id: int):
    """Возвращает [(Restaurant, [Package])] избранных заведений с активными пакетами"""
    with Session() as s:
        favs = s.query(Favorite).filter_by(user_id=user_id).all()
        result = []
        for fav in favs:
            rest = s.query(Restaurant).filter_by(id=fav.restaurant_id, active=True).first()
            if not rest:
                continue
            pkgs = s.query(Package).filter_by(
                restaurant_id=rest.id, active=True
            ).filter(Package.quantity > 0).all()
            s.expunge(rest)
            for p in pkgs:
                s.expunge(p)
            result.append((rest, pkgs))
        return result