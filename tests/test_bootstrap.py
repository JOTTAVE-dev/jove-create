from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base
from app.core.passwords import hash_password, verify_password
from app.models import User
from app.services.bootstrap import ensure_initial_admin


def make_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    return testing_session()


def test_initial_admin_is_created_even_when_other_users_exist(monkeypatch) -> None:
    session = make_session()
    session.add(User(name="Outro", email="outro@jove.local", password_hash=hash_password("senha-antiga")))
    session.commit()

    import app.services.bootstrap as bootstrap

    monkeypatch.setattr(bootstrap, "SessionLocal", lambda: session)
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_EMAIL", "admin1")
    monkeypatch.setenv("ADMIN_PASSWORD", "jove123")

    ensure_initial_admin()

    admin = session.query(User).filter_by(email="admin1").one()
    assert admin.is_active is True
    assert verify_password("jove123", admin.password_hash)

    get_settings.cache_clear()
