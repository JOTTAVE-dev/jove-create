from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import CurrentAuth, require_web_auth
from app.core.config import get_settings
from app.core.database import get_db
from app.core.timezone import now_local
from app.services.dashboard import build_dashboard

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(
    request: Request,
    preset: str | None = Query(default="current_month"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    dashboard = build_dashboard(db, preset=preset, date_from=date_from, date_to=date_to)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "current_user": auth.user,
            "csrf_token": request.cookies.get(settings.csrf_cookie_name, ""),
            "current_date": now_local().strftime("%d/%m/%Y"),
            "dashboard": dashboard,
            "selected_preset": dashboard["period"].preset,
        },
    )
