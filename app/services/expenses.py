from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Expense, ExpenseStatus, PaymentMethod
from app.repositories import expenses as repository
from app.schemas.expense import ExpenseCreate, ExpensePayment, ExpenseUpdate


class ExpenseNotFoundError(ValueError):
    pass


def recurring_key(payload: ExpenseCreate | ExpenseUpdate) -> str | None:
    if not payload.is_recurring:
        return None
    return f"{payload.category_name.lower()}:{payload.description.lower()}:{payload.expense_date:%Y-%m}"


def effective_status(expense: Expense, today: date | None = None) -> ExpenseStatus:
    today = today or date.today()
    if expense.status in {ExpenseStatus.PAID, ExpenseStatus.CANCELED}:
        return expense.status
    if expense.due_date and expense.due_date < today:
        return ExpenseStatus.OVERDUE
    return ExpenseStatus.PENDING


def list_expenses(db: Session, date_from=None, date_to=None, category_id: int | None = None, status: str | None = None):
    expenses = repository.list_expenses(db, date_from, date_to, category_id, status)
    for expense in expenses:
        current = effective_status(expense)
        if expense.status != current and current == ExpenseStatus.OVERDUE:
            expense.status = current
    return expenses


def get_expense_or_raise(db: Session, expense_id: int) -> Expense:
    expense = repository.get_expense(db, expense_id)
    if expense is None:
        raise ExpenseNotFoundError("Despesa nao encontrada.")
    expense.status = effective_status(expense)
    return expense


def create_expense(db: Session, payload: ExpenseCreate) -> Expense:
    category = repository.get_or_create_operational_category(db, payload.category_name)
    expense = Expense(
        category=category,
        description=payload.description,
        amount=payload.amount,
        expense_date=payload.expense_date,
        due_date=payload.due_date,
        paid_at=payload.paid_at,
        payment_method=payload.payment_method,
        status=payload.status,
        notes=payload.notes,
        is_recurring=payload.is_recurring,
        recurrence_months=payload.recurrence_months,
        recurring_key=recurring_key(payload),
    )
    if expense.paid_at:
        expense.status = ExpenseStatus.PAID
    return repository.save_expense(db, expense)


def update_expense(db: Session, expense_id: int, payload: ExpenseUpdate) -> Expense:
    expense = get_expense_or_raise(db, expense_id)
    category = repository.get_or_create_operational_category(db, payload.category_name)
    expense.category = category
    expense.description = payload.description
    expense.amount = payload.amount
    expense.expense_date = payload.expense_date
    expense.due_date = payload.due_date
    expense.paid_at = payload.paid_at
    expense.payment_method = payload.payment_method
    expense.status = ExpenseStatus.PAID if payload.paid_at else payload.status
    expense.notes = payload.notes
    expense.is_recurring = payload.is_recurring
    expense.recurrence_months = payload.recurrence_months
    expense.recurring_key = recurring_key(payload)
    return repository.save_expense(db, expense)


def register_payment(db: Session, expense_id: int, payload: ExpensePayment) -> Expense:
    expense = get_expense_or_raise(db, expense_id)
    expense.paid_at = payload.paid_at
    expense.payment_method = payload.payment_method
    expense.status = ExpenseStatus.PAID
    return repository.save_expense(db, expense)


def categories(db: Session):
    return repository.list_categories(db)


def indicators_by_category(db: Session, date_from=None, date_to=None) -> list[dict[str, Decimal | float | str]]:
    rows = repository.totals_by_category(db, date_from, date_to)
    max_total = max((total for _, total in rows), default=Decimal("0"))
    return [
        {
            "category": category,
            "total": total,
            "percent": 0 if max_total == 0 else round(float((total / max_total) * 100), 2),
        }
        for category, total in rows
    ]
