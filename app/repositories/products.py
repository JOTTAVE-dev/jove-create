from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import Product


def list_products(db: Session, query: str | None = None, include_inactive: bool = False) -> list[Product]:
    statement: Select[tuple[Product]] = select(Product).order_by(Product.name.asc())
    if not include_inactive:
        statement = statement.where(Product.is_active.is_(True))
    if query:
        term = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                Product.name.ilike(term),
                Product.category.ilike(term),
                Product.description.ilike(term),
            )
        )
    return list(db.scalars(statement).all())


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def create_product(db: Session, product: Product) -> Product:
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def save_product(db: Session, product: Product) -> Product:
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def product_has_sales(db: Session, product_id: int) -> bool:
    from app.models import SaleItem

    count = db.scalar(select(func.count(SaleItem.id)).where(SaleItem.product_id == product_id))
    return bool(count)
