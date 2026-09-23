from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.currency import format_brl
from app.core.timezone import get_app_timezone
from app.main import app


client = TestClient(app)


def test_health_check_returns_success() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "JOVE Manager",
        "timezone": "America/Fortaleza",
    }


def test_home_renders_initial_page() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_timezone_defaults_to_fortaleza() -> None:
    timezone = get_app_timezone()

    assert timezone.key == "America/Fortaleza"


def test_format_brl_uses_brazilian_currency_format() -> None:
    assert format_brl(Decimal("1234.5")) == "R$ 1.234,50"


def test_settings_accepts_configurable_database_url() -> None:
    settings = Settings(DATABASE_URL="sqlite:///./custom/jove.db")

    assert settings.database_url == "sqlite:///./custom/jove.db"


def test_application_does_not_require_postgresql() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("sqlite")
