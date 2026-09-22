from datetime import date, datetime, time

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Client, Product, Sale


def list_sales(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    product_id: int | None = None,
    client_query: str | None = None,
    payment_status: str | None = None,
) -> list[Sale]:
    statement: Select[tuple[Sale]] = (
        select(Sale)
        .join(Sale.client)
        .options(selectinload(Sale.client), selectinload(Sale.items), selectinload(Sale.payments))
        .order_by(Sale.sale_date.desc())
    )
    if product_id:
        from app.models import SaleItem

        statement = statement.join(Sale.items).where(SaleItem.product_id == product_id)
    if date_from:
        statement = statement.where(Sale.sale_date >= datetime.combine(date_from, time.min))
    if date_to:
        statement = statement.where(Sale.sale_date <= datetime.combine(date_to, time.max))
    if client_query:
        term = f"%{client_query.strip()}%"
        statement = statement.where(or_(Client.name.ilike(term), Client.email.ilike(term), Client.phone.ilike(term)))
    if payment_status:
        statement = statement.where(Sale.payment_status == payment_status)
    return list(db.scalars(statement).unique().all())


def get_sale(db: Session, sale_id: int) -> Sale | None:
    return db.scalar(
        select(Sale)
        .where(Sale.id == sale_id)
        .options(selectinload(Sale.client), selectinload(Sale.items), selectinload(Sale.payments))
    )


def get_or_create_client(db: Session, name: str) -> Client:
    client = db.scalar(select(Client).where(Client.name == name))
    if client:
        return client
    client = Client(name=name)
    db.add(client)
    db.flush()
    return client


def list_active_products(db: Session) -> list[Product]:
    return list(db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())).all())


def save_sale(db: Session, sale: Sale) -> Sale:
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale
