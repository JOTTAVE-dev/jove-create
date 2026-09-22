from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Equipment, EquipmentMaintenance
from app.repositories import equipments as repository
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, MaintenanceCreate


class EquipmentNotFoundError(ValueError):
    pass


def list_equipments(db: Session, category: str | None = None, include_inactive: bool = False) -> list[Equipment]:
    return repository.list_equipments(db, category, include_inactive)


def get_equipment_or_raise(db: Session, equipment_id: int) -> Equipment:
    equipment = repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise EquipmentNotFoundError("Equipamento nao encontrado.")
    return equipment


def create_equipment(db: Session, payload: EquipmentCreate) -> Equipment:
    values = payload.model_dump()
    values["equipment_type"] = values["category"]
    return repository.save_equipment(db, Equipment(**values))


def update_equipment(db: Session, equipment_id: int, payload: EquipmentUpdate) -> Equipment:
    equipment = get_equipment_or_raise(db, equipment_id)
    values = payload.model_dump()
    values["equipment_type"] = values["category"]
    for field, value in values.items():
        setattr(equipment, field, value)
    return repository.save_equipment(db, equipment)


def add_maintenance(db: Session, equipment_id: int, payload: MaintenanceCreate) -> Equipment:
    equipment = get_equipment_or_raise(db, equipment_id)
    equipment.maintenances.append(EquipmentMaintenance(**payload.model_dump()))
    return repository.save_equipment(db, equipment)


def categories(db: Session) -> list[str]:
    return repository.categories(db)


def total_invested(db: Session) -> Decimal:
    return Decimal(repository.total_invested(db) or 0)


def maintenance_total(equipment: Equipment) -> Decimal:
    return sum((maintenance.cost for maintenance in equipment.maintenances), Decimal("0"))
