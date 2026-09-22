from collections.abc import Generator
from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.passwords import hash_password
from app.main import app
from app.models import (
    Client,
    Equipment,
    Expense,
    ExpenseStatus,
    FilamentMaterial,
    FilamentPurchase,
    FinancialCategory,
    FinancialCategoryType,
    PaymentMethod,
    PaymentStatus,
    Sale,
    SaleChannel,
    SalePayment,
    SaleStatus,
    User,
)
from app.services.auth import reset_login_attempts
from app.services.dashboard import build_dashboard
from app.services.reports import ReportFilters, build_report, report_to_csv


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    with testing_session() as session:
        session.add(User(name="Admin", email="admin@jove.local", password_hash=hash_password("senha-segura")))
        seed_report_data(session)
        yield session


@pytest.fixture()
def auth_client(db_session: Session) -> Generator[TestClient, None, None]:
    reset_login_attempts()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        client.post("/login", data={"email": "admin@jove.local", "password": "senha-segura"}, follow_redirects=False)
        yield client
    app.dependency_overrides.clear()
    reset_login_attempts()


def seed_report_data(db: Session) -> None:
    client = Client(name="Cliente Relatorio")
    category = FinancialCategory(name="Energia", category_type=FinancialCategoryType.OPERATING_EXPENSE)
    sale = Sale(
        client=client,
        status=SaleStatus.OPEN,
        payment_status=PaymentStatus.PARTIALLY_PAID,
        channel=SaleChannel.WHATSAPP,
        payment_method=PaymentMethod.PIX,
        sale_date=datetime(2026, 9, 10, 9, 0, 0),
        subtotal_amount=Decimal("200.00"),
        discount_amount=Decimal("20.00"),
        total_amount=Decimal("180.00"),
        total_cost=Decimal("60.00"),
        gross_profit=Decimal("120.00"),
        amount_paid=Decimal("100.00"),
    )
    sale.payments.append(
        SalePayment(
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.PIX,
            paid_at=datetime(2026, 9, 11, 10, 0, 0),
        )
    )
    canceled_sale = Sale(
        client=client,
        status=SaleStatus.CANCELED,
        payment_status=PaymentStatus.CANCELED,
        channel=SaleChannel.INSTAGRAM,
        sale_date=datetime(2026, 9, 12, 9, 0, 0),
        total_amount=Decimal("999.00"),
        total_cost=Decimal("10.00"),
        gross_profit=Decimal("989.00"),
        amount_paid=Decimal("999.00"),
    )
    expense = Expense(
        category=category,
        description="Energia",
        amount=Decimal("40.00"),
        expense_date=date(2026, 9, 15),
        paid_at=date(2026, 9, 20),
        payment_method=PaymentMethod.PIX,
        status=ExpenseStatus.PAID,
    )
    filament_purchase = FilamentPurchase(
        brand="Marca",
        material=FilamentMaterial.PLA,
        color="Branco",
        weight_grams=Decimal("1000.000"),
        material_amount=Decimal("90.00"),
        shipping_amount=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        total_cost=Decimal("100.00"),
        cost_per_gram=Decimal("0.100000"),
        supplier="Fornecedor",
        purchase_date=date(2026, 9, 16),
    )
    equipment = Equipment(
        name="Paquimetro",
        equipment_type="Ferramenta",
        category="Medicao",
        purchase_date=date(2026, 9, 17),
        purchase_cost=Decimal("80.00"),
    )

    db.add_all([sale, canceled_sale, expense, filament_purchase, equipment])
    db.commit()


def test_reports_use_same_overview_values_as_dashboard(db_session: Session) -> None:
    filters = ReportFilters("sales", "custom", date(2026, 9, 1), date(2026, 9, 30))

    report = build_report(db_session, filters)
    dashboard = build_dashboard(db_session, "custom", date(2026, 9, 1), date(2026, 9, 30))

    assert report["summary"][0]["value"] == dashboard["metrics"][0]["value"]
    assert report["summary"][1]["value"] == dashboard["metrics"][1]["value"]
    assert report["overview"].estimated_operating_profit == Decimal("80.00")


def test_report_filters_by_sale_channel(db_session: Session) -> None:
    report = build_report(
        db_session,
        ReportFilters("sales", "custom", date(2026, 9, 1), date(2026, 9, 30), channel="instagram"),
    )

    assert report["overview"].revenue == Decimal("0.00")
    assert report["rows"] == []


def test_report_csv_export_uses_semicolon_and_brazilian_decimal(db_session: Session) -> None:
    report = build_report(db_session, ReportFilters("sales", "custom", date(2026, 9, 1), date(2026, 9, 30)))

    csv_content = report_to_csv(report)

    assert "Data;Cliente;Canal" in csv_content
    assert "180,00" in csv_content


def test_authenticated_user_can_view_reports(auth_client: TestClient) -> None:
    response = auth_client.get("/reports?report_type=sales&preset=custom&date_from=2026-09-01&date_to=2026-09-30")

    assert response.status_code == 200
    assert "Relatorios" in response.text
    assert "R$ 180,00" in response.text


def test_authenticated_user_can_export_report_csv(auth_client: TestClient) -> None:
    response = auth_client.get("/reports/export.csv?report_type=sales&preset=custom&date_from=2026-09-01&date_to=2026-09-30")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Cliente Relatorio" in response.text
