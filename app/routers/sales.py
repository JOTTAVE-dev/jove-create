from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.auth import CurrentAuth, require_api_auth, require_web_auth
from app.core.config import get_settings
from app.core.currency import format_brl
from app.core.database import get_db
from app.models.enums import PaymentMethod, PaymentStatus, SaleChannel
from app.schemas.sale import PaymentCreate, SaleCreate, SaleItemInput, SaleRead, SaleUpdate
from app.services import sales as sale_service
from app.services.auth import verify_csrf_token

router = APIRouter(tags=["sales"])
api_router = APIRouter(prefix="/api/sales", tags=["api-sales"])
templates = Jinja2Templates(directory="app/templates")


def _csrf_token(request: Request) -> str:
    return request.cookies.get(get_settings().csrf_cookie_name, "")


def _decimal(value: str | None, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or not value.strip():
        return default
    normalized = value.strip().replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        raise ValueError("Valor decimal invalido.") from None


def _date(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value)


def _base_context(request: Request, auth: CurrentAuth, **extra):
    context = {
        "app_name": get_settings().app_name,
        "current_user": auth.user,
        "csrf_token": _csrf_token(request),
        "format_brl": format_brl,
        "channels": list(SaleChannel),
        "payment_methods": list(PaymentMethod),
        "payment_statuses": list(PaymentStatus),
    }
    context.update(extra)
    return context


def _payload_from_form(
    sale_date: str | None,
    client_name: str,
    product_id: int,
    quantity: str,
    unit_price: str,
    discount_amount: str | None,
    unit_cost: str | None,
    channel: SaleChannel,
    payment_method: PaymentMethod | None,
    notes: str | None,
):
    return SaleCreate(
        sale_date=_date(sale_date),
        client_name=client_name,
        channel=channel,
        payment_method=payment_method,
        notes=notes,
        items=[
            SaleItemInput(
                product_id=product_id,
                quantity=_decimal(quantity),
                unit_price=_decimal(unit_price),
                discount_amount=_decimal(discount_amount),
                unit_cost=_decimal(unit_cost),
            )
        ],
    )


@router.get("/sales")
def sales_page(
    request: Request,
    date_from: date | None = None,
    date_to: date | None = None,
    product_id: int | None = None,
    client: str | None = None,
    payment_status: str | None = None,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    sales = sale_service.list_sales(db, date_from, date_to, product_id, client, payment_status)
    products = sale_service.list_active_products(db)
    return templates.TemplateResponse(
        request=request,
        name="sales/list.html",
        context=_base_context(
            request,
            auth,
            sales=sales,
            products=products,
            filters={
                "date_from": date_from.isoformat() if date_from else "",
                "date_to": date_to.isoformat() if date_to else "",
                "product_id": product_id or "",
                "client": client or "",
                "payment_status": payment_status or "",
            },
        ),
    )


@router.get("/sales/new")
def new_sale_page(request: Request, auth: CurrentAuth = Depends(require_web_auth), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="sales/form.html",
        context=_base_context(
            request,
            auth,
            sale=None,
            products=sale_service.list_active_products(db),
            action="/sales",
            title="Registrar venda",
            error=None,
        ),
    )


@router.post("/sales")
def create_sale(
    request: Request,
    csrf_token: str = Form(...),
    sale_date: str | None = Form(None),
    client_name: str = Form(...),
    product_id: int = Form(...),
    quantity: str = Form(...),
    unit_price: str = Form(...),
    discount_amount: str | None = Form(None),
    unit_cost: str | None = Form(None),
    channel: SaleChannel = Form(SaleChannel.OTHER),
    payment_method: PaymentMethod | None = Form(None),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = _payload_from_form(
            sale_date, client_name, product_id, quantity, unit_price, discount_amount, unit_cost, channel, payment_method, notes
        )
        sale = sale_service.create_sale(db, payload, auth.user.id)
    except (ValidationError, ValueError, sale_service.SaleValidationError):
        return templates.TemplateResponse(
            request=request,
            name="sales/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                sale=None,
                products=sale_service.list_active_products(db),
                action="/sales",
                title="Registrar venda",
                error="Verifique os dados da venda.",
            ),
        )
    return RedirectResponse(f"/sales/{sale.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/sales/{sale_id}")
def sale_detail(request: Request, sale_id: int, auth: CurrentAuth = Depends(require_web_auth), db: Session = Depends(get_db)):
    try:
        sale = sale_service.get_sale_or_raise(db, sale_id)
    except sale_service.SaleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda nao encontrada.") from None
    return templates.TemplateResponse(request=request, name="sales/detail.html", context=_base_context(request, auth, sale=sale))


@router.get("/sales/{sale_id}/edit")
def edit_sale_page(
    request: Request,
    sale_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        sale = sale_service.get_sale_or_raise(db, sale_id)
    except sale_service.SaleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda nao encontrada.") from None
    return templates.TemplateResponse(
        request=request,
        name="sales/form.html",
        context=_base_context(
            request,
            auth,
            sale=sale,
            products=sale_service.list_active_products(db),
            action=f"/sales/{sale.id}/edit",
            title="Editar venda",
            error=None,
        ),
    )


@router.post("/sales/{sale_id}/edit")
def update_sale(
    request: Request,
    sale_id: int,
    csrf_token: str = Form(...),
    sale_date: str | None = Form(None),
    client_name: str = Form(...),
    product_id: int = Form(...),
    quantity: str = Form(...),
    unit_price: str = Form(...),
    discount_amount: str | None = Form(None),
    unit_cost: str | None = Form(None),
    channel: SaleChannel = Form(SaleChannel.OTHER),
    payment_method: PaymentMethod | None = Form(None),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = SaleUpdate(
            **_payload_from_form(
                sale_date,
                client_name,
                product_id,
                quantity,
                unit_price,
                discount_amount,
                unit_cost,
                channel,
                payment_method,
                notes,
            ).model_dump()
        )
        sale = sale_service.update_sale(db, sale_id, payload)
    except sale_service.SaleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda nao encontrada.") from None
    except (ValidationError, ValueError, sale_service.SaleValidationError):
        sale = sale_service.get_sale_or_raise(db, sale_id)
        return templates.TemplateResponse(
            request=request,
            name="sales/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                sale=sale,
                products=sale_service.list_active_products(db),
                action=f"/sales/{sale.id}/edit",
                title="Editar venda",
                error="Verifique os dados da venda.",
            ),
        )
    return RedirectResponse(f"/sales/{sale.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/sales/{sale_id}/cancel")
def cancel_sale(
    sale_id: int,
    csrf_token: str = Form(...),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    sale_service.cancel_sale(db, sale_id)
    return RedirectResponse(f"/sales/{sale_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/sales/{sale_id}/payments")
def register_payment(
    sale_id: int,
    csrf_token: str = Form(...),
    amount: str = Form(...),
    payment_method: PaymentMethod = Form(...),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        sale_service.register_payment(db, sale_id, PaymentCreate(amount=_decimal(amount), payment_method=payment_method, notes=notes))
    except (ValidationError, ValueError, sale_service.SaleValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pagamento invalido.") from None
    return RedirectResponse(f"/sales/{sale_id}", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("", response_model=list[SaleRead])
def list_sales_api(auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    return sale_service.list_sales(db)


@api_router.get("/{sale_id}", response_model=SaleRead)
def get_sale_api(sale_id: int, auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    try:
        return sale_service.get_sale_or_raise(db, sale_id)
    except sale_service.SaleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda nao encontrada.") from None
