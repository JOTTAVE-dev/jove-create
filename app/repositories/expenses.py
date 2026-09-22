from datetime import date
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Expense, FinancialCategory, FinancialCategoryType


def get_or_create_operational_category(db: Session, name: str) -> FinancialCategory:
    category = db.scalar(
        select(FinancialCategory).where(
            FinancialCategory.name == name,
            FinancialCategory.category_type == FinancialCategoryType.OPERATING_EXPENSE,
        )
    )
    if category:
        return category
    category = FinancialCategory(name=name, category_type=FinancialCategoryType.OPERATING_EXPENSE, is_active=True)
    db.add(category)
    db.flush()
    return category


def list_categories(db: Session) -> list[FinancialCategory]:
    return list(
        db.scalars(
            select(FinancialCategory)
            .where(FinancialCategory.category_type == FinancialCategoryType.OPERATING_EXPENSE)
            .order_by(FinancialCategory.name.asc())
        ).all()
    )


def list_expenses(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    status: str | None = None,
) -> list[Expense]:
    statement: Select[tuple[Expense]] = (
        select(Expense)
        .join(Expense.category)
        .where(FinancialCategory.category_type == FinancialCategoryType.OPERATING_EXPENSE)
        .options(selectinload(Expense.category))
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
    )
    if date_from:
        statement = statement.where(Expense.expense_date >= date_from)
    if date_to:
        statement = statement.where(Expense.expense_date <= date_to)
    if category_id:
        statement = statement.where(Expense.category_id == category_id)
    if status:
        statement = statement.where(Expense.status == status)
    return list(db.scalars(statement).all())


def get_expense(db: Session, expense_id: int) -> Expense | None:
    return db.scalar(select(Expense).where(Expense.id == expense_id).options(selectinload(Expense.category)))


def save_expense(db: Session, expense: Expense) -> Expense:
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def totals_by_category(db: Session, date_from: date | None = None, date_to: date | None = None):
    statement = (
        select(FinancialCategory.name, func.sum(Expense.amount))
        .join(Expense.category)
        .where(
            FinancialCategory.category_type == FinancialCategoryType.OPERATING_EXPENSE,
            Expense.status != "canceled",
        )
        .group_by(FinancialCategory.name)
        .order_by(FinancialCategory.name.asc())
    )
    if date_from:
        statement = statement.where(Expense.expense_date >= date_from)
    if date_to:
        statement = statement.where(Expense.expense_date <= date_to)
    return [(name, total or Decimal("0")) for name, total in db.execute(statement).all()]
