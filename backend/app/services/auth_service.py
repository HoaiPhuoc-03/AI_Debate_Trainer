import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from app.core.config import settings
from app.services.normalization import (
    normalize_age_group,
    normalize_debate_level,
    normalize_language,
    optional_text,
)
from app.services.supabase_store import SupabaseStore
from app.services.session_store import (
    create_auth_session,
    create_user,
    deactivate_auth_session,
    get_auth_session_by_token,
    get_demo_user,
    get_user_by_email,
)

PASSWORD_ITERATIONS = 120_000
SESSION_DAYS = 7


def normalize_email(email: str) -> str:
    return str(email or "").strip().casefold()


def _validate_email(email: str):
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Invalid email")


def _validate_password(password: str):
    if len(password or "") < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "age_group": user.get("age_group"),
        "debate_level": user.get("debate_level"),
        "language": user.get("language") or "vi",
    }


def _session_user(auth_session: dict) -> dict:
    return {
        "id": auth_session["user_id"],
        "email": auth_session["email"],
        "display_name": auth_session["display_name"],
        "age_group": auth_session.get("age_group"),
        "debate_level": auth_session.get("debate_level"),
        "language": auth_session.get("language") or "vi",
    }


def _expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)


def _is_expired(expires_at: str | datetime | None) -> bool:
    if not expires_at:
        return False
    if isinstance(expires_at, datetime):
        expires = expires_at
    else:
        try:
            val_str = str(expires_at).strip()
            if " " in val_str:
                expires = datetime.strptime(val_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            else:
                expires = datetime.fromisoformat(val_str)
        except (ValueError, TypeError):
            return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires <= datetime.now(timezone.utc)



def issue_token_for_user(user: dict) -> dict:
    token = secrets.token_urlsafe(32)
    auth_session = create_auth_session(
        user_id=user["id"],
        token=token,
        expires_at=_expires_at(),
    )
    return {
        "token": auth_session["token"],
        "token_type": "bearer",
        "user": _session_user(auth_session),
    }


def _legacy_register_user(payload) -> dict:
    email = normalize_email(payload.email)
    _validate_email(email)
    _validate_password(payload.password)

    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")

    display_name = optional_text(payload.display_name) or email.split("@")[0]
    user = create_user(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=display_name,
        age_group=normalize_age_group(payload.age_group),
        debate_level=normalize_debate_level(payload.debate_level),
        language=normalize_language(payload.language),
    )
    return issue_token_for_user(user)


def _legacy_login_user(payload) -> dict:
    email = normalize_email(payload.email)
    _validate_email(email)
    user = get_user_by_email(email)

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return issue_token_for_user(user)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return token.strip()


def _legacy_get_user_from_token(token: str) -> dict:
    auth_session = get_auth_session_by_token(token)
    if (
        not auth_session
        or int(auth_session.get("is_active") or 0) != 1
        or _is_expired(auth_session.get("expires_at"))
    ):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return _session_user(auth_session)


def _auth_provider() -> str:
    provider = str(settings.AUTH_PROVIDER or "firebase").strip().lower()
    if provider not in {"firebase", "supabase"}:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unsupported AUTH_PROVIDER '{provider}'. "
                "Use 'firebase' or 'supabase'."
            ),
        )
    return provider


def _supabase_profile(
    auth_user: dict,
    *,
    age_group: str | None = None,
    debate_level: str | None = None,
    language: str | None = None,
) -> dict:
    metadata = dict(auth_user.get("metadata") or {})
    profile = SupabaseStore().ensure_profile(
        auth_user["id"],
        email=auth_user.get("email"),
        display_name=auth_user.get("display_name"),
        age_group=age_group or metadata.get("age_group"),
        debate_level=debate_level or metadata.get("debate_level"),
        language=language or metadata.get("language"),
        metadata={"auth_source": "supabase_auth"},
    )
    return _public_user(profile)


def _supabase_token_response(result: dict, user: dict) -> dict:
    access_token = result.get("access_token")
    return {
        "token": access_token,
        "access_token": access_token,
        "refresh_token": result.get("refresh_token"),
        "token_type": result.get("token_type") or "bearer",
        "user": user,
        "message": result.get("message"),
    }


def register_user(payload) -> dict:
    if _auth_provider() == "firebase":
        return _legacy_register_user(payload)

    email = normalize_email(payload.email)
    _validate_email(email)
    _validate_password(payload.password)
    display_name = optional_text(payload.display_name) or email.split("@", 1)[0]

    from app.services.supabase_auth_service import sign_up_with_email

    result = sign_up_with_email(email, payload.password, display_name)
    user = _supabase_profile(
        result["user"],
        age_group=normalize_age_group(payload.age_group),
        debate_level=normalize_debate_level(payload.debate_level),
        language=normalize_language(payload.language),
    )
    return _supabase_token_response(result, user)


def login_user(payload) -> dict:
    if _auth_provider() == "firebase":
        return _legacy_login_user(payload)

    email = normalize_email(payload.email)
    _validate_email(email)

    from app.services.supabase_auth_service import sign_in_with_email

    result = sign_in_with_email(email, payload.password)
    user = _supabase_profile(result["user"])
    return _supabase_token_response(result, user)


def get_user_from_token(token: str) -> dict:
    if _auth_provider() == "firebase":
        return _legacy_get_user_from_token(token)

    from app.services.supabase_auth_service import get_user_from_access_token

    auth_user = get_user_from_access_token(token)
    return _supabase_profile(auth_user)


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return get_user_from_token(token)


def get_debate_user(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_bearer_token(authorization)
    if token:
        return get_user_from_token(token)
    return _public_user(get_demo_user())


def logout_token(authorization: str | None) -> dict:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    if _auth_provider() == "firebase":
        _legacy_get_user_from_token(token)
        deactivate_auth_session(token)
        return {"status": "ok"}

    get_user_from_token(token)
    from app.services.supabase_auth_service import sign_out

    return sign_out(token)
