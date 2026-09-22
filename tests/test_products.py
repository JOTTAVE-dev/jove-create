from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.passwords import hash_password
from app.main import app
from app.models import Product, User
from app.schemas.product import ProductCreate
from app.services import products as product_service
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
        session.add(
            User(
                name="Administrador",
                email="admin@jove.local",
                password_hash=hash_password("senha-segura"),
                role="admin",
                is_active=True,
            )
        )
        session.commit()
        yield session


@pytest.fixture()
def auth_client(db_session: Session) -> Generator[TestClient, None, None]:
    reset_login_attempts()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        client.post(
            "/login",
            data={"email": "admin@jove.local", "password": "senha-segura"},
            follow_redirects=False,
        )
        yield client
    app.dependency_overrides.clear()
    reset_login_attempts()


def test_product_schema_allows_custom_product_without_fixed_price() -> None:
    payload = ProductCreate(
        name="Peca sob encomenda",
        description="Produto personalizado definido com o cliente.",
        category="Sob encomenda",
        sale_price=None,
        is_customizable=True,
    )

    assert payload.sale_price is None
    assert payload.is_customizable is True


def test_product_schema_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(name="Chaveiro", sale_price=Decimal("-1.00"))


def test_create_search_and_deactivate_product(db_session: Session) -> None:
    product = product_service.create_product(
        db_session,
        ProductCreate(
            name="Suporte para celular",
            category="Suportes",
            sale_price=Decimal("45.90"),
            estimated_production_cost=Decimal("14.20"),
            estimated_print_time_minutes=180,
            estimated_weight_grams=Decimal("65.500"),
        ),
    )

    results = product_service.list_products(db_session, query="celular")
    assert [item.id for item in results] == [product.id]

    product_service.deactivate_product(db_session, product.id)

    assert product_service.list_products(db_session, query="celular") == []
    inactive_results = product_service.list_products(db_session, query="celular", include_inactive=True)
    assert inactive_results[0].is_active is False


def test_product_form_accepts_dot_decimal_values(auth_client: TestClient, db_session: Session) -> None:
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/products",
        data={
            "csrf_token": csrf_token,
            "name": "Porta-retrato",
            "description": "",
            "category": "Decoracao",
            "sale_price": "8.50",
            "estimated_production_cost": "3.25",
            "estimated_print_time_minutes": "60",
            "estimated_weight_grams": "20.500",
            "image_url": "",
            "is_customizable": "on",
            "is_active": "on",
        },
        follow_redirects=False,
    )

    product = db_session.query(Product).filter(Product.name == "Porta-retrato").one()

    assert response.status_code == 303
    assert product.sale_price == Decimal("8.50")
    assert product.estimated_production_cost == Decimal("3.25")
    assert product.estimated_weight_grams == Decimal("20.500")


def test_products_page_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/products", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_authenticated_user_can_create_product_from_form(auth_client: TestClient, db_session: Session) -> None:
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/products",
        data={
            "csrf_token": csrf_token,
            "name": "Chaveiro personalizado",
            "description": "Chaveiro com nome do cliente",
            "category": "Personalizados",
            "sale_price": "",
            "estimated_production_cost": "8,50",
            "estimated_print_time_minutes": "45",
            "estimated_weight_grams": "18,250",
            "image_url": "",
            "is_customizable": "on",
            "is_active": "on",
        },
        follow_redirects=False,
    )

    product = db_session.query(Product).filter(Product.name == "Chaveiro personalizado").one()

    assert response.status_code == 303
    assert response.headers["location"] == f"/products/{product.id}"
    assert product.sale_price is None
    assert product.estimated_production_cost == Decimal("8.50")
    assert product.estimated_weight_grams == Decimal("18.250")


def test_product_api_is_authenticated(auth_client: TestClient) -> None:
    with TestClient(app) as anonymous_client:
        anonymous_response = anonymous_client.get("/api/products")

    authenticated_response = auth_client.get("/api/products")

    assert anonymous_response.status_code == 401
    assert authenticated_response.status_code == 200
