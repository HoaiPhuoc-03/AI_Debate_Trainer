import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services import session_store  # noqa: E402
from app.api import debate as debate_api  # noqa: E402
from app.main import app  # noqa: E402
from app.services.prompt_builder import build_groq_messages  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class FakeUserDocument:
    def __init__(self, store: dict, user_id: str):
        self.store = store
        self.user_id = user_id

    def get(self):
        return self

    @property
    def exists(self):
        return self.user_id in self.store

    def to_dict(self):
        return self.store.get(self.user_id)

    def set(self, data, merge=False):
        if merge:
            existing = self.store.get(self.user_id, {}).copy()
            existing.update(data)
            self.store[self.user_id] = existing
        else:
            self.store[self.user_id] = data


class FakeCollection:
    def __init__(self, store: dict):
        self.store = store

    def document(self, user_id: str):
        return FakeUserDocument(self.store, user_id)


class FakeDb:
    def __init__(self, users: dict):
        self.users = users

    def collection(self, name: str):
        if name != "users":
            raise AssertionError(f"Unexpected collection: {name}")
        return FakeCollection(self.users)


class UserMemoryTests(unittest.TestCase):
    def setUp(self):
        self.provider_patch = mock.patch.object(
            session_store.settings,
            "STORAGE_PROVIDER",
            "firebase",
        )
        self.provider_patch.start()
        self.users = {
            "user-1": {
                "id": "user-1",
                "email": "user@example.com",
            }
        }

    def tearDown(self):
        self.provider_patch.stop()

    def fake_db(self):
        return FakeDb(self.users)

    def test_new_user_memory_has_default_schema(self):
        memory = session_store._default_user_memory("user-1")

        self.assertEqual(memory["global"]["total_turns"], 0)
        self.assertIn("free_debate", memory["mode_state"])
        self.assertIn("claim_writing", memory["mode_state"])
        self.assertIn("find_evidence", memory["mode_state"])
        self.assertIn("quick_rebuttal", memory["mode_state"])
        self.assertIn("full_argument", memory["mode_state"])

    def test_merge_user_memory_keeps_existing_and_adds_missing_fields(self):
        memory = session_store._merge_user_memory(
            {
                "global": {
                    "total_turns": 2,
                    "recurring_weaknesses": ["Evidence is vague"],
                    "avg_scores": {"claim": 70},
                },
                "mode_state": {
                    "claim_practice": {
                        "common_weaknesses": ["Claim is too broad"],
                    }
                },
            },
            "user-1",
        )

        self.assertEqual(memory["global"]["total_turns"], 2)
        self.assertEqual(memory["global"]["avg_scores"]["claim"], 70.0)
        self.assertIn("Evidence is vague", memory["global"]["recurring_weaknesses"])
        self.assertIn("Claim is too broad", memory["mode_state"]["claim_writing"]["common_weaknesses"])
        self.assertIn("find_evidence", memory["mode_state"])

    def test_normalize_memory_mode_maps_aliases(self):
        self.assertEqual(session_store.normalize_memory_mode("claim_practice"), "claim_writing")
        self.assertEqual(session_store.normalize_memory_mode("evidence_practice"), "find_evidence")
        self.assertEqual(session_store.normalize_memory_mode("argument_builder"), "full_argument")
        self.assertEqual(session_store.normalize_memory_mode("unknown"), "free_debate")

    @mock.patch.object(session_store, "_db")
    def test_update_user_memory_after_turn_updates_only_current_mode(self, mocked_db):
        mocked_db.side_effect = self.fake_db
        ai_result = {
            "cer": {
                "claim": 80,
                "evidence": 40,
                "reasoning": 60,
                "overall": 60,
                "total": 60,
            },
            "feedback": {
                "strengths": ["Clear claim"],
                "weaknesses": ["Evidence needs a named source"],
                "suggestions": ["Add one concrete study"],
            },
        }

        memory = session_store.update_user_memory_after_turn(
            user_id="user-1",
            mode="find_evidence",
            topic="Should AI tutors replace homework?",
            topic_category="Education",
            user_argument="Full transcript should not be stored here.",
            ai_result=ai_result,
        )

        self.assertEqual(memory["global"]["total_turns"], 1)
        self.assertEqual(memory["global"]["avg_scores"]["evidence"], 40.0)
        self.assertIn("Education", memory["global"]["topic_preferences"])
        self.assertIn(
            "Evidence needs a named source",
            memory["mode_state"]["find_evidence"]["common_weaknesses"],
        )
        self.assertIn("thiếu bằng chứng cụ thể", memory["mode_state"]["find_evidence"]["evidence_patterns"])
        self.assertEqual(memory["mode_state"]["claim_writing"]["common_weaknesses"], [])
        self.assertNotIn("Full transcript should not be stored here.", str(memory))

    @mock.patch.object(session_store, "_db")
    def test_reset_user_memory_preserves_user_document_fields(self, mocked_db):
        self.users["user-1"][session_store.USER_MEMORY_FIELD] = {
            "global": {"total_turns": 5}
        }
        mocked_db.side_effect = self.fake_db

        memory = session_store.reset_user_memory("user-1")

        self.assertEqual(memory["global"]["total_turns"], 0)
        self.assertEqual(self.users["user-1"]["email"], "user@example.com")
        self.assertEqual(self.users["user-1"][session_store.USER_MEMORY_FIELD]["global"]["total_turns"], 0)

    def test_prompt_includes_user_memory_and_scoring_guardrails(self):
        messages = build_groq_messages(
            topic="Social media harms society",
            stance="support",
            difficulty="intermediate",
            user_argument="Social media makes people less focused.",
            age_group="adult",
            debate_level="intermediate",
            input_mode="text",
            language="vi",
            mode="claim_writing",
            memory_context={
                "session_summary": "1 recent turn tracked",
                "active_mode": "claim_writing",
                "recent_turns": [],
                "mode_state": {},
                "used_practice_prompts": [],
                "current_practice_prompt": "Current prompt",
                "user_memory": {
                    "global": {
                        "total_turns": 3,
                        "topic_preferences": ["Education"],
                        "recurring_weaknesses": ["Claim too broad"],
                        "recurring_suggestions": ["Narrow the scope"],
                        "avg_scores": {
                            "claim": 60,
                            "evidence": 55,
                            "reasoning": 70,
                            "overall": 62,
                        },
                    },
                    "mode_state": {
                        "claim_writing": {
                            "common_weaknesses": ["Claim too broad"],
                            "common_suggestions": ["Narrow the scope"],
                            "previous_claim_patterns": ["too broad"],
                        }
                    },
                },
            },
        )

        user_prompt = messages[1]["content"]
        self.assertIn("=== USER MEMORY ===", user_prompt)
        self.assertIn("Claim too broad", user_prompt)
        self.assertIn("Do not change CER scores because of past performance.", user_prompt)

    def test_user_memory_endpoint_reads_current_user_only(self):
        app.dependency_overrides[debate_api.get_current_user] = lambda: {"id": "user-a"}
        try:
            with mock.patch.object(debate_api, "get_user_memory", return_value={"user_id": "user-a"}) as mocked:
                response = TestClient(app).get("/api/v1/debate/user-memory")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["memory"]["user_id"], "user-a")
        mocked.assert_called_once_with("user-a")

    def test_user_memory_delete_resets_current_user_only(self):
        app.dependency_overrides[debate_api.get_current_user] = lambda: {"id": "user-a"}
        try:
            with mock.patch.object(debate_api, "reset_user_memory", return_value={"user_id": "user-a"}) as mocked:
                response = TestClient(app).delete("/api/v1/debate/user-memory")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["memory"]["user_id"], "user-a")
        mocked.assert_called_once_with("user-a")


if __name__ == "__main__":
    unittest.main()
