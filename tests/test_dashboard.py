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


def seed_dashboard_data(db: Session) -> None:
    client = Client(name="Cliente Dashboard")
    operating_category = FinancialCategory(
        name="Energia eletrica",
        category_type=FinancialCategoryType.OPERATING_EXPENSE,
    )
    inventory_category = FinancialCategory(
        name="Compras de estoque",
        category_type=FinancialCategoryType.INVENTORY_PURCHASE,
    )
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
    operating_expense = Expense(
        category=operating_category,
        description="Energia",
        amount=Decimal("40.00"),
        expense_date=date(2026, 9, 15),
        status=ExpenseStatus.PENDING,
    )
    non_operating_expense = Expense(
        category=inventory_category,
        description="Nao deve entrar como despesa operacional",
        amount=Decimal("500.00"),
        expense_date=date(2026, 9, 15),
        status=ExpenseStatus.PENDING,
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

    db.add_all([sale, canceled_sale, operating_expense, non_operating_expense, filament_purchase, equipment])
    db.commit()


def metric_value(dashboard: dict[str, object], label: str) -> str:
    metric = next(item for item in dashboard["metrics"] if item["label"] == label)
    return metric["value"]


def test_dashboard_calculates_financial_indicators_without_double_counting(db_session: Session) -> None:
    seed_dashboard_data(db_session)

    dashboard = build_dashboard(
        db_session,
        preset="custom",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 30),
    )

    assert metric_value(dashboard, "Faturamento") == "R$ 180,00"
    assert metric_value(dashboard, "Recebido") == "R$ 100,00"
    assert metric_value(dashboard, "Pendente") == "R$ 80,00"
    assert metric_value(dashboard, "Custo vendido") == "R$ 60,00"
    assert metric_value(dashboard, "Despesas operacionais") == "R$ 40,00"
    assert metric_value(dashboard, "Lucro bruto") == "R$ 120,00"
    assert metric_value(dashboard, "Lucro operacional") == "R$ 80,00"
    assert metric_value(dashboard, "Compras de filamentos") == "R$ 100,00"
    assert metric_value(dashboard, "Investimentos") == "R$ 80,00"
    assert metric_value(dashboard, "Vendas") == "1"
    assert metric_value(dashboard, "Ticket medio") == "R$ 180,00"


def test_dashboard_charts_use_real_database_rows(db_session: Session) -> None:
    seed_dashboard_data(db_session)

    dashboard = build_dashboard(
        db_session,
        preset="custom",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 30),
    )

    assert dashboard["charts"]["revenue_by_month"][0]["formatted"] == "R$ 180,00"
    assert dashboard["charts"]["expenses_by_category"][0]["label"] == "Energia eletrica"
    assert dashboard["charts"]["sales_by_channel"][0]["label"] == "WhatsApp"
    assert dashboard["charts"]["purchases_by_material"][0]["formatted"] == "R$ 100,00"


def test_authenticated_dashboard_renders_real_indicators(auth_client: TestClient, db_session: Session) -> None:
    seed_dashboard_data(db_session)

    response = auth_client.get("/?preset=custom&date_from=2026-09-01&date_to=2026-09-30")

    assert response.status_code == 200
    assert "Dashboard financeiro" in response.text
    assert "R$ 180,00" in response.text
    assert "Dados temporarios" not in response.text
