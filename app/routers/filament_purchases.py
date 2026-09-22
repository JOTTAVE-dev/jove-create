from datetime import date
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
from app.models.enums import FilamentMaterial
from app.schemas.filament_purchase import FilamentPurchaseCreate, FilamentPurchaseRead, FilamentPurchaseUpdate
from app.services import filament_purchases as service
from app.services.auth import verify_csrf_token

router = APIRouter(tags=["filament-purchases"])
api_router = APIRouter(prefix="/api/filament-purchases", tags=["api-filament-purchases"])
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


def _base_context(request: Request, auth: CurrentAuth, **extra):
    context = {
        "app_name": get_settings().app_name,
        "current_user": auth.user,
        "csrf_token": _csrf_token(request),
        "format_brl": format_brl,
        "materials": list(FilamentMaterial),
    }
    context.update(extra)
    return context


def _payload(
    brand: str,
    material: FilamentMaterial,
    color: str,
    weight_grams: str,
    material_amount: str,
    shipping_amount: str | None,
    discount_amount: str | None,
    supplier: str,
    purchase_date: date,
    notes: str | None,
):
    return FilamentPurchaseCreate(
        brand=brand,
        material=material,
        color=color,
        weight_grams=_decimal(weight_grams),
        material_amount=_decimal(material_amount),
        shipping_amount=_decimal(shipping_amount),
        discount_amount=_decimal(discount_amount),
        supplier=supplier,
        purchase_date=purchase_date,
        notes=notes,
    )


@router.get("/filament-purchases")
def purchases_page(
    request: Request,
    date_from: date | None = None,
    date_to: date | None = None,
    material: str | None = None,
    supplier: str | None = None,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    purchases = service.list_purchases(db, date_from, date_to, material, supplier)
    return templates.TemplateResponse(
        request=request,
        name="filament_purchases/list.html",
        context=_base_context(
            request,
            auth,
            purchases=purchases,
            chart=service.monthly_chart(db),
            filters={
                "date_from": date_from.isoformat() if date_from else "",
                "date_to": date_to.isoformat() if date_to else "",
                "material": material or "",
                "supplier": supplier or "",
            },
        ),
    )


@router.get("/filament-purchases/new")
def new_purchase_page(request: Request, auth: CurrentAuth = Depends(require_web_auth)):
    return templates.TemplateResponse(
        request=request,
        name="filament_purchases/form.html",
        context=_base_context(
            request,
            auth,
            purchase=None,
            action="/filament-purchases",
            title="Registrar compra de filamento",
            error=None,
        ),
    )


@router.post("/filament-purchases")
def create_purchase(
    request: Request,
    csrf_token: str = Form(...),
    brand: str = Form(...),
    material: FilamentMaterial = Form(...),
    color: str = Form(...),
    weight_grams: str = Form(...),
    material_amount: str = Form(...),
    shipping_amount: str | None = Form(None),
    discount_amount: str | None = Form(None),
    supplier: str = Form(...),
    purchase_date: date = Form(...),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        purchase = service.create_purchase(
            db,
            _payload(brand, material, color, weight_grams, material_amount, shipping_amount, discount_amount, supplier, purchase_date, notes),
        )
    except (ValidationError, ValueError, service.FilamentPurchaseValidationError):
        return templates.TemplateResponse(
            request=request,
            name="filament_purchases/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                purchase=None,
                action="/filament-purchases",
                title="Registrar compra de filamento",
                error="Verifique os dados da compra.",
            ),
        )
    return RedirectResponse(f"/filament-purchases/{purchase.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/filament-purchases/{purchase_id}")
def purchase_detail(
    request: Request,
    purchase_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        purchase = service.get_purchase_or_raise(db, purchase_id)
    except service.FilamentPurchaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compra nao encontrada.") from None
    return templates.TemplateResponse(
        request=request,
        name="filament_purchases/detail.html",
        context=_base_context(request, auth, purchase=purchase),
    )


@router.get("/filament-purchases/{purchase_id}/edit")
def edit_purchase_page(
    request: Request,
    purchase_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        purchase = service.get_purchase_or_raise(db, purchase_id)
    except service.FilamentPurchaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compra nao encontrada.") from None
    return templates.TemplateResponse(
        request=request,
        name="filament_purchases/form.html",
        context=_base_context(
            request,
            auth,
            purchase=purchase,
            action=f"/filament-purchases/{purchase.id}/edit",
            title="Editar compra de filamento",
            error=None,
        ),
    )


@router.post("/filament-purchases/{purchase_id}/edit")
def update_purchase(
    request: Request,
    purchase_id: int,
    csrf_token: str = Form(...),
    brand: str = Form(...),
    material: FilamentMaterial = Form(...),
    color: str = Form(...),
    weight_grams: str = Form(...),
    material_amount: str = Form(...),
    shipping_amount: str | None = Form(None),
    discount_amount: str | None = Form(None),
    supplier: str = Form(...),
    purchase_date: date = Form(...),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = FilamentPurchaseUpdate(
            **_payload(
                brand, material, color, weight_grams, material_amount, shipping_amount, discount_amount, supplier, purchase_date, notes
            ).model_dump()
        )
        purchase = service.update_purchase(db, purchase_id, payload)
    except service.FilamentPurchaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compra nao encontrada.") from None
    except (ValidationError, ValueError, service.FilamentPurchaseValidationError):
        purchase = service.get_purchase_or_raise(db, purchase_id)
        return templates.TemplateResponse(
            request=request,
            name="filament_purchases/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                purchase=purchase,
                action=f"/filament-purchases/{purchase.id}/edit",
                title="Editar compra de filamento",
                error="Verifique os dados da compra.",
            ),
        )
    return RedirectResponse(f"/filament-purchases/{purchase.id}", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("", response_model=list[FilamentPurchaseRead])
def list_purchases_api(auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    return service.list_purchases(db)


@api_router.get("/{purchase_id}", response_model=FilamentPurchaseRead)
def get_purchase_api(purchase_id: int, auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    try:
        return service.get_purchase_or_raise(db, purchase_id)
    except service.FilamentPurchaseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compra nao encontrada.") from None
