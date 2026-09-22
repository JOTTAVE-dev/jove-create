from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import IdMixin, TimestampMixin


class Product(IdMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_name_category", "name", "category"),
        Index("ix_products_active_category", "is_active", "category"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(String(1000))
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_production_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_print_time_minutes: Mapped[int | None] = mapped_column(Integer)
    estimated_weight_grams: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_customizable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sale_items = relationship("SaleItem", back_populates="product")
