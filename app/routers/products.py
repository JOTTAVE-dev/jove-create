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
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import products as product_service
from app.services.auth import verify_csrf_token

router = APIRouter(tags=["products"])
api_router = APIRouter(prefix="/api/products", tags=["api-products"])
templates = Jinja2Templates(directory="app/templates")


def _csrf_token(request: Request) -> str:
    return request.cookies.get(get_settings().csrf_cookie_name, "")


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _decimal_or_none(value: str | None) -> Decimal | None:
    cleaned = _empty_to_none(value)
    if cleaned is None:
        return None
    normalized = cleaned.replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        raise ValueError("Valor decimal invalido.") from None


def _int_or_none(value: str | None) -> int | None:
    cleaned = _empty_to_none(value)
    if cleaned is None:
        return None
    return int(cleaned)


def _product_payload(
    name: str,
    description: str | None,
    category: str | None,
    sale_price: str | None,
    estimated_production_cost: str | None,
    estimated_print_time_minutes: str | None,
    estimated_weight_grams: str | None,
    image_url: str | None,
    is_customizable: str | None,
    is_active: str | None,
) -> dict[str, object]:
    return {
        "name": name,
        "description": _empty_to_none(description),
        "category": _empty_to_none(category),
        "sale_price": _decimal_or_none(sale_price),
        "estimated_production_cost": _decimal_or_none(estimated_production_cost),
        "estimated_print_time_minutes": _int_or_none(estimated_print_time_minutes),
        "estimated_weight_grams": _decimal_or_none(estimated_weight_grams),
        "image_url": _empty_to_none(image_url),
        "is_customizable": is_customizable == "on",
        "is_active": is_active == "on",
    }


def _base_context(request: Request, auth: CurrentAuth, **extra):
    context = {
        "app_name": get_settings().app_name,
        "current_user": auth.user,
        "csrf_token": _csrf_token(request),
        "format_brl": format_brl,
    }
    context.update(extra)
    return context


@router.get("/products")
def products_page(
    request: Request,
    q: str | None = None,
    include_inactive: bool = False,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    products = product_service.list_products(db, query=q, include_inactive=include_inactive)
    return templates.TemplateResponse(
        request=request,
        name="products/list.html",
        context=_base_context(request, auth, products=products, q=q or "", include_inactive=include_inactive),
    )


@router.get("/products/new")
def new_product_page(request: Request, auth: CurrentAuth = Depends(require_web_auth)):
    return templates.TemplateResponse(
        request=request,
        name="products/form.html",
        context=_base_context(request, auth, product=None, action="/products", title="Cadastrar produto", error=None),
    )


@router.post("/products")
def create_product(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    description: str | None = Form(None),
    category: str | None = Form(None),
    sale_price: str | None = Form(None),
    estimated_production_cost: str | None = Form(None),
    estimated_print_time_minutes: str | None = Form(None),
    estimated_weight_grams: str | None = Form(None),
    image_url: str | None = Form(None),
    is_customizable: str | None = Form(None),
    is_active: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = ProductCreate(
            **_product_payload(
                name,
                description,
                category,
                sale_price,
                estimated_production_cost,
                estimated_print_time_minutes,
                estimated_weight_grams,
                image_url,
                is_customizable,
                is_active,
            )
        )
    except (ValidationError, ValueError):
        return templates.TemplateResponse(
            request=request,
            name="products/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                product=None,
                action="/products",
                title="Cadastrar produto",
                error="Verifique os dados do produto.",
            ),
        )

    product = product_service.create_product(db, payload)
    return RedirectResponse(f"/products/{product.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/products/{product_id}")
def product_detail(
    request: Request,
    product_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        product = product_service.get_product_or_raise(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.") from None

    return templates.TemplateResponse(
        request=request,
        name="products/detail.html",
        context=_base_context(request, auth, product=product),
    )


@router.get("/products/{product_id}/edit")
def edit_product_page(
    request: Request,
    product_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        product = product_service.get_product_or_raise(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.") from None

    return templates.TemplateResponse(
        request=request,
        name="products/form.html",
        context=_base_context(
            request,
            auth,
            product=product,
            action=f"/products/{product.id}/edit",
            title="Editar produto",
            error=None,
        ),
    )


@router.post("/products/{product_id}/edit")
def update_product(
    request: Request,
    product_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    description: str | None = Form(None),
    category: str | None = Form(None),
    sale_price: str | None = Form(None),
    estimated_production_cost: str | None = Form(None),
    estimated_print_time_minutes: str | None = Form(None),
    estimated_weight_grams: str | None = Form(None),
    image_url: str | None = Form(None),
    is_customizable: str | None = Form(None),
    is_active: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = ProductUpdate(
            **_product_payload(
                name,
                description,
                category,
                sale_price,
                estimated_production_cost,
                estimated_print_time_minutes,
                estimated_weight_grams,
                image_url,
                is_customizable,
                is_active,
            )
        )
        product = product_service.update_product(db, product_id, payload)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.") from None
    except (ValidationError, ValueError):
        product = product_service.get_product_or_raise(db, product_id)
        return templates.TemplateResponse(
            request=request,
            name="products/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                product=product,
                action=f"/products/{product.id}/edit",
                title="Editar produto",
                error="Verifique os dados do produto.",
            ),
        )

    return RedirectResponse(f"/products/{product.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}/deactivate")
def deactivate_product(
    product_id: int,
    csrf_token: str = Form(...),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        product_service.deactivate_product(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.") from None
    return RedirectResponse("/products?include_inactive=true", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("", response_model=list[ProductRead])
def list_products_api(
    q: str | None = None,
    include_inactive: bool = False,
    auth: CurrentAuth = Depends(require_api_auth),
    db: Session = Depends(get_db),
):
    return product_service.list_products(db, query=q, include_inactive=include_inactive)


@api_router.get("/{product_id}", response_model=ProductRead)
def get_product_api(
    product_id: int,
    auth: CurrentAuth = Depends(require_api_auth),
    db: Session = Depends(get_db),
):
    try:
        return product_service.get_product_or_raise(db, product_id)
    except product_service.ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado.") from None
