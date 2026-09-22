from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import AuthSession, User
from app.services.auth import get_session_by_token


@dataclass
class CurrentAuth:
    user: User
    session: AuthSession


def get_optional_auth(request: Request, db: Session = Depends(get_db)) -> CurrentAuth | None:
    settings = get_settings()
    raw_token = request.cookies.get(settings.session_cookie_name)
    session = get_session_by_token(db, raw_token)
    if session is None:
        return None
    return CurrentAuth(user=session.user, session=session)


def require_web_auth(auth: CurrentAuth | None = Depends(get_optional_auth)) -> CurrentAuth:
    if auth is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return auth


def require_api_auth(auth: CurrentAuth | None = Depends(get_optional_auth)) -> CurrentAuth:
    if auth is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nao autenticado.")
    return auth


def redirect_if_authenticated(auth: CurrentAuth | None) -> RedirectResponse | None:
    if auth is None:
        return None
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
