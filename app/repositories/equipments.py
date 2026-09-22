from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Equipment


def list_equipments(db: Session, category: str | None = None, include_inactive: bool = False) -> list[Equipment]:
    statement: Select[tuple[Equipment]] = (
        select(Equipment)
        .options(selectinload(Equipment.maintenances))
        .order_by(Equipment.purchase_date.desc(), Equipment.name.asc())
    )
    if category:
        statement = statement.where(Equipment.category == category)
    if not include_inactive:
        statement = statement.where(Equipment.status != "inactive")
    return list(db.scalars(statement).all())


def get_equipment(db: Session, equipment_id: int) -> Equipment | None:
    return db.scalar(
        select(Equipment)
        .where(Equipment.id == equipment_id)
        .options(selectinload(Equipment.maintenances))
    )


def categories(db: Session) -> list[str]:
    return list(db.scalars(select(Equipment.category).distinct().order_by(Equipment.category.asc())).all())


def total_invested(db: Session) -> object:
    return db.scalar(select(func.coalesce(func.sum(Equipment.purchase_cost), 0)))


def save_equipment(db: Session, equipment: Equipment) -> Equipment:
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment
