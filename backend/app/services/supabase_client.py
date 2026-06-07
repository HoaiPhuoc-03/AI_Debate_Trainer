from functools import lru_cache

from app.core.config import settings
from app.services.storage_errors import StorageConfigurationError


@lru_cache(maxsize=1)
def get_supabase_admin_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise StorageConfigurationError(
            "Supabase admin access requires SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY is missing."
        )

    try:
        from supabase import create_client
        from supabase.client import ClientOptions
    except ImportError as exc:
        raise StorageConfigurationError(
            "Supabase access requires the 'supabase' package."
        ) from exc

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )


def get_supabase_public_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise StorageConfigurationError(
            "Supabase Auth requires SUPABASE_URL and SUPABASE_ANON_KEY."
        )

    try:
        from supabase import create_client
        from supabase.client import ClientOptions
    except ImportError as exc:
        raise StorageConfigurationError(
            "Supabase Auth requires the 'supabase' package."
        ) from exc

    # Auth clients hold session state, so each auth operation gets an isolated
    # client instead of sharing a mutable process-wide session.
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )


# Backward-compatible name used by the storage layer.
get_supabase_client = get_supabase_admin_client
