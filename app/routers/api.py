from fastapi import APIRouter, Depends

from app.core.auth import CurrentAuth, require_api_auth

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/me")
def read_current_user(auth: CurrentAuth = Depends(require_api_auth)) -> dict[str, str | int]:
    return {
        "id": auth.user.id,
        "name": auth.user.name,
        "email": auth.user.email,
        "role": auth.user.role,
    }
