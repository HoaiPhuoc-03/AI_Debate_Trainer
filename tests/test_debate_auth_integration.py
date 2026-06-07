import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.api import debate as debate_api  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import supabase_auth_service  # noqa: E402
from app.services.supabase_store import SupabaseStore  # noqa: E402


USER_ID = "a3f48af4-5d42-4af6-a834-744fd0d1947c"
AUTH_USER = {
    "id": USER_ID,
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


def empty_progress():
    return {
        "total_sessions": 0,
        "completed_sessions": 0,
        "avg_claim_score": 0,
        "avg_evidence_score": 0,
        "avg_reasoning_score": 0,
        "overall_score": 0,
        "streak_days": 0,
        "recent_topics": [],
        "topic_category_breakdown": [],
        "weekly_avg_score": 0,
        "monthly_avg_score": 0,
        "recent_trend_delta": 0,
        "best_topic": None,
        "worst_topic": None,
        "skill_strength": "claim",
        "skill_weakness": "evidence",
    }


class DebateAuthIntegrationTests(unittest.TestCase):
    def auth_patches(self):
        return (
            mock.patch.object(settings, "AUTH_PROVIDER", "supabase"),
            mock.patch.object(
                supabase_auth_service,
                "get_user_from_access_token",
                return_value=AUTH_USER,
            ),
            mock.patch.object(
                SupabaseStore,
                "ensure_profile",
                return_value=PROFILE,
            ),
        )

    def test_progress_uses_supabase_auth_user_id(self):
        provider, verify, profile = self.auth_patches()
        with provider, verify, profile, mock.patch.object(
            debate_api,
            "get_progress_overview",
            return_value=empty_progress(),
        ) as progress:
            response = TestClient(app).get(
                "/api/v1/debate/progress/overview",
                headers={"Authorization": "Bearer valid-jwt"},
            )

        self.assertEqual(response.status_code, 200)
        progress.assert_called_once_with(user_id=USER_ID)

    def test_new_session_uses_supabase_auth_user_id(self):
        session = {
            "session_id": "session-1",
            "user_id": USER_ID,
            "topic": "Co nen dung AI de ho tro hoc sinh hoc tap khong?",
            "topic_id": None,
            "topic_category": None,
            "topic_tags": None,
            "custom_topic": None,
            "stance": "support",
            "difficulty": "Trung binh",
            "input_mode": "text",
            "age_group": "adult",
            "debate_level": "intermediate",
            "coach_model": "socratic_v3",
            "language": "vi",
            "mode": "free_debate",
            "response_time": None,
            "max_turns": 5,
            "turn_count": 0,
            "status": "active",
        }
        provider, verify, profile = self.auth_patches()
        with provider, verify, profile, mock.patch.object(
            debate_api,
            "create_session",
            return_value=session,
        ) as create_session:
            response = TestClient(app).post(
                "/api/v1/debate/session",
                headers={"Authorization": "Bearer valid-jwt"},
                json={
                    "topic": "Co nen dung AI de ho tro hoc sinh hoc tap khong?",
                    "stance": "support",
                    "difficulty": "intermediate",
                    "input_mode": "text",
                    "age_group": "adult",
                    "debate_level": "intermediate",
                    "language": "vi",
                    "mode": "free_debate",
                    "max_turns": 5,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(create_session.call_args.kwargs["user_id"], USER_ID)
        self.assertNotEqual(create_session.call_args.kwargs["user_id"], "demo-user")


if __name__ == "__main__":
    unittest.main()
