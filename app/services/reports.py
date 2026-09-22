import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.currency import format_brl
from app.models import Equipment, Expense, FilamentPurchase, FinancialCategory, Sale, SalePayment
from app.models.enums import SaleChannel
from app.services.financials import (
    ZERO,
    calculate_financial_overview,
    equipment_investments_query,
    expenses_query,
    filament_purchases_query,
    money,
    resolve_period,
    sales_query,
    start_datetime,
    end_datetime,
)


REPORT_TYPES = {
    "sales": "Vendas",
    "expenses": "Despesas",
    "purchases": "Compras",
    "investments": "Investimentos",
    "revenue": "Faturamento",
    "profit": "Lucro",
    "cash_flow": "Fluxo de caixa",
}

FUTURE_EXPORT_FORMATS = ["Excel", "PDF"]


@dataclass(frozen=True)
class ReportFilters:
    report_type: str
    preset: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    category_id: int | None = None
    channel: str | None = None


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _month_label(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{month}/{year[-2:]}"


def _channel_label(channel: str) -> str:
    labels = {
        "instagram": "Instagram",
        "whatsapp": "WhatsApp",
        "shopee": "Shopee",
        "in_person": "Venda presencial",
        "other": "Outros",
    }
    return labels.get(channel, channel)


def _status_label(status: str) -> str:
    labels = {
        "pending": "Pendente",
        "paid": "Pago",
        "partially_paid": "Parcial",
        "canceled": "Cancelado",
        "open": "Aberta",
        "draft": "Rascunho",
        "overdue": "Atrasado",
    }
    return labels.get(status, status)


def _bar_rows(rows: list[dict[str, object]], key: str = "amount") -> list[dict[str, object]]:
    maximum = max((money(row[key]) for row in rows), default=ZERO)
    result = []
    for row in rows:
        value = money(row[key])
        percent = 0 if maximum <= ZERO else max(4, min(100, int((value / maximum) * 100)))
        result.append({"label": row["label"], "formatted": format_brl(value), "percent": percent})
    return result


def report_categories(db: Session) -> list[FinancialCategory]:
    return list(db.scalars(select(FinancialCategory).order_by(FinancialCategory.name.asc())).all())


def _sales_rows(db: Session, filters: ReportFilters):
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    statement = (
        sales_query(period, filters.channel)
        .options(selectinload(Sale.client), selectinload(Sale.items), selectinload(Sale.payments))
        .order_by(Sale.sale_date.desc())
    )
    sales = list(db.scalars(statement).all())
    return [
        {
            "date": sale.sale_date.strftime("%d/%m/%Y"),
            "client": sale.client.name if sale.client else "-",
            "channel": _channel_label(str(sale.channel)),
            "status": _status_label(str(sale.payment_status)),
            "revenue": sale.total_amount,
            "received": sale.amount_paid,
            "pending": money(max(sale.total_amount - sale.amount_paid, ZERO)),
            "product_cost": sale.total_cost,
            "gross_profit": sale.gross_profit,
        }
        for sale in sales
    ]


def _expense_rows(db: Session, filters: ReportFilters):
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    expenses = list(
        db.scalars(
            expenses_query(period, filters.category_id).options(selectinload(Expense.category)).order_by(Expense.expense_date.desc())
        ).all()
    )
    return [
        {
            "date": expense.expense_date.strftime("%d/%m/%Y"),
            "description": expense.description,
            "category": expense.category.name,
            "status": _status_label(str(expense.status)),
            "amount": expense.amount,
            "paid_at": expense.paid_at.strftime("%d/%m/%Y") if expense.paid_at else "-",
        }
        for expense in expenses
    ]


def _purchase_rows(db: Session, filters: ReportFilters):
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    purchases = list(db.scalars(filament_purchases_query(period).order_by(FilamentPurchase.purchase_date.desc())).all())
    return [
        {
            "date": purchase.purchase_date.strftime("%d/%m/%Y"),
            "description": f"{purchase.material} {purchase.color}",
            "supplier": purchase.supplier,
            "weight": f"{purchase.weight_grams} g",
            "amount": purchase.total_cost,
            "unit_cost": purchase.cost_per_gram,
        }
        for purchase in purchases
    ]


def _investment_rows(db: Session, filters: ReportFilters):
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    equipments = list(db.scalars(equipment_investments_query(period).order_by(Equipment.purchase_date.desc())).all())
    return [
        {
            "date": equipment.purchase_date.strftime("%d/%m/%Y") if equipment.purchase_date else "-",
            "name": equipment.name,
            "category": equipment.category,
            "supplier": equipment.supplier or "-",
            "amount": equipment.purchase_cost,
        }
        for equipment in equipments
    ]


def _monthly_revenue_rows(db: Session, filters: ReportFilters):
    rows: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    for sale in db.scalars(sales_query(period, filters.channel)).all():
        rows[_month_key(sale.sale_date.date())] += money(sale.total_amount)
    return [{"label": _month_label(month), "amount": money(amount)} for month, amount in sorted(rows.items())]


def _monthly_profit_rows(db: Session, filters: ReportFilters):
    rows: defaultdict[str, dict[str, Decimal]] = defaultdict(lambda: {"revenue": ZERO, "cost": ZERO, "gross_profit": ZERO})
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    for sale in db.scalars(sales_query(period, filters.channel)).all():
        month = _month_key(sale.sale_date.date())
        rows[month]["revenue"] += money(sale.total_amount)
        rows[month]["cost"] += money(sale.total_cost)
        rows[month]["gross_profit"] += money(sale.gross_profit)
    return [
        {
            "label": _month_label(month),
            "revenue": money(values["revenue"]),
            "cost": money(values["cost"]),
            "amount": money(values["gross_profit"]),
        }
        for month, values in sorted(rows.items())
    ]


def _cash_flow_rows(db: Session, filters: ReportFilters):
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    rows: defaultdict[str, dict[str, Decimal]] = defaultdict(lambda: {"inflow": ZERO, "outflow": ZERO})
    payments = (
        select(SalePayment)
        .join(SalePayment.sale)
        .where(SalePayment.paid_at >= start_datetime(period), SalePayment.paid_at <= end_datetime(period), Sale.status != "canceled")
    )
    if filters.channel:
        payments = payments.where(Sale.channel == filters.channel)
    for payment in db.scalars(payments).all():
        rows[_month_key(payment.paid_at.date())]["inflow"] += money(payment.amount)

    for expense in db.scalars(expenses_query(period, filters.category_id)).all():
        if expense.paid_at:
            rows[_month_key(expense.paid_at)]["outflow"] += money(expense.amount)

    for purchase in db.scalars(filament_purchases_query(period)).all():
        rows[_month_key(purchase.purchase_date)]["outflow"] += money(purchase.total_cost)

    for equipment in db.scalars(equipment_investments_query(period)).all():
        if equipment.purchase_date:
            rows[_month_key(equipment.purchase_date)]["outflow"] += money(equipment.purchase_cost)

    return [
        {
            "label": _month_label(month),
            "inflow": money(values["inflow"]),
            "outflow": money(values["outflow"]),
            "amount": money(values["inflow"] - values["outflow"]),
        }
        for month, values in sorted(rows.items())
    ]


def build_report(db: Session, filters: ReportFilters) -> dict[str, object]:
    report_type = filters.report_type if filters.report_type in REPORT_TYPES else "sales"
    filters = ReportFilters(report_type, filters.preset, filters.date_from, filters.date_to, filters.category_id, filters.channel)
    period = resolve_period(filters.preset, filters.date_from, filters.date_to)
    overview = calculate_financial_overview(db, period, category_id=filters.category_id, channel=filters.channel)

    if report_type == "expenses":
        rows = _expense_rows(db, filters)
        columns = [("date", "Data"), ("description", "Descricao"), ("category", "Categoria"), ("status", "Status"), ("amount", "Valor"), ("paid_at", "Pagamento")]
        chart_source = [{"label": row["category"], "amount": row["amount"]} for row in rows]
    elif report_type == "purchases":
        rows = _purchase_rows(db, filters)
        columns = [("date", "Data"), ("description", "Material"), ("supplier", "Fornecedor"), ("weight", "Peso"), ("amount", "Total"), ("unit_cost", "Custo/g")]
        chart_source = [{"label": row["description"], "amount": row["amount"]} for row in rows]
    elif report_type == "investments":
        rows = _investment_rows(db, filters)
        columns = [("date", "Data"), ("name", "Nome"), ("category", "Categoria"), ("supplier", "Fornecedor"), ("amount", "Valor")]
        chart_source = [{"label": row["category"], "amount": row["amount"]} for row in rows]
    elif report_type == "revenue":
        rows = _monthly_revenue_rows(db, filters)
        columns = [("label", "Mes"), ("amount", "Faturamento")]
        chart_source = rows
    elif report_type == "profit":
        rows = _monthly_profit_rows(db, filters)
        columns = [("label", "Mes"), ("revenue", "Faturamento"), ("cost", "Custo vendido"), ("amount", "Lucro bruto")]
        chart_source = rows
    elif report_type == "cash_flow":
        rows = _cash_flow_rows(db, filters)
        columns = [("label", "Mes"), ("inflow", "Entradas"), ("outflow", "Saidas"), ("amount", "Saldo")]
        chart_source = rows
    else:
        rows = _sales_rows(db, filters)
        columns = [
            ("date", "Data"),
            ("client", "Cliente"),
            ("channel", "Canal"),
            ("status", "Pagamento"),
            ("revenue", "Faturamento"),
            ("received", "Recebido"),
            ("pending", "Pendente"),
            ("product_cost", "Custo"),
            ("gross_profit", "Lucro bruto"),
        ]
        chart_source = [{"label": row["channel"], "amount": row["revenue"]} for row in rows]

    return {
        "period": period,
        "filters": filters,
        "report_type": report_type,
        "report_title": REPORT_TYPES[report_type],
        "report_types": REPORT_TYPES,
        "future_export_formats": FUTURE_EXPORT_FORMATS,
        "channels": list(SaleChannel),
        "categories": report_categories(db),
        "overview": overview,
        "summary": [
            {"label": "Faturamento", "value": format_brl(overview.revenue)},
            {"label": "Recebido", "value": format_brl(overview.received)},
            {"label": "Pendente", "value": format_brl(overview.pending)},
            {"label": "Lucro operacional", "value": format_brl(overview.estimated_operating_profit)},
        ],
        "columns": columns,
        "rows": rows,
        "chart": _bar_rows(chart_source),
    }


def report_to_csv(report: dict[str, object]) -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    columns = report["columns"]
    writer.writerow([label for _, label in columns])
    for row in report["rows"]:
        writer.writerow([_csv_value(row[key]) for key, _ in columns])
    return output.getvalue()


def _csv_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value).replace(".", ",")
    return str(value)
