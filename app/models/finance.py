from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExpenseStatus, FinancialCategoryType
from app.models.mixins import IdMixin, TimestampMixin


class FinancialCategory(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_categories"
    __table_args__ = (
        Index("ix_financial_categories_name_type", "name", "category_type"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_type: Mapped[FinancialCategoryType] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    purchases = relationship("Purchase", back_populates="category")
    expenses = relationship("Expense", back_populates="category")


class Expense(IdMixin, TimestampMixin, Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_expense_date", "expense_date"),
        Index("ix_expenses_category_due_date", "category_id", "due_date"),
        Index("ix_expenses_status_due_date", "status", "due_date"),
        Index("ix_expenses_recurring_key", "recurring_key"),
    )

    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    paid_at: Mapped[date | None] = mapped_column(Date)
    payment_method: Mapped[str | None] = mapped_column(String(32), index=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        String(32),
        default=ExpenseStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_months: Mapped[int | None] = mapped_column(Integer)
    recurring_key: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(String(500))

    category = relationship("FinancialCategory", back_populates="expenses")
