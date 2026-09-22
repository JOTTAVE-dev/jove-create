from fastapi import APIRouter, Depends, Form, Request, status
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import CurrentAuth, get_optional_auth, redirect_if_authenticated, require_web_auth
from app.core.config import get_settings
from app.core.database import get_db
from app.services.auth import (
    GENERIC_LOCKOUT_ERROR,
    GENERIC_LOGIN_ERROR,
    authenticate_user,
    change_user_password,
    clear_login_attempts,
    create_auth_session,
    is_login_limited,
    register_failed_login,
    revoke_session,
    verify_csrf_token,
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _set_session_cookies(response: RedirectResponse, request: Request, token: str, csrf_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_expire_minutes * 60,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=settings.session_expire_minutes * 60,
        httponly=False,
        secure=request.url.scheme == "https",
        samesite="lax",
    )


def _clear_session_cookie(response: RedirectResponse) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.session_cookie_name, httponly=True, samesite="lax")
    response.delete_cookie(key=settings.csrf_cookie_name, samesite="lax")


@router.get("/login")
def login_page(request: Request, auth: CurrentAuth | None = Depends(get_optional_auth)):
    redirect = redirect_if_authenticated(auth)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"app_name": get_settings().app_name, "error": None},
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ip_address = _client_ip(request)
    if is_login_limited(email, ip_address):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            context={"app_name": get_settings().app_name, "error": GENERIC_LOCKOUT_ERROR},
        )

    user = authenticate_user(db, email, password)
    if user is None:
        register_failed_login(email, ip_address)
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            status_code=status.HTTP_401_UNAUTHORIZED,
            context={"app_name": get_settings().app_name, "error": GENERIC_LOGIN_ERROR},
        )

    clear_login_attempts(email, ip_address)
    created_session = create_auth_session(db, user, request.headers.get("user-agent"))
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    _set_session_cookies(response, request, created_session.raw_token, created_session.csrf_token)
    return response


@router.post("/logout")
def logout(
    csrf_token: str = Form(...),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    if not verify_csrf_token(auth.session, csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF invalido.")
    revoke_session(db, auth.session)
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    _clear_session_cookie(response)
    return response


@router.get("/settings/password")
def change_password_page(request: Request, auth: CurrentAuth = Depends(require_web_auth)):
    csrf_token = request.cookies.get(get_settings().csrf_cookie_name, "")
    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={
            "app_name": get_settings().app_name,
            "current_user": auth.user,
            "csrf_token": csrf_token,
            "error": None,
            "success": None,
        },
    )


@router.post("/settings/password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    auth: CurrentAuth = Depends(require_web_auth),
    db: Session = Depends(get_db),
):
    from app.core.passwords import verify_password

    context = {
        "app_name": get_settings().app_name,
        "current_user": auth.user,
        "csrf_token": csrf_token,
        "error": None,
        "success": None,
    }

    if not verify_csrf_token(auth.session, csrf_token):
        context["error"] = "Nao foi possivel validar a requisicao."
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            status_code=status.HTTP_403_FORBIDDEN,
            context=context,
        )

    if new_password != confirm_password or len(new_password) < 8:
        context["error"] = "Nao foi possivel alterar a senha."
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=context,
        )

    if not verify_password(current_password, auth.user.password_hash):
        context["error"] = "Nao foi possivel alterar a senha."
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            context=context,
        )

    change_user_password(db, auth.user, new_password)
    context["success"] = "Senha alterada com sucesso."
    return templates.TemplateResponse(request=request, name="change_password.html", context=context)
