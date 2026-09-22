from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PaymentMethod, PaymentStatus, SaleChannel, SaleStatus
from app.models.mixins import IdMixin, TimestampMixin
from app.core.timezone import now_local


class Sale(IdMixin, TimestampMixin, Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_client_status", "client_id", "status"),
        Index("ix_sales_sale_date_status", "sale_date", "status"),
    )

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[SaleStatus] = mapped_column(String(32), default=SaleStatus.DRAFT, nullable=False, index=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        String(32),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    channel: Mapped[SaleChannel] = mapped_column(String(32), default=SaleChannel.OTHER, nullable=False, index=True)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(String(32), index=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_local, nullable=False, index=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    client = relationship("Client", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("SalePayment", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        Index("ix_sale_items_sale_product", "sale_id", "product_id"),
    )

    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class SalePayment(IdMixin, TimestampMixin, Base):
    __tablename__ = "sale_payments"
    __table_args__ = (
        Index("ix_sale_payments_sale_paid_at", "sale_id", "paid_at"),
    )

    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(String(32), nullable=False, index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_local, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(String(500))

    sale = relationship("Sale", back_populates="payments")
