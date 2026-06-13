import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.services.store_factory import FirebaseStore, get_store  # noqa: E402
from app.services import session_store  # noqa: E402
from app.services.storage_errors import StorageConfigurationError  # noqa: E402
from app.services.supabase_client import get_supabase_client  # noqa: E402
from app.services.supabase_store import SupabaseStore  # noqa: E402


class StoreProviderTests(unittest.TestCase):
    def test_firebase_provider_selects_firebase_without_supabase_env(self):
        with mock.patch.object(settings, "STORAGE_PROVIDER", "firebase"), \
             mock.patch.object(settings, "SUPABASE_URL", ""), \
             mock.patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", ""):
            store = get_store()

        self.assertIsInstance(store, FirebaseStore)

    def test_supabase_provider_selects_supabase_store(self):
        with mock.patch.object(settings, "STORAGE_PROVIDER", "supabase"):
            store = get_store()

        self.assertIsInstance(store, SupabaseStore)

    def test_empty_storage_provider_defaults_to_supabase(self):
        with mock.patch.object(settings, "STORAGE_PROVIDER", ""):
            store = get_store()

        self.assertIsInstance(store, SupabaseStore)

    def test_unknown_provider_has_clear_error(self):
        with mock.patch.object(settings, "STORAGE_PROVIDER", "unknown"):
            with self.assertRaises(StorageConfigurationError):
                get_store()

    def test_supabase_missing_env_has_clear_error(self):
        get_supabase_client.cache_clear()
        with mock.patch.object(settings, "SUPABASE_URL", ""), \
             mock.patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", ""):
            with self.assertRaisesRegex(
                StorageConfigurationError,
                "SUPABASE_URL.*SUPABASE_SERVICE_ROLE_KEY",
            ):
                get_supabase_client()

    def test_supabase_demo_user_does_not_call_firebase(self):
        demo = {
            "id": "demo-user",
            "email": "demo@local.test",
            "display_name": "Demo User",
        }
        with mock.patch.object(settings, "STORAGE_PROVIDER", "supabase"), \
             mock.patch.object(session_store, "_db", side_effect=AssertionError("Firebase called")), \
             mock.patch.object(SupabaseStore, "get_demo_user", return_value=demo) as called:
            result = session_store.get_demo_user()

        self.assertEqual(result, demo)
        called.assert_called_once_with()

    def test_supabase_init_does_not_call_firebase(self):
        with mock.patch.object(settings, "STORAGE_PROVIDER", "supabase"), \
             mock.patch.object(session_store, "_db", side_effect=AssertionError("Firebase called")), \
             mock.patch.object(SupabaseStore, "init_db") as called:
            session_store.init_db()

        called.assert_called_once_with()

    def test_firebase_demo_user_uses_rollback_path(self):
        demo = {"id": "demo-user"}
        with mock.patch.object(settings, "STORAGE_PROVIDER", "firebase"), \
             mock.patch.object(
                 session_store,
                 "_firebase_get_demo_user",
                 return_value=demo,
             ) as called:
            result = session_store.get_demo_user()

        self.assertEqual(result, demo)
        called.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
