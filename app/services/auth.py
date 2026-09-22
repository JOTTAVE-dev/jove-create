from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.passwords import hash_password, verify_password
from app.core.timezone import now_local
from app.core.tokens import generate_token, hash_token, verify_token
from app.models import AuthSession, User


GENERIC_LOGIN_ERROR = "E-mail ou senha invalidos."
GENERIC_LOCKOUT_ERROR = "Muitas tentativas. Tente novamente mais tarde."

_login_attempts: dict[str, list[datetime]] = {}


@dataclass
class CreatedSession:
    raw_token: str
    csrf_token: str
    session: AuthSession


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _now_for_lockout() -> datetime:
    current = now_local()
    if current.tzinfo is not None:
        return current.replace(tzinfo=None)
    return current


def _attempt_key(email: str, ip_address: str) -> str:
    return f"{normalize_email(email)}:{ip_address}"


def is_login_limited(email: str, ip_address: str) -> bool:
    settings = get_settings()
    key = _attempt_key(email, ip_address)
    cutoff = _now_for_lockout() - timedelta(minutes=settings.login_lockout_minutes)
    attempts = [attempt for attempt in _login_attempts.get(key, []) if attempt >= cutoff]
    _login_attempts[key] = attempts
    return len(attempts) >= settings.login_max_attempts


def register_failed_login(email: str, ip_address: str) -> None:
    key = _attempt_key(email, ip_address)
    _login_attempts.setdefault(key, []).append(_now_for_lockout())


def clear_login_attempts(email: str, ip_address: str) -> None:
    _login_attempts.pop(_attempt_key(email, ip_address), None)


def reset_login_attempts() -> None:
    _login_attempts.clear()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized_email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized_email, User.is_active.is_(True)))
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_auth_session(db: Session, user: User, user_agent: str | None = None) -> CreatedSession:
    settings = get_settings()
    raw_token = generate_token()
    csrf_token = generate_token()
    session = AuthSession(
        user=user,
        token_hash=hash_token(raw_token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=now_local() + timedelta(minutes=settings.session_expire_minutes),
        user_agent=user_agent[:255] if user_agent else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return CreatedSession(raw_token=raw_token, csrf_token=csrf_token, session=session)


def _is_expired(expires_at: datetime) -> bool:
    current = now_local()
    if expires_at.tzinfo is None and current.tzinfo is not None:
        current = current.replace(tzinfo=None)
    return expires_at <= current


def get_session_by_token(db: Session, raw_token: str | None) -> AuthSession | None:
    if not raw_token:
        return None

    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(raw_token),
            AuthSession.revoked_at.is_(None),
        )
    )
    if session is None or _is_expired(session.expires_at) or not session.user.is_active:
        return None
    return session


def revoke_session(db: Session, session: AuthSession) -> None:
    session.revoked_at = now_local()
    db.add(session)
    db.commit()


def verify_csrf_token(session: AuthSession, csrf_token: str | None) -> bool:
    if not csrf_token:
        return False
    return verify_token(csrf_token, session.csrf_token_hash)


def change_user_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    user.password_changed_at = now_local()
    db.add(user)
    db.commit()
