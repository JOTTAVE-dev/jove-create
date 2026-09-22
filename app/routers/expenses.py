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
from app.models.enums import ExpenseStatus, PaymentMethod
from app.schemas.expense import ExpenseCreate, ExpensePayment, ExpenseUpdate
from app.services import expenses as service
from app.services.auth import verify_csrf_token

router = APIRouter(tags=["expenses"])
api_router = APIRouter(prefix="/api/expenses", tags=["api-expenses"])
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
        "payment_methods": list(PaymentMethod),
        "statuses": list(ExpenseStatus),
    }
    context.update(extra)
    return context


def _payload(
    description: str,
    category_name: str,
    amount: str,
    expense_date: date,
    due_date: date | None,
    paid_at: date | None,
    payment_method: PaymentMethod | None,
    status_value: ExpenseStatus,
    notes: str | None,
    is_recurring: str | None,
    recurrence_months: str | None,
):
    return ExpenseCreate(
        description=description,
        category_name=category_name,
        amount=_decimal(amount),
        expense_date=expense_date,
        due_date=due_date,
        paid_at=paid_at,
        payment_method=payment_method,
        status=status_value,
        notes=notes,
        is_recurring=is_recurring == "on",
        recurrence_months=_int_or_none(recurrence_months),
    )


@router.get("/expenses")
def expenses_page(
    request: Request,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    status_filter: str | None = None,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    expenses = service.list_expenses(db, date_from, date_to, category_id, status_filter)
    return templates.TemplateResponse(
        request=request,
        name="expenses/list.html",
        context=_base_context(
            request,
            auth,
            expenses=expenses,
            categories=service.categories(db),
            indicators=service.indicators_by_category(db, date_from, date_to),
            filters={
                "date_from": date_from.isoformat() if date_from else "",
                "date_to": date_to.isoformat() if date_to else "",
                "category_id": category_id or "",
                "status_filter": status_filter or "",
            },
        ),
    )


@router.get("/expenses/new")
def new_expense_page(request: Request, auth: CurrentAuth = Depends(require_web_auth), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="expenses/form.html",
        context=_base_context(request, auth, expense=None, categories=service.categories(db), action="/expenses", title="Cadastrar despesa", error=None),
    )


@router.post("/expenses")
def create_expense(
    request: Request,
    csrf_token: str = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    amount: str = Form(...),
    expense_date: date = Form(...),
    due_date: date | None = Form(None),
    paid_at: date | None = Form(None),
    payment_method: PaymentMethod | None = Form(None),
    status_value: ExpenseStatus = Form(ExpenseStatus.PENDING, alias="status"),
    notes: str | None = Form(None),
    is_recurring: str | None = Form(None),
    recurrence_months: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        expense = service.create_expense(
            db,
            _payload(
                description,
                category_name,
                amount,
                expense_date,
                due_date,
                paid_at,
                payment_method,
                status_value,
                notes,
                is_recurring,
                recurrence_months,
            ),
        )
    except (ValidationError, ValueError):
        return templates.TemplateResponse(
            request=request,
            name="expenses/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(request, auth, expense=None, categories=service.categories(db), action="/expenses", title="Cadastrar despesa", error="Verifique os dados."),
        )
    return RedirectResponse(f"/expenses/{expense.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/expenses/{expense_id}")
def expense_detail(request: Request, expense_id: int, auth: CurrentAuth = Depends(require_web_auth), db: Session = Depends(get_db)):
    try:
        expense = service.get_expense_or_raise(db, expense_id)
    except service.ExpenseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa nao encontrada.") from None
    return templates.TemplateResponse(request=request, name="expenses/detail.html", context=_base_context(request, auth, expense=expense))


@router.get("/expenses/{expense_id}/edit")
def edit_expense_page(
    request: Request,
    expense_id: int,
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    expense = service.get_expense_or_raise(db, expense_id)
    return templates.TemplateResponse(
        request=request,
        name="expenses/form.html",
        context=_base_context(
            request,
            auth,
            expense=expense,
            categories=service.categories(db),
            action=f"/expenses/{expense.id}/edit",
            title="Editar despesa",
            error=None,
        ),
    )


@router.post("/expenses/{expense_id}/edit")
def update_expense(
    request: Request,
    expense_id: int,
    csrf_token: str = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    amount: str = Form(...),
    expense_date: date = Form(...),
    due_date: date | None = Form(None),
    paid_at: date | None = Form(None),
    payment_method: PaymentMethod | None = Form(None),
    status_value: ExpenseStatus = Form(ExpenseStatus.PENDING, alias="status"),
    notes: str | None = Form(None),
    is_recurring: str | None = Form(None),
    recurrence_months: str | None = Form(None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    try:
        payload = ExpenseUpdate(
            **_payload(
                description,
                category_name,
                amount,
                expense_date,
                due_date,
                paid_at,
                payment_method,
                status_value,
                notes,
                is_recurring,
                recurrence_months,
            ).model_dump()
        )
        expense = service.update_expense(db, expense_id, payload)
    except service.ExpenseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa nao encontrada.") from None
    except (ValidationError, ValueError):
        expense = service.get_expense_or_raise(db, expense_id)
        return templates.TemplateResponse(
            request=request,
            name="expenses/form.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=_base_context(
                request,
                auth,
                expense=expense,
                categories=service.categories(db),
                action=f"/expenses/{expense.id}/edit",
                title="Editar despesa",
                error="Verifique os dados.",
            ),
        )
    return RedirectResponse(f"/expenses/{expense.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/expenses/{expense_id}/payments")
def register_payment(
    expense_id: int,
    csrf_token: str = Form(...),
    paid_at: date = Form(...),
    payment_method: PaymentMethod = Form(...),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    service.register_payment(db, expense_id, ExpensePayment(paid_at=paid_at, payment_method=payment_method))
    return RedirectResponse(f"/expenses/{expense_id}", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("")
def list_expenses_api(auth: CurrentAuth = Depends(require_api_auth), db: Session = Depends(get_db)):
    return service.list_expenses(db)
