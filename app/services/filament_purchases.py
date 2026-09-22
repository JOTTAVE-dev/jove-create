from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models import FilamentPurchase
from app.repositories import filament_purchases as repository
from app.schemas.filament_purchase import FilamentPurchaseCreate, FilamentPurchaseUpdate

MONEY = Decimal("0.01")
COST_PER_GRAM = Decimal("0.000001")


class FilamentPurchaseNotFoundError(ValueError):
    pass


class FilamentPurchaseValidationError(ValueError):
    pass


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def cost_per_gram(value: Decimal) -> Decimal:
    return value.quantize(COST_PER_GRAM, rounding=ROUND_HALF_UP)


def calculate_total_cost(material_amount: Decimal, shipping_amount: Decimal, discount_amount: Decimal) -> Decimal:
    total = money(material_amount + shipping_amount - discount_amount)
    if total < Decimal("0"):
        raise FilamentPurchaseValidationError("Desconto maior que o valor da compra.")
    return total


def calculate_cost_per_gram(total_cost: Decimal, weight_grams: Decimal) -> Decimal:
    if weight_grams <= Decimal("0"):
        raise FilamentPurchaseValidationError("Peso adquirido deve ser maior que zero.")
    return cost_per_gram(total_cost / weight_grams)


def _values(payload: FilamentPurchaseCreate | FilamentPurchaseUpdate) -> dict:
    total_cost = calculate_total_cost(payload.material_amount, payload.shipping_amount, payload.discount_amount)
    return {
        **payload.model_dump(),
        "total_cost": total_cost,
        "cost_per_gram": calculate_cost_per_gram(total_cost, payload.weight_grams),
    }


def list_purchases(db: Session, date_from=None, date_to=None, material: str | None = None, supplier: str | None = None):
    return repository.list_purchases(db, date_from, date_to, material, supplier)


def get_purchase_or_raise(db: Session, purchase_id: int) -> FilamentPurchase:
    purchase = repository.get_purchase(db, purchase_id)
    if purchase is None:
        raise FilamentPurchaseNotFoundError("Compra de filamento nao encontrada.")
    return purchase


def create_purchase(db: Session, payload: FilamentPurchaseCreate) -> FilamentPurchase:
    return repository.save_purchase(db, FilamentPurchase(**_values(payload)))


def update_purchase(db: Session, purchase_id: int, payload: FilamentPurchaseUpdate) -> FilamentPurchase:
    purchase = get_purchase_or_raise(db, purchase_id)
    for field, value in _values(payload).items():
        setattr(purchase, field, value)
    return repository.save_purchase(db, purchase)


def monthly_chart(db: Session) -> list[dict[str, Decimal | float | str]]:
    rows = repository.monthly_totals(db)
    max_total = max((total for _, total in rows), default=Decimal("0"))
    return [
        {
            "month": month,
            "total": total,
            "percent": 0 if max_total == 0 else round(float((total / max_total) * 100), 2),
        }
        for month, total in rows
    ]
