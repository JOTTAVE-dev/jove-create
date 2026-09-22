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
from app.models import EquipmentKind, EquipmentMaintenance, EquipmentStatus, User
from app.schemas.equipment import EquipmentCreate, MaintenanceCreate
from app.services import equipments as service
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


def equipment_payload(**overrides):
    payload = {
        "name": "Impressora Bambu Lab A1 Combo",
        "category": "Impressora 3D",
        "kind": EquipmentKind.DURABLE,
        "manufacturer": "Bambu Lab",
        "model": "A1 Combo",
        "purchase_date": date(2026, 9, 22),
        "purchase_cost": Decimal("3500.00"),
        "supplier": "Bambu Store",
        "estimated_life_months": 48,
        "status": EquipmentStatus.ACTIVE,
    }
    payload.update(overrides)
    return EquipmentCreate(**payload)


def test_create_equipment_counts_as_investment_not_production_cost(db_session: Session) -> None:
    equipment = service.create_equipment(db_session, equipment_payload())

    assert equipment.purchase_cost == Decimal("3500.00")
    assert service.total_invested(db_session) == Decimal("3500.00")
    assert equipment.kind == EquipmentKind.DURABLE


def test_consumable_equipment_kind_is_supported(db_session: Session) -> None:
    equipment = service.create_equipment(
        db_session,
        equipment_payload(
            name="Lixa de acabamento",
            category="Ferramentas de acabamento",
            kind=EquipmentKind.CONSUMABLE,
            purchase_cost=Decimal("25.00"),
            estimated_life_months=None,
        ),
    )

    assert equipment.kind == EquipmentKind.CONSUMABLE


def test_add_maintenance_to_equipment(db_session: Session) -> None:
    equipment = service.create_equipment(db_session, equipment_payload())

    service.add_maintenance(
        db_session,
        equipment.id,
        MaintenanceCreate(
            maintenance_date=date(2026, 10, 1),
            description="Troca de bico",
            cost=Decimal("45.00"),
            supplier="Maker Parts",
        ),
    )

    assert db_session.query(EquipmentMaintenance).count() == 1
    assert service.maintenance_total(equipment) == Decimal("45.00")


def test_filter_by_category(db_session: Session) -> None:
    service.create_equipment(db_session, equipment_payload(category="Impressora 3D"))
    service.create_equipment(db_session, equipment_payload(name="Paquimetro", category="Medicao", purchase_cost=Decimal("80.00")))

    results = service.list_equipments(db_session, category="Medicao")

    assert len(results) == 1
    assert results[0].name == "Paquimetro"


def test_authenticated_user_can_create_equipment_from_form(auth_client: TestClient, db_session: Session) -> None:
    csrf_token = auth_client.cookies.get("jove_csrf")
    response = auth_client.post(
        "/equipments",
        data={
            "csrf_token": csrf_token,
            "name": "Paquimetro",
            "category": "Medicao",
            "kind": "durable",
            "manufacturer": "Digital Tools",
            "model": "150mm",
            "purchase_date": "2026-09-22",
            "purchase_cost": "85,00",
            "supplier": "Ferramentas BR",
            "estimated_life_months": "36",
            "status": "active",
            "notes": "Uso para conferencia de pecas",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert service.total_invested(db_session) == Decimal("85.00")


def test_equipments_api_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/equipments")

    assert response.status_code == 401
