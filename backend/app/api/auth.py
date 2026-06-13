from fastapi import APIRouter, Depends, Header

from app.schemas.auth import (
    AuthConfigResponse,
    AuthTokenResponse,
    AuthUserResponse,
    LoginRequest,
    LogoutResponse,
    OAuthTokenRequest,
    RegisterRequest,
)
from app.core.config import settings
from app.services.auth_service import (
    exchange_oauth_token,
    get_current_user,
    login_user,
    logout_token,
    register_user,
)

router = APIRouter()


@router.get("/config", response_model=AuthConfigResponse)
def auth_config():
    provider = str(settings.AUTH_PROVIDER or "supabase").strip().lower()
    supabase_enabled = provider == "supabase"
    return {
        "provider": provider,
        "supabase_url": settings.SUPABASE_URL if supabase_enabled else None,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY if supabase_enabled else None,
    }


@router.post("/register", response_model=AuthTokenResponse)
def register(payload: RegisterRequest):
    return register_user(payload)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest):
    return login_user(payload)


@router.post("/oauth", response_model=AuthTokenResponse)
def oauth_login(payload: OAuthTokenRequest):
    return exchange_oauth_token(payload.access_token)


@router.get("/me", response_model=AuthUserResponse)
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(authorization: str | None = Header(default=None)):
    return logout_token(authorization)
