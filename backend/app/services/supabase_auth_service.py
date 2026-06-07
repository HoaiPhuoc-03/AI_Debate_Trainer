from fastapi import HTTPException

from app.services.supabase_client import (
    get_supabase_admin_client,
    get_supabase_public_client,
)


def _auth_error(exc: Exception, *, default_status: int, default_message: str):
    code = getattr(exc, "code", None)
    message = str(getattr(exc, "message", "") or default_message)
    status = int(getattr(exc, "status", 0) or default_status)

    if code in {"email_exists", "user_already_exists"} or "already registered" in message.lower():
        status = 409
    elif code in {
        "bad_jwt",
        "invalid_jwt",
        "invalid_credentials",
        "session_not_found",
        "user_not_found",
    }:
        status = 401

    raise HTTPException(status_code=status, detail=message) from exc


def _user_dict(user) -> dict:
    metadata = dict(getattr(user, "user_metadata", None) or {})
    email = getattr(user, "email", None)
    return {
        "id": str(user.id),
        "email": email,
        "display_name": (
            metadata.get("display_name")
            or metadata.get("full_name")
            or (email.split("@", 1)[0] if email else str(user.id))
        ),
        "metadata": metadata,
    }


def _auth_response(response) -> dict:
    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if not user:
        raise HTTPException(status_code=502, detail="Supabase Auth did not return a user.")

    result = {
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
        "token_type": getattr(session, "token_type", None) or "bearer",
        "user": _user_dict(user),
    }
    if not session:
        result["message"] = (
            "Registration succeeded. Check your email to confirm the account "
            "before signing in."
        )
    return result


def sign_up_with_email(
    email: str,
    password: str,
    display_name: str | None = None,
) -> dict:
    try:
        response = get_supabase_public_client().auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name or email.split("@", 1)[0],
                    }
                },
            }
        )
    except Exception as exc:
        _auth_error(
            exc,
            default_status=400,
            default_message="Unable to register with Supabase Auth.",
        )
    return _auth_response(response)


def sign_in_with_email(email: str, password: str) -> dict:
    try:
        response = get_supabase_public_client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as exc:
        _auth_error(
            exc,
            default_status=401,
            default_message="Invalid email or password.",
        )
    return _auth_response(response)


def get_user_from_access_token(access_token: str) -> dict:
    try:
        response = get_supabase_public_client().auth.get_user(access_token)
    except Exception as exc:
        _auth_error(
            exc,
            default_status=401,
            default_message="Invalid or expired token.",
        )
    user = getattr(response, "user", None) if response else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return _user_dict(user)


def sign_out(access_token: str) -> dict:
    try:
        get_supabase_admin_client().auth.admin.sign_out(access_token, "global")
    except Exception as exc:
        _auth_error(
            exc,
            default_status=401,
            default_message="Unable to sign out.",
        )
    return {"status": "ok"}
