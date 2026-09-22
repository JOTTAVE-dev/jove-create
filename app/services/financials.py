from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezone import now_local
from app.models import Equipment, Expense, FinancialCategory, FinancialCategoryType, FilamentPurchase, Sale, SalePayment
from app.models.enums import ExpenseStatus, SaleStatus

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class FinancialPeriod:
    preset: str
    date_from: date
    date_to: date
    label: str


@dataclass(frozen=True)
class FinancialOverview:
    revenue: Decimal
    received: Decimal
    pending: Decimal
    product_costs: Decimal
    operating_expenses: Decimal
    gross_profit: Decimal
    estimated_operating_profit: Decimal
    filament_purchases: Decimal
    equipment_investments: Decimal
    sales_count: int
    average_ticket: Decimal


def money(value: Decimal | int | None) -> Decimal:
    if value is None:
        return ZERO
    return Decimal(value).quantize(Decimal("0.01"))


def resolve_period(preset: str | None = None, date_from: date | None = None, date_to: date | None = None) -> FinancialPeriod:
    today = now_local().date()
    selected = preset or "current_month"

    if selected == "today":
        start = end = today
        label = "Hoje"
    elif selected == "last_7_days":
        start = today - timedelta(days=6)
        end = today
        label = "Ultimos 7 dias"
    elif selected == "previous_month":
        first_current_month = today.replace(day=1)
        end = first_current_month - timedelta(days=1)
        start = end.replace(day=1)
        label = "Mes anterior"
    elif selected == "current_year":
        start = today.replace(month=1, day=1)
        end = today
        label = "Ano atual"
    elif selected == "custom" and date_from and date_to:
        start = min(date_from, date_to)
        end = max(date_from, date_to)
        label = "Periodo personalizado"
    else:
        start = today.replace(day=1)
        end = today
        selected = "current_month"
        label = "Mes atual"

    return FinancialPeriod(preset=selected, date_from=start, date_to=end, label=label)


def start_datetime(period: FinancialPeriod) -> datetime:
    return datetime.combine(period.date_from, time.min)


def end_datetime(period: FinancialPeriod) -> datetime:
    return datetime.combine(period.date_to, time.max)


def sales_query(period: FinancialPeriod, channel: str | None = None):
    statement = select(Sale).where(
        Sale.sale_date >= start_datetime(period),
        Sale.sale_date <= end_datetime(period),
        Sale.status != SaleStatus.CANCELED,
    )
    if channel:
        statement = statement.where(Sale.channel == channel)
    return statement


def payments_query(period: FinancialPeriod, channel: str | None = None):
    statement = (
        select(SalePayment.amount)
        .join(SalePayment.sale)
        .where(
            SalePayment.paid_at >= start_datetime(period),
            SalePayment.paid_at <= end_datetime(period),
            Sale.status != SaleStatus.CANCELED,
        )
    )
    if channel:
        statement = statement.where(Sale.channel == channel)
    return statement


def expenses_query(period: FinancialPeriod, category_id: int | None = None):
    statement = (
        select(Expense)
        .join(Expense.category)
        .where(
            Expense.expense_date >= period.date_from,
            Expense.expense_date <= period.date_to,
            Expense.status != ExpenseStatus.CANCELED,
            FinancialCategory.category_type == FinancialCategoryType.OPERATING_EXPENSE,
        )
    )
    if category_id:
        statement = statement.where(Expense.category_id == category_id)
    return statement


def filament_purchases_query(period: FinancialPeriod):
    return select(FilamentPurchase).where(
        FilamentPurchase.purchase_date >= period.date_from,
        FilamentPurchase.purchase_date <= period.date_to,
    )


def equipment_investments_query(period: FinancialPeriod):
    return select(Equipment).where(
        Equipment.purchase_date >= period.date_from,
        Equipment.purchase_date <= period.date_to,
    )


def calculate_financial_overview(
    db: Session,
    period: FinancialPeriod,
    category_id: int | None = None,
    channel: str | None = None,
) -> FinancialOverview:
    sales = list(db.scalars(sales_query(period, channel)).all())
    expenses = list(db.scalars(expenses_query(period, category_id)).all())
    filament_purchases = list(db.scalars(filament_purchases_query(period)).all())
    equipments = list(db.scalars(equipment_investments_query(period)).all())

    revenue = money(sum((sale.total_amount for sale in sales), ZERO))
    received = money(sum((amount for amount in db.scalars(payments_query(period, channel)).all()), ZERO))
    pending = money(sum((max(sale.total_amount - sale.amount_paid, ZERO) for sale in sales), ZERO))
    product_costs = money(sum((sale.total_cost for sale in sales), ZERO))
    operating_expenses = money(sum((expense.amount for expense in expenses), ZERO))
    gross_profit = money(revenue - product_costs)
    estimated_operating_profit = money(gross_profit - operating_expenses)
    filament_total = money(sum((purchase.total_cost for purchase in filament_purchases), ZERO))
    equipment_total = money(sum((equipment.purchase_cost for equipment in equipments), ZERO))
    sales_count = len(sales)
    average_ticket = money(revenue / sales_count) if sales_count else ZERO

    return FinancialOverview(
        revenue=revenue,
        received=received,
        pending=pending,
        product_costs=product_costs,
        operating_expenses=operating_expenses,
        gross_profit=gross_profit,
        estimated_operating_profit=estimated_operating_profit,
        filament_purchases=filament_total,
        equipment_investments=equipment_total,
        sales_count=sales_count,
        average_ticket=average_ticket,
    )
