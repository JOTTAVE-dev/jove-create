from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.core.timezone import now_local
from app.models import PaymentStatus, Product, Sale, SaleItem, SalePayment, SaleStatus
from app.models.enums import PaymentMethod
from app.repositories import sales as sale_repository
from app.schemas.sale import PaymentCreate, SaleCreate, SaleItemInput, SaleUpdate

MONEY = Decimal("0.01")


class SaleNotFoundError(ValueError):
    pass


class SaleValidationError(ValueError):
    pass


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_item(product: Product, payload: SaleItemInput) -> dict[str, Decimal | str | int]:
    subtotal = money(payload.quantity * payload.unit_price)
    discount = money(payload.discount_amount)
    if discount > subtotal:
        raise SaleValidationError("Desconto maior que o subtotal do item.")
    total = money(subtotal - discount)
    total_cost = money(payload.quantity * payload.unit_cost)
    gross_profit = money(total - total_cost)
    return {
        "product_id": product.id,
        "product_name": product.name,
        "quantity": payload.quantity,
        "unit_price": money(payload.unit_price),
        "discount_amount": discount,
        "total_amount": total,
        "unit_cost": money(payload.unit_cost),
        "total_cost": total_cost,
        "gross_profit": gross_profit,
    }


def calculate_totals(items: list[SaleItem]) -> dict[str, Decimal]:
    subtotal = money(sum((item.quantity * item.unit_price for item in items), Decimal("0")))
    discount = money(sum((item.discount_amount for item in items), Decimal("0")))
    total = money(sum((item.total_amount for item in items), Decimal("0")))
    total_cost = money(sum((item.total_cost for item in items), Decimal("0")))
    gross_profit = money(total - total_cost)
    return {
        "subtotal_amount": subtotal,
        "discount_amount": discount,
        "total_amount": total,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
    }


def payment_status_for(total_amount: Decimal, amount_paid: Decimal, canceled: bool = False) -> PaymentStatus:
    if canceled:
        return PaymentStatus.CANCELED
    if amount_paid <= Decimal("0"):
        return PaymentStatus.PENDING
    if amount_paid < total_amount:
        return PaymentStatus.PARTIALLY_PAID
    return PaymentStatus.PAID


def _build_items(db: Session, payload_items: list[SaleItemInput]) -> list[SaleItem]:
    items: list[SaleItem] = []
    for item_payload in payload_items:
        product = db.get(Product, item_payload.product_id)
        if product is None:
            raise SaleValidationError("Produto nao encontrado.")
        items.append(SaleItem(**calculate_item(product, item_payload)))
    return items


def list_sales(
    db: Session,
    date_from=None,
    date_to=None,
    product_id: int | None = None,
    client_query: str | None = None,
    payment_status: str | None = None,
) -> list[Sale]:
    return sale_repository.list_sales(db, date_from, date_to, product_id, client_query, payment_status)


def get_sale_or_raise(db: Session, sale_id: int) -> Sale:
    sale = sale_repository.get_sale(db, sale_id)
    if sale is None:
        raise SaleNotFoundError("Venda nao encontrada.")
    return sale


def create_sale(db: Session, payload: SaleCreate, user_id: int | None = None) -> Sale:
    client = sale_repository.get_or_create_client(db, payload.client_name)
    items = _build_items(db, payload.items)
    totals = calculate_totals(items)
    sale = Sale(
        client=client,
        user_id=user_id,
        status=SaleStatus.OPEN,
        payment_status=PaymentStatus.PENDING,
        channel=payload.channel,
        payment_method=payload.payment_method,
        sale_date=payload.sale_date or now_local(),
        notes=payload.notes,
        items=items,
        **totals,
    )
    return sale_repository.save_sale(db, sale)


def update_sale(db: Session, sale_id: int, payload: SaleUpdate) -> Sale:
    sale = get_sale_or_raise(db, sale_id)
    if sale.status == SaleStatus.CANCELED:
        raise SaleValidationError("Venda cancelada nao pode ser editada.")
    sale.client = sale_repository.get_or_create_client(db, payload.client_name)
    sale.channel = payload.channel
    sale.payment_method = payload.payment_method
    sale.sale_date = payload.sale_date or sale.sale_date
    sale.notes = payload.notes
    sale.items = _build_items(db, payload.items)
    for field, value in calculate_totals(sale.items).items():
        setattr(sale, field, value)
    sale.payment_status = payment_status_for(sale.total_amount, sale.amount_paid)
    return sale_repository.save_sale(db, sale)


def cancel_sale(db: Session, sale_id: int) -> Sale:
    sale = get_sale_or_raise(db, sale_id)
    sale.status = SaleStatus.CANCELED
    sale.payment_status = PaymentStatus.CANCELED
    return sale_repository.save_sale(db, sale)


def register_payment(db: Session, sale_id: int, payload: PaymentCreate) -> Sale:
    sale = get_sale_or_raise(db, sale_id)
    if sale.status == SaleStatus.CANCELED:
        raise SaleValidationError("Venda cancelada nao recebe pagamento.")
    payment = SalePayment(
        amount=money(payload.amount),
        payment_method=payload.payment_method,
        paid_at=payload.paid_at or now_local(),
        notes=payload.notes,
    )
    sale.payments.append(payment)
    sale.amount_paid = money(sum((payment.amount for payment in sale.payments), Decimal("0")))
    sale.payment_method = payload.payment_method
    sale.payment_status = payment_status_for(sale.total_amount, sale.amount_paid)
    if sale.payment_status == PaymentStatus.PAID:
        sale.status = SaleStatus.PAID
    return sale_repository.save_sale(db, sale)


def list_active_products(db: Session):
    return sale_repository.list_active_products(db)
