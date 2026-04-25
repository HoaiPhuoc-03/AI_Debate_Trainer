from fastapi import APIRouter, Depends, Header

from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserResponse,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
)
from app.services.auth_service import (
    get_current_user,
    login_user,
    logout_token,
    register_user,
)

router = APIRouter()


@router.post("/register", response_model=AuthTokenResponse)
def register(payload: RegisterRequest):
    return register_user(payload)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest):
    return login_user(payload)


@router.get("/me", response_model=AuthUserResponse)
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(authorization: str | None = Header(default=None)):
    return logout_token(authorization)
