import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import auth_service, supabase_auth_service  # noqa: E402
from app.services.supabase_store import SupabaseStore  # noqa: E402


AUTH_USER = {
    "id": "a3f48af4-5d42-4af6-a834-744fd0d1947c",
    "email": "auth@example.com",
    "display_name": "Auth User",
    "metadata": {},
}
PROFILE = {
    **AUTH_USER,
    "age_group": "adult",
    "debate_level": "intermediate",
    "language": "vi",
}


class AuthProviderTests(unittest.TestCase):
    def test_empty_auth_provider_defaults_to_supabase(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", ""), \
             mock.patch.object(settings, "SUPABASE_URL", "https://project.supabase.co"), \
             mock.patch.object(settings, "SUPABASE_ANON_KEY", "public-anon-key"):
            response = TestClient(app).get("/api/v1/auth/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "supabase")

    def test_auth_config_exposes_active_supabase_public_config(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(settings, "SUPABASE_URL", "https://project.supabase.co"), \
             mock.patch.object(settings, "SUPABASE_ANON_KEY", "public-anon-key"):
            response = TestClient(app).get("/api/v1/auth/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "provider": "supabase",
            "supabase_url": "https://project.supabase.co",
            "supabase_anon_key": "public-anon-key",
        })

    def test_oauth_token_is_verified_and_profile_is_created(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(
                 supabase_auth_service,
                 "get_user_from_access_token",
                 return_value=AUTH_USER,
             ) as verify, \
             mock.patch.object(
                 SupabaseStore,
                 "ensure_profile",
                 return_value=PROFILE,
             ) as ensure_profile:
            response = TestClient(app).post(
                "/api/v1/auth/oauth",
                json={"access_token": "google-oauth-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_token"], "google-oauth-token")
        self.assertEqual(response.json()["user"]["id"], AUTH_USER["id"])
        verify.assert_called_once_with("google-oauth-token")
        ensure_profile.assert_called_once()

    def test_supabase_auth_requires_bearer_token(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"):
            response = TestClient(app).get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401)

    def test_supabase_auth_rejects_invalid_token(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(
                 supabase_auth_service,
                 "get_user_from_access_token",
                 side_effect=HTTPException(status_code=401, detail="Invalid token"),
             ):
            response = TestClient(app).get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid"},
            )

        self.assertEqual(response.status_code, 401)

    def test_supabase_auth_returns_current_user(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(
                 supabase_auth_service,
                 "get_user_from_access_token",
                 return_value=AUTH_USER,
             ) as verify, \
             mock.patch.object(
                 SupabaseStore,
                 "ensure_profile",
                 return_value=PROFILE,
             ):
            response = TestClient(app).get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid-jwt"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], AUTH_USER["id"])
        verify.assert_called_once_with("valid-jwt")

    def test_register_uses_supabase_auth_and_creates_profile(self):
        auth_result = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
            "user": AUTH_USER,
        }
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(
                 supabase_auth_service,
                 "sign_up_with_email",
                 return_value=auth_result,
             ) as sign_up, \
             mock.patch.object(
                 SupabaseStore,
                 "ensure_profile",
                 return_value=PROFILE,
             ) as ensure_profile:
            response = TestClient(app).post(
                "/api/v1/auth/register",
                json={
                    "email": "auth@example.com",
                    "password": "password123",
                    "display_name": "Auth User",
                    "age_group": "adult",
                    "debate_level": "intermediate",
                    "language": "vi",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_token"], "access-token")
        self.assertEqual(response.json()["token"], "access-token")
        sign_up.assert_called_once()
        ensure_profile.assert_called_once()

    def test_login_returns_supabase_access_token(self):
        auth_result = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
            "user": AUTH_USER,
        }
        with mock.patch.object(settings, "AUTH_PROVIDER", "supabase"), \
             mock.patch.object(
                 supabase_auth_service,
                 "sign_in_with_email",
                 return_value=auth_result,
             ), \
             mock.patch.object(
                 SupabaseStore,
                 "ensure_profile",
                 return_value=PROFILE,
             ):
            response = TestClient(app).post(
                "/api/v1/auth/login",
                json={"email": "auth@example.com", "password": "password123"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_token"], "access-token")

    def test_firebase_provider_keeps_legacy_token_path(self):
        with mock.patch.object(settings, "AUTH_PROVIDER", "firebase"), \
             mock.patch.object(
                 auth_service,
                 "_legacy_get_user_from_token",
                 return_value=PROFILE,
             ) as legacy:
            result = auth_service.get_user_from_token("legacy-token")

        self.assertEqual(result["id"], AUTH_USER["id"])
        legacy.assert_called_once_with("legacy-token")


if __name__ == "__main__":
    unittest.main()
