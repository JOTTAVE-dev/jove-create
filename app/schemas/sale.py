from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import PaymentMethod, SaleChannel


class SaleItemInput(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    unit_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class SaleCreate(BaseModel):
    sale_date: datetime | None = None
    client_name: str = Field(min_length=2, max_length=160)
    channel: SaleChannel = SaleChannel.OTHER
    payment_method: PaymentMethod | None = None
    notes: str | None = Field(default=None, max_length=500)
    items: list[SaleItemInput] = Field(min_length=1)

    @field_validator("client_name", "notes", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class SaleUpdate(SaleCreate):
    pass


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    payment_method: PaymentMethod
    paid_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("notes", mode="before")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class SaleItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    gross_profit: Decimal

    model_config = ConfigDict(from_attributes=True)


class SaleRead(BaseModel):
    id: int
    client_id: int
    status: str
    payment_status: str
    channel: str
    payment_method: str | None
    subtotal_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    amount_paid: Decimal
    items: list[SaleItemRead]

    model_config = ConfigDict(from_attributes=True)
