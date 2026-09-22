from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.timezone import now_local
from app.models.enums import PurchaseStatus
from app.models.mixins import IdMixin, TimestampMixin


class Purchase(IdMixin, TimestampMixin, Base):
    __tablename__ = "purchases"
    __table_args__ = (
        Index("ix_purchases_category_status", "category_id", "status"),
        Index("ix_purchases_supplier_date", "supplier_name", "purchase_date"),
    )

    supplier_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[PurchaseStatus] = mapped_column(String(32), default=PurchaseStatus.DRAFT, nullable=False, index=True)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_local, nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    category = relationship("FinancialCategory", back_populates="purchases")
    user = relationship("User", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        Index("ix_purchase_items_purchase", "purchase_id"),
        Index("ix_purchase_items_filament", "filament_id"),
        Index("ix_purchase_items_equipment", "equipment_id"),
    )

    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"), nullable=False)
    filament_id: Mapped[int | None] = mapped_column(ForeignKey("filaments.id"))
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipments.id"))
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchase", back_populates="items")
    filament = relationship("Filament", back_populates="purchase_items")
    equipment = relationship("Equipment", back_populates="purchase_items")
