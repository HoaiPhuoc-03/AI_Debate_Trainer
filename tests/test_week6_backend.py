import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.api import debate as debate_api  # noqa: E402
from app.main import app  # noqa: E402
from app.services.session_store import init_db  # noqa: E402


def fake_analysis():
    return {
        "ok": True,
        "rebuttal": "AI rebuttal",
        "cer": {
            "claim": 70.0,
            "evidence": 50.0,
            "reasoning": 60.0,
            "overall": 60.0,
            "total": 60.0,
        },
        "cer_breakdown": {
            "claim": {"clarity": 30.0, "relevance": 25.0, "specificity": 15.0},
            "evidence": {"presence": 20.0, "specificity": 15.0, "relevance": 15.0},
            "reasoning": {"logical_connection": 25.0, "causal_explanation": 25.0, "fallacy_control": 10.0},
        },
        "feedback": {
            "strengths": ["Clear claim"],
            "weaknesses": ["Needs stronger evidence"],
            "suggestions": ["Add one concrete example"],
        },
        "content_flags": [],
        "is_valid": True,
        "status": "success",
        "error": "",
    }


class Week6BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        settings.DATABASE_PATH = self.db_path
        settings.DEFAULT_MAX_TURNS = 3
        init_db()
        self.client = TestClient(app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def register_user(
        self,
        email="minh@example.com",
        password="password123",
        display_name="Minh Nguyen",
    ):
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": display_name,
                "age_group": "Teen",
                "debate_level": "Advanced",
                "language": "English",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def new_session_payload(self, max_turns=2, topic="Should AI tutors replace homework?"):
        return {
            "topic": topic,
            "stance": "Support",
            "difficulty": "Advanced",
            "input_mode": "Voice",
            "age_group": "Teen",
            "debate_level": "Advanced",
            "language": "English",
            "response_time": "90 sec",
            "max_turns": max_turns,
            "display_name": "Minh Nguyen",
        }

    def create_session(self, payload=None, token=None):
        headers = self.auth_headers(token) if token else None
        response = self.client.post(
            "/api/v1/debate/session",
            json=payload or self.new_session_payload(),
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def count_rows(self, table_name):
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        finally:
            connection.close()

    def submit_turn(self, session_id, argument="Phones can support quick research.", token=None):
        headers = self.auth_headers(token) if token else None
        return self.client.post(
            "/api/v1/debate/turn",
            json={
                "session_id": session_id,
                "user_argument": argument,
            },
            headers=headers,
        )

    def test_health_check(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @mock.patch("app.api.debate.build_practice_prompt")
    def test_practice_prompt_endpoint_returns_generated_round_prompt(self, mocked_prompt):
        app.dependency_overrides[debate_api.get_debate_user] = lambda: {"id": "demo-user"}
        mocked_prompt.return_value = {
            "status": "success",
            "mode": "find_evidence",
            "prompt_type": "claim_prompt",
            "prompt": "Học trực tuyến giúp học sinh tự chủ hơn trong việc quản lý thời gian.",
            "instruction": "Hãy đưa ra bằng chứng cụ thể để hỗ trợ hoặc phản bác claim này.",
            "warning": None,
        }
        try:
            response = self.client.post(
                "/api/v1/debate/practice-prompt",
                json={
                    "mode": "evidence_practice",
                    "topic": "Có nên cho học sinh dùng AI trong học tập?",
                    "difficulty": "Trung cấp",
                    "round": 2,
                    "previous_prompts": ["Claim cũ"],
                    "previous_topics": ["Chủ đề cũ"],
                    "avoid_repeating": True,
                },
            )
        finally:
            app.dependency_overrides.pop(debate_api.get_debate_user, None)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["prompt_type"], "claim_prompt")
        self.assertIn("Học trực tuyến", data["prompt"])
        mocked_prompt.assert_called_once_with(
            mode="evidence_practice",
            topic="Có nên cho học sinh dùng AI trong học tập?",
            difficulty="Trung cấp",
            category=None,
            round_number=2,
            session_id=None,
            used_prompts=["Claim cũ"],
            previous_topics=["Chủ đề cũ"],
            avoid_repeating=True,
        )

    @mock.patch("app.api.debate.ai_service.generate_practice_prompt")
    def test_quick_rebuttal_endpoint_is_deterministic_without_ai_provider(self, mocked_ai_prompt):
        app.dependency_overrides[debate_api.get_debate_user] = lambda: {"id": "demo-user"}
        try:
            response = self.client.post(
                "/api/v1/debate/practice-prompt",
                json={
                    "mode": "quick_rebuttal",
                    "topic": "Điểm số có còn là thước đo tốt cho năng lực học sinh?",
                    "difficulty": "Cơ bản",
                    "round": 1,
                    "previous_prompts": [],
                    "previous_topics": [],
                    "avoid_repeating": True,
                },
            )
        finally:
            app.dependency_overrides.pop(debate_api.get_debate_user, None)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "quick_rebuttal")
        self.assertEqual(data["prompt_type"], "weak_argument")
        self.assertEqual(data["prompt"], data["weak_argument"])
        self.assertIn("Hãy chỉ ra", data["instruction"])
        self.assertNotIn("? chắc chắn", data["weak_argument"])
        self.assertNotIn("Hãy chỉ ra", data["weak_argument"])
        mocked_ai_prompt.assert_not_called()

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_full_argument_turn_uses_practice_topic_and_keeps_session_active(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        payload = self.new_session_payload(
            max_turns=1,
            topic="Chủ đề ban đầu của phiên tranh biện",
        )
        payload["mode"] = "full_argument"
        session = self.create_session(payload)

        response = self.client.post(
            "/api/v1/debate/turn",
            json={
                "session_id": session["session_id"],
                "user_argument": "Claim, evidence and reasoning for the new topic.",
                "practice_mode": "cer",
                "practice_topic": "Có nên giới hạn thời gian sử dụng TikTok của thanh thiếu niên?",
                "practice_prompt": "Hãy xây dựng một lập luận C-E-R đầy đủ.",
                "practice_round": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "active")
        self.assertEqual(
            mocked_ai.call_args.kwargs["topic"],
            "Có nên giới hạn thời gian sử dụng TikTok của thanh thiếu niên?",
        )
        self.assertEqual(mocked_ai.call_args.kwargs["practice_mode"], "cer")

    def test_register_success(self):
        data = self.register_user()

        self.assertTrue(data["token"])
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "minh@example.com")
        self.assertEqual(data["user"]["display_name"], "Minh Nguyen")
        self.assertEqual(data["user"]["age_group"], "teen")
        self.assertEqual(data["user"]["debate_level"], "advanced")
        self.assertEqual(data["user"]["language"], "vi")

    def test_register_duplicate_email_returns_error(self):
        self.register_user(email="dupe@example.com")

        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "DUPE@example.com",
                "password": "password123",
                "display_name": "Duplicate User",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_login_success(self):
        self.register_user(email="login@example.com", password="password123")

        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["token"])
        self.assertEqual(data["user"]["email"], "login@example.com")

    def test_login_wrong_password_returns_401(self):
        self.register_user(email="wrong@example.com", password="password123")

        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_me_with_valid_token_returns_current_user(self):
        auth = self.register_user(email="me@example.com")

        response = self.client.get(
            "/api/v1/auth/me",
            headers=self.auth_headers(auth["token"]),
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["email"], "me@example.com")
        self.assertEqual(data["id"], auth["user"]["id"])

    def test_logout_invalidates_token(self):
        auth = self.register_user(email="logout@example.com")

        logout_response = self.client.post(
            "/api/v1/auth/logout",
            headers=self.auth_headers(auth["token"]),
        )
        me_response = self.client.get(
            "/api/v1/auth/me",
            headers=self.auth_headers(auth["token"]),
        )

        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.json(), {"status": "ok"})
        self.assertEqual(me_response.status_code, 401)

    def test_create_session_with_new_payload_success(self):
        data = self.create_session()

        self.assertTrue(data["session_id"])
        self.assertEqual(data["topic"], "Should AI tutors replace homework?")
        self.assertIsNone(data["topic_category"])
        self.assertIsNone(data["custom_topic"])
        self.assertEqual(data["stance"], "support")
        self.assertEqual(data["difficulty"], "Nâng cao")
        self.assertEqual(data["input_mode"], "voice")
        self.assertEqual(data["age_group"], "teen")
        self.assertEqual(data["debate_level"], "advanced")
        self.assertEqual(data["coach_model"], "socratic_v3")
        self.assertEqual(data["language"], "vi")
        self.assertEqual(data["response_time"], "90 sec")
        self.assertEqual(data["max_turns"], 2)
        self.assertEqual(data["turn_count"], 0)
        self.assertEqual(data["status"], "active")
        self.assertEqual(self.count_rows("debate_sessions"), 1)

    def test_create_session_accepts_legacy_payload_defaults(self):
        data = self.create_session(
            {
                "topic": "Should phones be allowed in class?",
                "stance": "Support",
                "difficulty": "Medium",
                "input_mode": "text",
            }
        )

        self.assertEqual(data["topic"], "Should phones be allowed in class?")
        self.assertIsNone(data["topic_category"])
        self.assertEqual(data["stance"], "support")
        self.assertEqual(data["difficulty"], "Trung bình")
        self.assertEqual(data["input_mode"], "text")
        self.assertEqual(data["age_group"], "adult")
        self.assertEqual(data["debate_level"], "intermediate")
        self.assertEqual(data["coach_model"], "socratic_v3")
        self.assertEqual(data["language"], "vi")
        self.assertEqual(data["max_turns"], 5)

    def test_create_session_rejects_invalid_topic(self):
        response = self.client.post(
            "/api/v1/debate/session",
            json={
                "topic": "ok k",
                "stance": "Support",
                "difficulty": "Medium",
                "input_mode": "text",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Topic", response.json()["detail"])
        self.assertEqual(self.count_rows("debate_sessions"), 0)

    def test_create_session_ignores_legacy_custom_topic_override(self):
        data = self.create_session(
            {
                "topic": "Should phones be allowed in class?",
                "topic_category": "Technology & AI",
                "custom_topic": "Should AI tutors replace homework?",
                "stance": "Support",
                "difficulty": "Medium",
                "input_mode": "text",
            }
        )

        self.assertEqual(data["topic"], "Should phones be allowed in class?")
        self.assertIsNone(data["topic_category"])
        self.assertIsNone(data["custom_topic"])

    def test_create_session_maps_missing_difficulty_from_profile_modes(self):
        adult = self.create_session(
            {
                "topic": "Sinh viên có nên đi làm thêm năm nhất?",
                "stance": "support",
                "age_group": "adult",
                "debate_level": "intermediate",
                "input_mode": "text",
                "coach_model": "socratic_v3",
                "language": "vi",
                "max_turns": 5,
            }
        )
        teen = self.create_session(
            {
                "topic": "Học sinh có nên dùng AI để học tập?",
                "stance": "support",
                "age_group": "teen",
                "debate_level": "basic",
                "input_mode": "voice",
            }
        )

        self.assertEqual(adult["age_group"], "adult")
        self.assertEqual(adult["debate_level"], "intermediate")
        self.assertEqual(adult["input_mode"], "text")
        self.assertEqual(adult["difficulty"], "Trung bình")
        self.assertEqual(teen["age_group"], "teen")
        self.assertEqual(teen["debate_level"], "basic")
        self.assertEqual(teen["input_mode"], "voice")
        self.assertEqual(teen["difficulty"], "Cơ bản")

    def test_create_session_normalizes_vietnamese_profile_values(self):
        data = self.create_session(
            {
                "topic": "Sinh viên có nên đi làm thêm năm nhất?",
                "stance": "Ủng hộ",
                "age_group": "Người lớn",
                "debate_level": "Trung cấp",
                "input_mode": "Văn bản",
            }
        )

        self.assertEqual(data["stance"], "support")
        self.assertEqual(data["age_group"], "adult")
        self.assertEqual(data["debate_level"], "intermediate")
        self.assertEqual(data["input_mode"], "text")
        self.assertEqual(data["difficulty"], "Trung bình")

    def test_get_session_reads_new_session_information(self):
        session = self.create_session()

        response = self.client.get(f"/api/v1/debate/session/{session['session_id']}")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["session_id"], session["session_id"])
        self.assertEqual(data["topic"], "Should AI tutors replace homework?")
        self.assertEqual(data["stance"], "support")
        self.assertEqual(data["difficulty"], "Nâng cao")
        self.assertEqual(data["max_turns"], 2)
        self.assertEqual(data["turn_count"], 0)
        self.assertEqual(data["status"], "active")

    def test_authenticated_user_creates_owned_session(self):
        auth = self.register_user(email="owner@example.com")

        session = self.create_session(token=auth["token"])
        progress = self.client.get(
            "/api/v1/debate/progress/overview",
            headers=self.auth_headers(auth["token"]),
        ).json()

        self.assertTrue(session["session_id"])
        self.assertEqual(progress["total_sessions"], 1)
        self.assertEqual(progress["recent_topics"], ["Should AI tutors replace homework?"])

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_user_b_cannot_use_user_a_session(self, mocked_ai):
        user_a = self.register_user(email="a@example.com")
        user_b = self.register_user(email="b@example.com")
        session = self.create_session(token=user_a["token"])

        response = self.submit_turn(
            session["session_id"],
            "I should not be allowed into another user's session.",
            token=user_b["token"],
        )

        self.assertEqual(response.status_code, 404)
        mocked_ai.assert_not_called()

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_debate_turn_happy_path_returns_structured_response_and_persists(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        session = self.create_session()

        response = self.submit_turn(session["session_id"])
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ai_rebuttal"], "AI rebuttal")
        self.assertEqual(data["turn_number"], 1)
        self.assertEqual(data["max_turns"], 2)
        self.assertEqual(data["cer"]["total"], 60.0)
        self.assertEqual(data["cer"]["overall"], 60.0)
        self.assertEqual(data["cer_breakdown"]["claim"]["clarity"], 30.0)
        self.assertEqual(data["feedback"]["strengths"], ["Clear claim"])
        self.assertEqual(data["status"], "active")
        self.assertEqual(self.count_rows("debate_turns"), 1)
        self.assertEqual(self.count_rows("cer_scores"), 1)
        self.assertEqual(self.count_rows("feedback_items"), 3)
        mocked_ai.assert_called_once()
        self.assertEqual(mocked_ai.call_args.kwargs["age_group"], "teen")
        self.assertEqual(mocked_ai.call_args.kwargs["debate_level"], "advanced")
        self.assertEqual(mocked_ai.call_args.kwargs["input_mode"], "voice")
        self.assertEqual(mocked_ai.call_args.kwargs["coach_model"], "socratic_v3")
        self.assertEqual(mocked_ai.call_args.kwargs["language"], "vi")

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_authenticated_debate_turn_happy_path_still_works(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        auth = self.register_user(email="turn@example.com")
        session = self.create_session(token=auth["token"])

        response = self.submit_turn(session["session_id"], "A valid argument.", token=auth["token"])
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["ai_rebuttal"], "AI rebuttal")
        self.assertEqual(data["turn_number"], 1)
        self.assertEqual(data["status"], "active")

    def test_debate_turn_unknown_session_returns_404(self):
        response = self.submit_turn("missing-session", "A valid argument.")

        self.assertEqual(response.status_code, 404)

    def test_debate_turn_empty_argument_returns_400(self):
        session = self.create_session()

        response = self.submit_turn(session["session_id"], "   ")

        self.assertEqual(response.status_code, 400)

    def test_debate_turn_invalid_argument_returns_zero_cer_without_ai_call(self):
        session = self.create_session()

        response = self.submit_turn(session["session_id"], "ok tùy")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "invalid")
        self.assertFalse(data["is_valid"])
        self.assertEqual(data["cer"]["claim"], 0.0)
        self.assertEqual(data["cer"]["evidence"], 0.0)
        self.assertEqual(data["cer"]["reasoning"], 0.0)
        self.assertEqual(data["cer"]["overall"], 0.0)

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_session_completed_after_max_turns(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        session = self.create_session(self.new_session_payload(max_turns=2))

        first_response = self.submit_turn(session["session_id"], "Argument 1")
        second_response = self.submit_turn(session["session_id"], "Argument 2")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.json()["status"], "active")
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["turn_number"], 2)
        self.assertEqual(second_response.json()["status"], "completed")

        session_response = self.client.get(f"/api/v1/debate/session/{session['session_id']}")
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.json()["status"], "completed")
        self.assertEqual(session_response.json()["turn_count"], 2)

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_session_summary_returns_aggregated_data(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        session = self.create_session()
        turn_response = self.submit_turn(session["session_id"], "Argument 1")
        self.assertEqual(turn_response.status_code, 200)

        response = self.client.get(f"/api/v1/debate/session/{session['session_id']}/summary")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["session_id"], session["session_id"])
        self.assertEqual(data["topic"], "Should AI tutors replace homework?")
        self.assertEqual(data["turn_count"], 1)
        self.assertEqual(data["max_turns"], 2)
        self.assertEqual(data["avg_claim_score"], 70.0)
        self.assertEqual(data["avg_evidence_score"], 50.0)
        self.assertEqual(data["avg_reasoning_score"], 60.0)
        self.assertEqual(data["overall_score"], 60.0)
        self.assertEqual(data["strength_summary"], ["Clear claim"])
        self.assertEqual(data["weakness_summary"], ["Needs stronger evidence"])
        self.assertEqual(data["next_steps"], ["Add one concrete example"])

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_progress_overview_returns_valid_structure(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        session = self.create_session(self.new_session_payload(max_turns=1))
        turn_response = self.submit_turn(session["session_id"], "Argument 1")
        self.assertEqual(turn_response.status_code, 200)

        response = self.client.get("/api/v1/debate/progress/overview")
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_sessions"], 1)
        self.assertEqual(data["completed_sessions"], 1)
        self.assertEqual(data["avg_claim_score"], 70.0)
        self.assertEqual(data["avg_evidence_score"], 50.0)
        self.assertEqual(data["avg_reasoning_score"], 60.0)
        self.assertEqual(data["overall_score"], 60.0)
        self.assertIsInstance(data["streak_days"], int)
        self.assertEqual(data["recent_topics"], ["Should AI tutors replace homework?"])
        self.assertEqual(data["skill_strength"], "claim")
        self.assertEqual(data["skill_weakness"], "evidence")

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_progress_overview_is_scoped_to_current_user(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        user_a = self.register_user(email="progress-a@example.com")
        user_b = self.register_user(email="progress-b@example.com")
        session_a = self.create_session(
            self.new_session_payload(max_turns=1, topic="Should students debate Topic A?"),
            token=user_a["token"],
        )
        session_b = self.create_session(
            self.new_session_payload(max_turns=1, topic="Should students debate Topic B?"),
            token=user_b["token"],
        )
        self.assertEqual(self.submit_turn(session_a["session_id"], "Argument A", token=user_a["token"]).status_code, 200)
        self.assertEqual(self.submit_turn(session_b["session_id"], "Argument B", token=user_b["token"]).status_code, 200)

        response = self.client.get(
            "/api/v1/debate/progress/overview",
            headers=self.auth_headers(user_a["token"]),
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_sessions"], 1)
        self.assertEqual(data["completed_sessions"], 1)
        self.assertEqual(data["recent_topics"], ["Should students debate Topic A?"])

    @mock.patch("app.api.debate.ai_service.generate_debate_analysis")
    def test_new_user_progress_is_empty_even_when_other_users_have_data(self, mocked_ai):
        mocked_ai.return_value = fake_analysis()
        existing_user = self.register_user(email="existing@example.com")
        new_user = self.register_user(email="new@example.com")
        session = self.create_session(
            self.new_session_payload(max_turns=1, topic="Should schools keep an existing topic?"),
            token=existing_user["token"],
        )
        self.assertEqual(self.submit_turn(session["session_id"], "Argument", token=existing_user["token"]).status_code, 200)

        response = self.client.get(
            "/api/v1/debate/progress/overview",
            headers=self.auth_headers(new_user["token"]),
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["total_sessions"], 0)
        self.assertEqual(data["completed_sessions"], 0)
        self.assertEqual(data["overall_score"], 0.0)
        self.assertEqual(data["recent_topics"], [])


if __name__ == "__main__":
    unittest.main()
