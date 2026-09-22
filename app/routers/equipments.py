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
from app.models.enums import EquipmentKind, EquipmentStatus
from app.schemas.equipment import EquipmentCreate, EquipmentRead, EquipmentUpdate, MaintenanceCreate
from app.services import equipments as service
from app.services.auth import verify_csrf_token

router = APIRouter(tags=["equipments"])
api_router = APIRouter(prefix="/api/equipments", tags=["api-equipments"])
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


def _int_or_none(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)


def _base_context(request: Request, auth: CurrentAuth, **extra):
    context = {
        "app_name": get_settings().app_name,
        "current_user": auth.user,
        "csrf_token": _csrf_token(request),
        "format_brl": format_brl,
        "kinds": list(EquipmentKind),
        "statuses": list(EquipmentStatus),
        "maintenance_total": service.maintenance_total,
    }
    context.update(extra)
    return context


def _payload(
    name: str,
    category: str,
    kind: EquipmentKind,
    manufacturer: str | None,
    model: str | None,
    purchase_date: date | None,
    purchase_cost: str | None,
    supplier: str | None,
    estimated_life_months: str | None,
    notes: str | None,
    status_value: EquipmentStatus,
):
    return EquipmentCreate(
        name=name,
        category=category,
        kind=kind,
        manufacturer=manufacturer,
        model=model,
        purchase_date=purchase_date,
        purchase_cost=_decimal(purchase_cost),
        supplier=supplier,
        estimated_life_months=_int_or_none(estimated_life_months),
        notes=notes,
        status=status_value,
    )


@router.get("/equipments")
def equipments_page(
    request: Request,
    category: str | None = None,
    include_inactive: bool = False,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="equipments/list.html",
        context=_base_context(
            request,
            auth,
            equipments=service.list_equipments(db, category, include_inactive),
            categories=service.categories(db),
            total_invested=service.total_invested(db),
            filters={"category": category or "", "include_inactive": include_inactive},
        ),
    )


@router.get("/equipments/new")
def new_equipment_page(request: Request, auth: CurrentAuth = Depends(require_web_auth)):
    return templates.TemplateResponse(
        request=request,
        name="equipments/form.html",
        context=_base_context(
            request,
            auth,
            equipment=None,
            action="/equipments",
            title="Cadastrar equipamento",
            error=None,
        ),
    )


@router.post("/equipments")
def create_equipment(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    kind: EquipmentKind = Form(EquipmentKind.DURABLE),
    manufacturer: str | None = Form(None),
    model: str | None = Form(None),
    purchase_date: date | None = Form(None),
    purchase_cost: str | None = Form(None),
    supplier: str | None = Form(None),
    estimated_life_months: str | None = Form(None),
    notes: str | None = Form(None),
    status_value: EquipmentStatus = Form(EquipmentStatus.ACTIVE, alias="status"),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        equipment = service.create_equipment(
            db,
            _payload(
                name,
                category,
                kind,
                manufacturer,
                model,
                purchase_date,
                purchase_cost,
                supplier,
                estimated_life_months,
                notes,
                status_value,
            ),
        )
    except (ValidationError, ValueError):
        return templates.TemplateResponse(
            request=request,
            name="equipments/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(request, auth, equipment=None, action="/equipments", title="Cadastrar equipamento", error="Verifique os dados."),
        )
    return RedirectResponse(f"/equipments/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/equipments/{equipment_id}")
def equipment_detail(
    request: Request,
    equipment_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    try:
        equipment = service.get_equipment_or_raise(db, equipment_id)
    except service.EquipmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipamento nao encontrado.") from None
    return templates.TemplateResponse(
        request=request,
        name="equipments/detail.html",
        context=_base_context(request, auth, equipment=equipment),
    )


@router.get("/equipments/{equipment_id}/edit")
def edit_equipment_page(
    request: Request,
    equipment_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    equipment = service.get_equipment_or_raise(db, equipment_id)
    return templates.TemplateResponse(
        request=request,
        name="equipments/form.html",
        context=_base_context(
            request,
            auth,
            equipment=equipment,
            action=f"/equipments/{equipment.id}/edit",
            title="Editar equipamento",
            error=None,
        ),
    )


@router.post("/equipments/{equipment_id}/edit")
def update_equipment(
    request: Request,
    equipment_id: int,
    csrf_token: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    kind: EquipmentKind = Form(EquipmentKind.DURABLE),
    manufacturer: str | None = Form(None),
    model: str | None = Form(None),
    purchase_date: date | None = Form(None),
    purchase_cost: str | None = Form(None),
    supplier: str | None = Form(None),
    estimated_life_months: str | None = Form(None),
    notes: str | None = Form(None),
    status_value: EquipmentStatus = Form(EquipmentStatus.ACTIVE, alias="status"),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = EquipmentUpdate(
            **_payload(
                name,
                category,
                kind,
                manufacturer,
                model,
                purchase_date,
                purchase_cost,
                supplier,
                estimated_life_months,
                notes,
                status_value,
            ).model_dump()
        )
        equipment = service.update_equipment(db, equipment_id, payload)
    except service.EquipmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipamento nao encontrado.") from None
    except (ValidationError, ValueError):
        equipment = service.get_equipment_or_raise(db, equipment_id)
        return templates.TemplateResponse(
            request=request,
            name="equipments/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                equipment=equipment,
                action=f"/equipments/{equipment.id}/edit",
                title="Editar equipamento",
                error="Verifique os dados.",
            ),
        )
    return RedirectResponse(f"/equipments/{equipment.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/equipments/{equipment_id}/maintenances")
def add_maintenance(
    equipment_id: int,
    csrf_token: str = Form(...),
    maintenance_date: date = Form(...),
    description: str = Form(...),
    cost: str | None = Form(None),
    supplier: str | None = Form(None),
    notes: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    service.add_maintenance(
        db,
        equipment_id,
        MaintenanceCreate(
            maintenance_date=maintenance_date,
            description=description,
            cost=_decimal(cost),
            supplier=supplier,
            notes=notes,
        ),
    )
    return RedirectResponse(f"/equipments/{equipment_id}", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("", response_model=list[EquipmentRead])
def list_equipments_api(auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    return service.list_equipments(db)


@api_router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment_api(equipment_id: int, auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    try:
        return service.get_equipment_or_raise(db, equipment_id)
    except service.EquipmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipamento nao encontrado.") from None
