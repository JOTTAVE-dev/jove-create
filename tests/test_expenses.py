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
from app.models import EquipmentKind, ExpenseStatus, FilamentMaterial, PaymentMethod, User
from app.schemas.equipment import EquipmentCreate
from app.schemas.expense import ExpenseCreate, ExpensePayment
from app.schemas.filament_purchase import FilamentPurchaseCreate
from app.services import equipments, expenses, filament_purchases
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


def expense_payload(**overrides):
    payload = {
        "description": "Energia eletrica",
        "category_name": "Energia eletrica",
        "amount": Decimal("220.00"),
        "expense_date": date(2026, 9, 22),
        "due_date": date(2026, 9, 30),
    }
    payload.update(overrides)
    return ExpenseCreate(**payload)


def test_create_and_pay_operational_expense(db_session: Session) -> None:
    expense = expenses.create_expense(db_session, expense_payload())

    assert expense.status == ExpenseStatus.PENDING
    assert expense.paid_at is None

    expenses.register_payment(
        db_session,
        expense.id,
        ExpensePayment(paid_at=date(2026, 9, 25), payment_method=PaymentMethod.PIX),
    )

    assert expense.status == ExpenseStatus.PAID
    assert expense.payment_method == PaymentMethod.PIX


def test_overdue_status_is_detected(db_session: Session) -> None:
    expense = expenses.create_expense(db_session, expense_payload(due_date=date(2020, 1, 1)))

    assert expenses.effective_status(expense, today=date(2020, 1, 2)) == ExpenseStatus.OVERDUE


def test_recurring_expense_does_not_auto_duplicate(db_session: Session) -> None:
    expense = expenses.create_expense(
        db_session,
        expense_payload(is_recurring=True, recurrence_months=1),
    )

    assert expense.recurring_key == "energia eletrica:energia eletrica:2026-09"
    assert len(expenses.list_expenses(db_session)) == 1


def test_indicators_ignore_filament_and_equipment_purchases(db_session: Session) -> None:
    expenses.create_expense(db_session, expense_payload(amount=Decimal("220.00")))
    filament_purchases.create_purchase(
        db_session,
        FilamentPurchaseCreate(
            brand="Jayo",
            material=FilamentMaterial.PLA,
            color="Branco",
            weight_grams=Decimal("1000"),
            material_amount=Decimal("90.00"),
            shipping_amount=Decimal("10.00"),
            discount_amount=Decimal("0"),
            supplier="Maker",
            purchase_date=date(2026, 9, 22),
        ),
    )
    equipments.create_equipment(
        db_session,
        EquipmentCreate(
            name="Paquimetro",
            category="Medicao",
            kind=EquipmentKind.DURABLE,
            purchase_date=date(2026, 9, 22),
            purchase_cost=Decimal("85.00"),
        ),
    )

    indicators = expenses.indicators_by_category(db_session)

    assert len(indicators) == 1
    assert indicators[0]["total"] == Decimal("220.00")


def test_authenticated_user_can_create_expense_from_form(auth_client: TestClient, db_session: Session) -> None:
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/expenses",
        data={
            "csrf_token": csrf_token,
            "description": "Embalagens kraft",
            "category_name": "Embalagens",
            "amount": "45,90",
            "expense_date": "2026-09-22",
            "due_date": "2026-09-30",
            "payment_method": "pix",
            "status": "pending",
            "notes": "Caixas e papel",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert expenses.list_expenses(db_session)[0].amount == Decimal("45.90")


def test_expenses_api_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/expenses")

    assert response.status_code == 401
