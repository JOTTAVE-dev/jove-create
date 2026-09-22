from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ExpenseStatus, PaymentMethod


class ExpenseBase(BaseModel):
    description: str = Field(min_length=2, max_length=255)
    category_name: str = Field(min_length=2, max_length=120)
    amount: Decimal = Field(gt=Decimal("0"))
    expense_date: date
    due_date: date | None = None
    paid_at: date | None = None
    payment_method: PaymentMethod | None = None
    status: ExpenseStatus = ExpenseStatus.PENDING
    notes: str | None = Field(default=None, max_length=500)
    is_recurring: bool = False
    recurrence_months: int | None = Field(default=None, ge=1)

    @field_validator("description", "category_name", "notes", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpensePayment(BaseModel):
    paid_at: date
    payment_method: PaymentMethod
