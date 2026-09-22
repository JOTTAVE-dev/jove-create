from datetime import date
from decimal import Decimal

from sqlalchemy import Select, extract, func, select
from sqlalchemy.orm import Session

from app.models import FilamentPurchase


def list_purchases(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    material: str | None = None,
    supplier: str | None = None,
) -> list[FilamentPurchase]:
    statement: Select[tuple[FilamentPurchase]] = select(FilamentPurchase).order_by(
        FilamentPurchase.purchase_date.desc(),
        FilamentPurchase.id.desc(),
    )
    if date_from:
        statement = statement.where(FilamentPurchase.purchase_date >= date_from)
    if date_to:
        statement = statement.where(FilamentPurchase.purchase_date <= date_to)
    if material:
        statement = statement.where(FilamentPurchase.material == material)
    if supplier:
        statement = statement.where(FilamentPurchase.supplier.ilike(f"%{supplier.strip()}%"))
    return list(db.scalars(statement).all())


def get_purchase(db: Session, purchase_id: int) -> FilamentPurchase | None:
    return db.get(FilamentPurchase, purchase_id)


def save_purchase(db: Session, purchase: FilamentPurchase) -> FilamentPurchase:
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def monthly_totals(db: Session) -> list[tuple[str, Decimal]]:
    rows = db.execute(
        select(
            extract("year", FilamentPurchase.purchase_date),
            extract("month", FilamentPurchase.purchase_date),
            func.sum(FilamentPurchase.total_cost),
        )
        .group_by(extract("year", FilamentPurchase.purchase_date), extract("month", FilamentPurchase.purchase_date))
        .order_by(extract("year", FilamentPurchase.purchase_date), extract("month", FilamentPurchase.purchase_date))
    ).all()
    return [(f"{int(year):04d}-{int(month):02d}", total or Decimal("0")) for year, month, total in rows]
