from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.routers.api import router as api_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.home import router as home_router
from app.routers.filament_purchases import api_router as filament_purchases_api_router
from app.routers.filament_purchases import router as filament_purchases_router
from app.routers.equipments import api_router as equipments_api_router
from app.routers.equipments import router as equipments_router
from app.routers.expenses import api_router as expenses_api_router
from app.routers.expenses import router as expenses_router
from app.routers.products import api_router as products_api_router
from app.routers.products import router as products_router
from app.routers.reports import api_router as reports_api_router
from app.routers.reports import router as reports_router
from app.routers.sales import api_router as sales_api_router
from app.routers.sales import router as sales_router
from app.services.bootstrap import ensure_initial_admin


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    ensure_initial_admin()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    application.mount("/static", StaticFiles(directory="app/static"), name="static")
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(api_router)
    application.include_router(equipments_api_router)
    application.include_router(equipments_router)
    application.include_router(expenses_api_router)
    application.include_router(expenses_router)
    application.include_router(filament_purchases_api_router)
    application.include_router(filament_purchases_router)
    application.include_router(products_api_router)
    application.include_router(products_router)
    application.include_router(reports_api_router)
    application.include_router(reports_router)
    application.include_router(sales_api_router)
    application.include_router(sales_router)
    application.include_router(home_router)
    register_exception_handlers(application)

    return application


app = create_app()
