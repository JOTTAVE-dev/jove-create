from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.passwords import hash_password
from app.main import app
from app.models import PaymentMethod, PaymentStatus, Product, SaleStatus, User
from app.schemas.sale import PaymentCreate, SaleCreate, SaleItemInput
from app.services import sales as sale_service
from app.services.auth import reset_login_attempts


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
        session.add(Product(name="Chaveiro personalizado", sale_price=Decimal("30.00"), estimated_production_cost=Decimal("8.00")))
        session.commit()
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


def test_sale_calculates_totals_discount_cost_and_profit(db_session: Session) -> None:
    product = db_session.query(Product).one()
    sale = sale_service.create_sale(
        db_session,
        SaleCreate(
            client_name="Cliente",
            items=[
                SaleItemInput(
                    product_id=product.id,
                    quantity=Decimal("2"),
                    unit_price=Decimal("30.00"),
                    discount_amount=Decimal("5.00"),
                    unit_cost=Decimal("8.00"),
                )
            ],
        ),
    )

    assert sale.subtotal_amount == Decimal("60.00")
    assert sale.discount_amount == Decimal("5.00")
    assert sale.total_amount == Decimal("55.00")
    assert sale.total_cost == Decimal("16.00")
    assert sale.gross_profit == Decimal("39.00")
    assert sale.payment_status == PaymentStatus.PENDING


def test_sale_preserves_product_price_history(db_session: Session) -> None:
    product = db_session.query(Product).one()
    sale = sale_service.create_sale(
        db_session,
        SaleCreate(client_name="Cliente", items=[SaleItemInput(product_id=product.id, quantity=Decimal("1"), unit_price=Decimal("30.00"))]),
    )
    product.sale_price = Decimal("99.00")
    db_session.add(product)
    db_session.commit()
    db_session.refresh(sale)

    assert sale.items[0].unit_price == Decimal("30.00")


def test_register_partial_and_full_payment(db_session: Session) -> None:
    product = db_session.query(Product).one()
    sale = sale_service.create_sale(
        db_session,
        SaleCreate(client_name="Cliente", items=[SaleItemInput(product_id=product.id, quantity=Decimal("1"), unit_price=Decimal("100.00"))]),
    )

    sale_service.register_payment(db_session, sale.id, PaymentCreate(amount=Decimal("40.00"), payment_method=PaymentMethod.PIX))
    assert sale.payment_status == PaymentStatus.PARTIALLY_PAID
    assert sale.amount_paid == Decimal("40.00")

    sale_service.register_payment(db_session, sale.id, PaymentCreate(amount=Decimal("60.00"), payment_method=PaymentMethod.CASH))
    assert sale.payment_status == PaymentStatus.PAID
    assert sale.status == SaleStatus.PAID
    assert sale.amount_paid == Decimal("100.00")


def test_cancel_sale_marks_payment_as_canceled(db_session: Session) -> None:
    product = db_session.query(Product).one()
    sale = sale_service.create_sale(
        db_session,
        SaleCreate(client_name="Cliente", items=[SaleItemInput(product_id=product.id, quantity=Decimal("1"), unit_price=Decimal("50.00"))]),
    )

    sale_service.cancel_sale(db_session, sale.id)

    assert sale.status == SaleStatus.CANCELED
    assert sale.payment_status == PaymentStatus.CANCELED


def test_authenticated_user_can_create_sale_from_form(auth_client: TestClient, db_session: Session) -> None:
    product = db_session.query(Product).one()
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/sales",
        data={
            "csrf_token": csrf_token,
            "client_name": "Cliente Web",
            "product_id": str(product.id),
            "quantity": "2",
            "unit_price": "25,00",
            "discount_amount": "5,00",
            "unit_cost": "8,00",
            "channel": "whatsapp",
            "payment_method": "pix",
            "notes": "Entrega combinada",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    sale = sale_service.list_sales(db_session, client_query="Cliente Web")[0]
    assert sale.total_amount == Decimal("45.00")
    assert sale.gross_profit == Decimal("29.00")


def test_sales_api_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/sales")

    assert response.status_code == 401
