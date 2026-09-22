from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.passwords import hash_password
from app.main import app
from app.models import FilamentMaterial, FilamentPurchase, User
from app.schemas.filament_purchase import FilamentPurchaseCreate
from app.services import filament_purchases as service
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


def filament_payload(**overrides):
    payload = {
        "brand": "3D Prime",
        "material": FilamentMaterial.PLA,
        "color": "Branco",
        "weight_grams": Decimal("1000"),
        "material_amount": Decimal("90.00"),
        "shipping_amount": Decimal("10.00"),
        "discount_amount": Decimal("0"),
        "supplier": "Filamentos Brasil",
        "purchase_date": date(2026, 9, 22),
    }
    payload.update(overrides)
    return FilamentPurchaseCreate(**payload)


def test_filament_purchase_calculates_total_and_cost_per_gram(db_session: Session) -> None:
    purchase = service.create_purchase(db_session, filament_payload())

    assert purchase.total_cost == Decimal("100.00")
    assert purchase.cost_per_gram == Decimal("0.100000")


def test_discount_reduces_total_cost(db_session: Session) -> None:
    purchase = service.create_purchase(db_session, filament_payload(discount_amount=Decimal("15.00")))

    assert purchase.total_cost == Decimal("85.00")
    assert purchase.cost_per_gram == Decimal("0.085000")


def test_multiple_purchases_preserve_price_history(db_session: Session) -> None:
    first = service.create_purchase(db_session, filament_payload(material_amount=Decimal("90.00")))
    second = service.create_purchase(db_session, filament_payload(material_amount=Decimal("120.00")))

    assert first.id != second.id
    assert first.cost_per_gram == Decimal("0.100000")
    assert second.cost_per_gram == Decimal("0.130000")
    assert db_session.query(FilamentPurchase).count() == 2


def test_negative_total_is_rejected(db_session: Session) -> None:
    with pytest.raises(service.FilamentPurchaseValidationError):
        service.create_purchase(db_session, filament_payload(discount_amount=Decimal("200.00")))


def test_authenticated_user_can_create_filament_purchase_from_form(auth_client: TestClient, db_session: Session) -> None:
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/filament-purchases",
        data={
            "csrf_token": csrf_token,
            "brand": "Jayo",
            "material": "PLA",
            "color": "Preto",
            "weight_grams": "1000",
            "material_amount": "90,00",
            "shipping_amount": "10,00",
            "discount_amount": "0",
            "supplier": "Maker Shop",
            "purchase_date": "2026-09-22",
            "notes": "Compra para estoque",
        },
        follow_redirects=False,
    )

    purchase = db_session.query(FilamentPurchase).filter(FilamentPurchase.brand == "Jayo").one()

    assert response.status_code == 303
    assert response.headers["location"] == f"/filament-purchases/{purchase.id}"
    assert purchase.total_cost == Decimal("100.00")
    assert purchase.cost_per_gram == Decimal("0.100000")


def test_filament_purchases_api_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/filament-purchases")

    assert response.status_code == 401
