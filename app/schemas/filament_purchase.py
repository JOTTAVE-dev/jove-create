from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import FilamentMaterial


class FilamentPurchaseBase(BaseModel):
    brand: str = Field(min_length=1, max_length=120)
    material: FilamentMaterial
    color: str = Field(min_length=1, max_length=80)
    weight_grams: Decimal = Field(gt=Decimal("0"))
    material_amount: Decimal = Field(ge=Decimal("0"))
    shipping_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    supplier: str = Field(min_length=1, max_length=160)
    purchase_date: date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("brand", "color", "supplier", "notes", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class FilamentPurchaseCreate(FilamentPurchaseBase):
    pass


class FilamentPurchaseUpdate(FilamentPurchaseBase):
    pass


class FilamentPurchaseRead(FilamentPurchaseBase):
    id: int
    total_cost: Decimal
    cost_per_gram: Decimal

    model_config = ConfigDict(from_attributes=True)
