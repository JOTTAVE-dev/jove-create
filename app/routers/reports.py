from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import CurrentAuth, require_api_auth, require_web_auth
from app.core.config import get_settings
from app.core.currency import format_brl
from app.core.database import get_db
from app.services.reports import ReportFilters, build_report, report_to_csv

router = APIRouter(prefix="/reports", tags=["reports"])
api_router = APIRouter(prefix="/api/reports", tags=["api", "reports"])
templates = Jinja2Templates(directory="app/templates")


def _filters(
    report_type: str = Query(default="sales"),
    preset: str | None = Query(default="current_month"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
) -> ReportFilters:
    parsed_category_id = int(category_id) if category_id and category_id.isdigit() else None
    return ReportFilters(
        report_type=report_type,
        preset=preset,
        date_from=date_from,
        date_to=date_to,
        category_id=parsed_category_id,
        channel=channel or None,
    )


@router.get("")
def list_reports(
    request: Request,
    filters: ReportFilters = Depends(_filters),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    report = build_report(db, filters)
    return templates.TemplateResponse(
        request=request,
        name="reports/list.html",
        context={
            "app_name": settings.app_name,
            "current_user": auth.user,
            "csrf_token": request.cookies.get(settings.csrf_cookie_name, ""),
            "format_brl": format_brl,
            "report": report,
        },
    )


@router.get("/export.csv")
def export_report_csv(
    filters: ReportFilters = Depends(_filters),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    report = build_report(db, filters)
    csv_content = report_to_csv(report)
    filename = f"jove-{report['report_type']}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.get("")
def read_report_api(
    filters: ReportFilters = Depends(_filters),
    auth: CurrentAuth = Depends(require_api_auth),
    db: Session = Depends(get_db),
):
    report = build_report(db, filters)
    return {
        "report_type": report["report_type"],
        "period": {
            "date_from": report["period"].date_from.isoformat(),
            "date_to": report["period"].date_to.isoformat(),
        },
        "summary": report["summary"],
        "rows": report["rows"],
    }
