from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.passwords import hash_password
from app.models import User
from app.services.auth import normalize_email


def ensure_initial_admin() -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return

    with SessionLocal() as db:
        try:
            existing_user = db.scalar(select(User.id).limit(1))
            if existing_user is not None:
                return

            admin = User(
                name="Administrador",
                email=normalize_email(settings.admin_email),
                password_hash=hash_password(settings.admin_password),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
