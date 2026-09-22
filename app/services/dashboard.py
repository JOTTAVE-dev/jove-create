from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.currency import format_brl
from app.models import Sale
from app.services.financials import calculate_financial_overview, expenses_query, filament_purchases_query, money, resolve_period, sales_query

ZERO = Decimal("0.00")


def _percent(value: Decimal, maximum: Decimal) -> int:
    if maximum <= ZERO:
        return 0
    return max(4, min(100, int((value / maximum) * 100)))


def _bar_rows(rows: list[tuple[str, Decimal]]) -> list[dict[str, object]]:
    maximum = max((value for _, value in rows), default=ZERO)
    return [
        {
            "label": label,
            "value": value,
            "formatted": format_brl(value),
            "percent": _percent(value, maximum),
        }
        for label, value in rows
    ]


def _month_label(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{month}/{year[-2:]}"


def _sale_channel_label(channel: str) -> str:
    labels = {
        "instagram": "Instagram",
        "whatsapp": "WhatsApp",
        "shopee": "Shopee",
        "in_person": "Venda presencial",
        "other": "Outros",
    }
    return labels.get(channel, channel)


def _payment_status_label(status: str) -> str:
    labels = {
        "pending": "Pendente",
        "paid": "Pago",
        "partially_paid": "Parcial",
        "canceled": "Cancelado",
    }
    return labels.get(status, status)


def _expense_status_label(status: str) -> str:
    labels = {
        "pending": "Pendente",
        "paid": "Pago",
        "overdue": "Atrasado",
        "canceled": "Cancelado",
    }
    return labels.get(status, status)


def build_dashboard(db: Session, preset: str | None = None, date_from: date | None = None, date_to: date | None = None) -> dict[str, object]:
    period = resolve_period(preset, date_from, date_to)
    overview = calculate_financial_overview(db, period)
    sales = list(db.scalars(sales_query(period).order_by(Sale.sale_date.desc())).all())
    expenses = list(db.scalars(expenses_query(period)).all())
    filament_purchases = list(db.scalars(filament_purchases_query(period)).all())

    revenue_by_month: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    profit_by_month: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    sales_by_channel: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    expenses_by_category: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    purchases_by_material: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)

    for sale in sales:
        month_key = sale.sale_date.strftime("%Y-%m")
        revenue_by_month[month_key] += money(sale.total_amount)
        profit_by_month[month_key] += money(sale.gross_profit)
        sales_by_channel[str(sale.channel)] += money(sale.total_amount)

    for expense in expenses:
        expenses_by_category[expense.category.name] += money(expense.amount)

    for purchase in filament_purchases:
        purchases_by_material[str(purchase.material)] += money(purchase.total_cost)

    return {
        "period": period,
        "metrics": [
            {"label": "Faturamento", "value": format_brl(overview.revenue), "detail": "Vendas nao canceladas", "tone": "positive"},
            {"label": "Recebido", "value": format_brl(overview.received), "detail": "Pagamentos no periodo", "tone": "positive"},
            {"label": "Pendente", "value": format_brl(overview.pending), "detail": "Vendido e ainda nao recebido", "tone": "neutral"},
            {"label": "Custo vendido", "value": format_brl(overview.product_costs), "detail": "Custo registrado nas vendas", "tone": "negative"},
            {"label": "Despesas operacionais", "value": format_brl(overview.operating_expenses), "detail": "Sem filamentos/equipamentos", "tone": "negative"},
            {"label": "Lucro bruto", "value": format_brl(overview.gross_profit), "detail": "Faturamento menos custo vendido", "tone": "positive" if overview.gross_profit >= ZERO else "negative"},
            {"label": "Lucro operacional", "value": format_brl(overview.estimated_operating_profit), "detail": "Estimado, sem saldo de caixa", "tone": "positive" if overview.estimated_operating_profit >= ZERO else "negative"},
            {"label": "Compras de filamentos", "value": format_brl(overview.filament_purchases), "detail": "Estoque, nao custo vendido", "tone": "neutral"},
            {"label": "Investimentos", "value": format_brl(overview.equipment_investments), "detail": "Equipamentos separados", "tone": "neutral"},
            {"label": "Vendas", "value": str(overview.sales_count), "detail": "Quantidade no periodo", "tone": "neutral"},
            {"label": "Ticket medio", "value": format_brl(overview.average_ticket), "detail": "Faturamento por venda", "tone": "neutral"},
        ],
        "charts": {
            "revenue_by_month": _bar_rows([(_month_label(month), money(total)) for month, total in sorted(revenue_by_month.items())]),
            "profit_by_month": _bar_rows([(_month_label(month), money(total)) for month, total in sorted(profit_by_month.items())]),
            "expenses_by_category": _bar_rows([(name, money(total)) for name, total in sorted(expenses_by_category.items())]),
            "sales_by_channel": _bar_rows([(_sale_channel_label(channel), money(total)) for channel, total in sorted(sales_by_channel.items())]),
            "purchases_by_material": _bar_rows([(material, money(total)) for material, total in sorted(purchases_by_material.items())]),
        },
        "recent_sales": [
            {
                "id": sale.id,
                "date": sale.sale_date.strftime("%d/%m/%Y"),
                "client": sale.client.name if sale.client else "-",
                "status": _payment_status_label(str(sale.payment_status)),
                "value": format_brl(sale.total_amount),
            }
            for sale in sales[:5]
        ],
        "open_expenses": [
            {
                "id": expense.id,
                "description": expense.description,
                "category": expense.category.name,
                "status": _expense_status_label(str(expense.status)),
                "value": format_brl(expense.amount),
            }
            for expense in expenses
            if str(expense.status) in {"pending", "overdue"}
        ][:5],
    }
