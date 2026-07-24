from database import Session, PackageTemplate


def create_template(restaurant_id: int, name: str, photo_file_id: str,
                    price: int, pickup_from: str, pickup_to: str) -> PackageTemplate:
    with Session() as s:
        tpl = PackageTemplate(
            restaurant_id=restaurant_id,
            name=name,
            photo_file_id=photo_file_id,
            price=price,
            pickup_from=pickup_from,
            pickup_to=pickup_to,
        )
        s.add(tpl)
        s.commit()
        s.refresh(tpl)
        s.expunge(tpl)
        return tpl


def get_templates(restaurant_id: int):
    with Session() as s:
        tpls = s.query(PackageTemplate).filter_by(restaurant_id=restaurant_id).all()
        s.expunge_all()
        return tpls


def get_template(template_id: int):
    with Session() as s:
        tpl = s.query(PackageTemplate).filter_by(id=template_id).first()
        if tpl:
            s.expunge(tpl)
        return tpl


def delete_template(template_id: int):
    with Session() as s:
        tpl = s.query(PackageTemplate).filter_by(id=template_id).first()
        if tpl:
            s.delete(tpl)
            s.commit()