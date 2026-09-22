from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EquipmentKind, EquipmentStatus


class EquipmentBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=1, max_length=100)
    kind: EquipmentKind = EquipmentKind.DURABLE
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    purchase_date: date | None = None
    purchase_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    supplier: str | None = Field(default=None, max_length=160)
    estimated_life_months: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=500)
    status: EquipmentStatus = EquipmentStatus.ACTIVE

    @field_validator("name", "category", "manufacturer", "model", "supplier", "notes", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(EquipmentBase):
    pass


class EquipmentRead(EquipmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MaintenanceCreate(BaseModel):
    maintenance_date: date
    description: str = Field(min_length=2, max_length=255)
    cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    supplier: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("description", "supplier", "notes", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None
