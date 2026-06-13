from app.core.config import settings
from app.services.storage_errors import StorageConfigurationError


class FirebaseStore:
    provider = "firebase"

    def __getattr__(self, name):
        from app.services import session_store

        implementation = getattr(session_store, f"_firebase_{name}", None)
        if implementation is None:
            raise AttributeError(name)
        return implementation


def get_store():
    provider = str(settings.STORAGE_PROVIDER or "supabase").strip().lower()
    if provider == "firebase":
        return FirebaseStore()
    if provider == "supabase":
        from app.services.supabase_store import SupabaseStore

        return SupabaseStore()
    raise StorageConfigurationError(
        f"Unsupported STORAGE_PROVIDER '{provider}'. Use 'firebase' or 'supabase'."
    )
