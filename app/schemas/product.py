from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    category: str | None = Field(default=None, max_length=100)
    sale_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    estimated_production_cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    estimated_print_time_minutes: int | None = Field(default=None, ge=0)
    estimated_weight_grams: Decimal | None = Field(default=None, ge=Decimal("0"))
    image_url: str | None = Field(default=None, max_length=500)
    is_customizable: bool = True
    is_active: bool = True

    @field_validator("name", "description", "category", "image_url", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
