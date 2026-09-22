from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Integer, Numeric, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EquipmentKind, EquipmentStatus, FilamentMaterial
from app.models.mixins import IdMixin, TimestampMixin


class Filament(IdMixin, TimestampMixin, Base):
    __tablename__ = "filaments"
    __table_args__ = (
        Index("ix_filaments_material_color", "material", "color"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    material: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    diameter_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    spool_weight_grams: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    stock_grams: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0.000"), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    purchase_items = relationship("PurchaseItem", back_populates="filament")
    filament_purchases = relationship("FilamentPurchase", back_populates="filament")


class FilamentPurchase(IdMixin, TimestampMixin, Base):
    __tablename__ = "filament_purchases"
    __table_args__ = (
        Index("ix_filament_purchases_purchase_date", "purchase_date"),
        Index("ix_filament_purchases_material_color", "material", "color"),
        Index("ix_filament_purchases_supplier_date", "supplier", "purchase_date"),
    )

    filament_id: Mapped[int | None] = mapped_column(ForeignKey("filaments.id"))
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    material: Mapped[FilamentMaterial] = mapped_column(String(32), nullable=False)
    color: Mapped[str] = mapped_column(String(80), nullable=False)
    weight_grams: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    material_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_per_gram: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    supplier: Mapped[str] = mapped_column(String(160), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    filament = relationship("Filament", back_populates="filament_purchases")


class Equipment(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipments"
    __table_args__ = (
        Index("ix_equipments_name_status", "name", "status"),
        Index("ix_equipments_category_kind", "category", "kind"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Equipamento", index=True)
    kind: Mapped[EquipmentKind] = mapped_column(String(32), default=EquipmentKind.DURABLE, nullable=False, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    serial_number: Mapped[str | None] = mapped_column(String(120), unique=True)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(160), index=True)
    estimated_life_months: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[EquipmentStatus] = mapped_column(
        String(32),
        default=EquipmentStatus.ACTIVE,
        nullable=False,
    )

    purchase_items = relationship("PurchaseItem", back_populates="equipment")
    maintenances = relationship("EquipmentMaintenance", back_populates="equipment", cascade="all, delete-orphan")


class EquipmentMaintenance(IdMixin, TimestampMixin, Base):
    __tablename__ = "equipment_maintenances"
    __table_args__ = (
        Index("ix_equipment_maintenances_equipment_date", "equipment_id", "maintenance_date"),
    )

    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id"), nullable=False)
    maintenance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(160))
    notes: Mapped[str | None] = mapped_column(String(500))

    equipment = relationship("Equipment", back_populates="maintenances")
