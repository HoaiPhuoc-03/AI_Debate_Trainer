import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services import supabase_auth_service  # noqa: E402


def auth_user(user_id="auth-user", email="user@example.com"):
    return SimpleNamespace(
        id=user_id,
        email=email,
        user_metadata={"display_name": "Auth User"},
    )


class SupabaseAuthServiceTests(unittest.TestCase):
    def test_sign_up_returns_supabase_tokens_and_user(self):
        response = SimpleNamespace(
            user=auth_user(),
            session=SimpleNamespace(
                access_token="access-token",
                refresh_token="refresh-token",
                token_type="bearer",
            ),
        )
        client = mock.Mock()
        client.auth.sign_up.return_value = response

        with mock.patch.object(
            supabase_auth_service,
            "get_supabase_public_client",
            return_value=client,
        ):
            result = supabase_auth_service.sign_up_with_email(
                "user@example.com",
                "password123",
                "Auth User",
            )

        self.assertEqual(result["access_token"], "access-token")
        self.assertEqual(result["refresh_token"], "refresh-token")
        self.assertEqual(result["user"]["id"], "auth-user")
        client.auth.sign_up.assert_called_once()

    def test_sign_up_without_session_returns_confirmation_message(self):
        client = mock.Mock()
        client.auth.sign_up.return_value = SimpleNamespace(
            user=auth_user(),
            session=None,
        )

        with mock.patch.object(
            supabase_auth_service,
            "get_supabase_public_client",
            return_value=client,
        ):
            result = supabase_auth_service.sign_up_with_email(
                "user@example.com",
                "password123",
            )

        self.assertIsNone(result["access_token"])
        self.assertIn("confirm", result["message"].lower())

    def test_get_user_validates_access_token_with_supabase(self):
        client = mock.Mock()
        client.auth.get_user.return_value = SimpleNamespace(user=auth_user())

        with mock.patch.object(
            supabase_auth_service,
            "get_supabase_public_client",
            return_value=client,
        ):
            user = supabase_auth_service.get_user_from_access_token("jwt")

        self.assertEqual(user["id"], "auth-user")
        client.auth.get_user.assert_called_once_with("jwt")

    def test_invalid_access_token_returns_401(self):
        client = mock.Mock()
        client.auth.get_user.side_effect = RuntimeError("invalid JWT")

        with mock.patch.object(
            supabase_auth_service,
            "get_supabase_public_client",
            return_value=client,
        ):
            with self.assertRaises(HTTPException) as raised:
                supabase_auth_service.get_user_from_access_token("invalid")

        self.assertEqual(raised.exception.status_code, 401)

    def test_sign_out_uses_admin_client_without_exposing_key(self):
        client = mock.Mock()

        with mock.patch.object(
            supabase_auth_service,
            "get_supabase_admin_client",
            return_value=client,
        ):
            result = supabase_auth_service.sign_out("jwt")

        self.assertEqual(result, {"status": "ok"})
        client.auth.admin.sign_out.assert_called_once_with("jwt", "global")


if __name__ == "__main__":
    unittest.main()
