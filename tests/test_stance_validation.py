import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from app.services.auth_service import get_debate_user  # noqa: E402
from app.services.normalization import normalize_stance, validate_stance  # noqa: E402


def valid_session_payload(stance="support"):
    return {
        "topic": "Should students use AI tools for homework?",
        "stance": stance,
        "difficulty": "Intermediate",
        "input_mode": "text",
        "age_group": "Adult",
        "debate_level": "Intermediate",
        "language": "vi",
        "response_time": "90 sec",
    }


class StanceValidationTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_debate_user] = lambda: {
            "id": "test-user",
            "email": "test@example.com",
            "display_name": "Test User",
            "age_group": "adult",
            "debate_level": "intermediate",
            "language": "vi",
        }
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_validate_stance_allows_only_support_and_oppose(self):
        self.assertEqual(validate_stance("Ủng hộ")["stance"], "support")
        self.assertEqual(validate_stance("Phản đối")["stance"], "oppose")
        self.assertEqual(validate_stance("support")["stance"], "support")
        self.assertEqual(validate_stance("oppose")["stance"], "oppose")
        self.assertFalse(validate_stance("Trung lập")["is_valid"])
        self.assertFalse(validate_stance("neutral")["is_valid"])
        self.assertFalse(validate_stance("trung_lap")["is_valid"])

    def test_normalize_stance_falls_back_legacy_neutral_to_support(self):
        self.assertEqual(normalize_stance("neutral"), "support")
        self.assertEqual(normalize_stance("Trung lập"), "support")
        self.assertEqual(normalize_stance("trung_lap"), "support")

    def test_create_session_rejects_neutral_stance(self):
        response = self.client.post(
            "/api/v1/debate/session",
            json=valid_session_payload("neutral"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Lập trường không hợp lệ", response.json()["detail"])

    @mock.patch("app.api.debate.create_session")
    def test_create_session_accepts_support_and_oppose_stances(self, mocked_create_session):
        def fake_create_session(**kwargs):
            return {
                "session_id": "session-1",
                "topic": kwargs["topic"],
                "topic_id": kwargs.get("topic_id"),
                "topic_category": kwargs.get("topic_category"),
                "topic_tags": kwargs.get("topic_tags"),
                "custom_topic": kwargs.get("custom_topic"),
                "stance": kwargs["stance"],
                "difficulty": kwargs["difficulty"],
                "input_mode": kwargs["input_mode"],
                "age_group": kwargs.get("age_group"),
                "debate_level": kwargs.get("debate_level"),
                "coach_model": kwargs.get("coach_model"),
                "language": kwargs.get("language"),
                "mode": kwargs.get("mode"),
                "response_time": kwargs.get("response_time"),
                "max_turns": 2,
                "turn_count": 0,
                "status": "active",
            }

        mocked_create_session.side_effect = fake_create_session

        support_response = self.client.post(
            "/api/v1/debate/session",
            json=valid_session_payload("Ủng hộ"),
        )
        oppose_response = self.client.post(
            "/api/v1/debate/session",
            json=valid_session_payload("Phản đối"),
        )

        self.assertEqual(support_response.status_code, 200)
        self.assertEqual(support_response.json()["stance"], "support")
        self.assertEqual(oppose_response.status_code, 200)
        self.assertEqual(oppose_response.json()["stance"], "oppose")


if __name__ == "__main__":
    unittest.main()
