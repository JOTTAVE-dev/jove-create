from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.passwords import hash_password, verify_password
from app.main import app
from app.models import AuthSession, User
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
        yield client
    app.dependency_overrides.clear()
    reset_login_attempts()


def login(client: TestClient, password: str = "senha-segura"):
    return client.post(
        "/login",
        data={"email": "admin@jove.local", "password": password},
        follow_redirects=False,
    )


def test_password_hash_does_not_store_plain_text() -> None:
    password_hash = hash_password("senha-segura")

    assert password_hash != "senha-segura"
    assert verify_password("senha-segura", password_hash)
    assert not verify_password("senha-errada", password_hash)


def test_login_creates_http_only_session_cookie(auth_client: TestClient, db_session: Session) -> None:
    response = login(auth_client)

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "httponly" in response.headers["set-cookie"].lower()
    assert db_session.query(AuthSession).count() == 1


def test_private_dashboard_requires_authentication(auth_client: TestClient) -> None:
    response = auth_client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_authenticated_user_can_access_dashboard(auth_client: TestClient) -> None:
    login(auth_client)
    response = auth_client.get("/")

    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_api_route_requires_authentication(auth_client: TestClient) -> None:
    response = auth_client.get("/api/me")

    assert response.status_code == 401


def test_authenticated_api_route_returns_current_user(auth_client: TestClient) -> None:
    login(auth_client)
    response = auth_client.get("/api/me")

    assert response.status_code == 200
    assert response.json()["email"] == "admin@jove.local"


def test_login_error_is_generic(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/login",
        data={"email": "missing@jove.local", "password": "qualquer"},
    )

    assert response.status_code == 401
    assert "E-mail ou senha invalidos." in response.text
    assert "missing" not in response.text


def test_excessive_login_attempts_are_limited(auth_client: TestClient) -> None:
    for _ in range(5):
        auth_client.post(
            "/login",
            data={"email": "admin@jove.local", "password": "errada"},
        )

    response = auth_client.post(
        "/login",
        data={"email": "admin@jove.local", "password": "senha-segura"},
    )

    assert response.status_code == 429
    assert "Muitas tentativas" in response.text


def test_change_password_requires_csrf(auth_client: TestClient) -> None:
    login(auth_client)
    response = auth_client.post(
        "/settings/password",
        data={
            "current_password": "senha-segura",
            "new_password": "nova-senha",
            "confirm_password": "nova-senha",
            "csrf_token": "token-invalido",
        },
    )

    assert response.status_code == 403


def test_logout_requires_valid_csrf(auth_client: TestClient) -> None:
    login(auth_client)
    response = auth_client.post(
        "/logout",
        data={"csrf_token": "token-invalido"},
        follow_redirects=False,
    )

    assert response.status_code == 403


def test_authenticated_user_can_change_password(auth_client: TestClient) -> None:
    login(auth_client)
    csrf_token = auth_client.cookies.get("jove_csrf")

    response = auth_client.post(
        "/settings/password",
        data={
            "current_password": "senha-segura",
            "new_password": "nova-senha",
            "confirm_password": "nova-senha",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert "Senha alterada com sucesso." in response.text

    logout_response = auth_client.post("/logout", data={"csrf_token": csrf_token}, follow_redirects=False)
    assert logout_response.status_code == 303

    new_login = auth_client.post(
        "/login",
        data={"email": "admin@jove.local", "password": "nova-senha"},
        follow_redirects=False,
    )
    assert new_login.status_code == 303
