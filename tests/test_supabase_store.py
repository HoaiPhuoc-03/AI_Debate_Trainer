import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.supabase_store import SupabaseStore  # noqa: E402


def response(data):
    return SimpleNamespace(data=data)


class SupabaseStoreTests(unittest.TestCase):
    def test_ensure_user_creates_demo_profile_once(self):
        store = SupabaseStore(mock.MagicMock())
        demo = {
            "id": "demo-user",
            "email": "demo@local.test",
            "display_name": "Demo User",
        }
        store.get_user = mock.Mock(side_effect=[None, demo])
        store.create_user = mock.Mock(return_value=demo)

        first = store.ensure_user(
            "demo-user",
            email="demo@local.test",
            display_name="Demo User",
        )

        self.assertEqual(first["id"], "demo-user")
        store.create_user.assert_called_once_with(
            user_id="demo-user",
            email="demo@local.test",
            display_name="Demo User",
            age_group="adult",
            debate_level="Trung cấp",
            language="vi",
            metadata={"source": "local_demo"},
        )

    def test_create_session_maps_id_to_session_id(self):
        client = mock.MagicMock()
        table = client.table.return_value
        table.insert.return_value.execute.return_value = response(
            [{
                "id": "session-1",
                "topic": "Topic",
                "stance": "support",
                "difficulty": "Advanced",
                "practice_mode": "free_debate",
                "status": "active",
                "turn_count": 0,
                "metadata": {"input_mode": "text", "max_turns": 5},
            }]
        )
        store = SupabaseStore(client)

        result = store.create_session(
            user_id="firebase-user",
            topic="Topic",
            stance="support",
            difficulty="Advanced",
            input_mode="text",
        )

        self.assertEqual(result["session_id"], "session-1")
        self.assertEqual(result["mode"], "free_debate")

    def test_save_feedback_items_splits_categories(self):
        client = mock.MagicMock()
        client.table.return_value.insert.return_value.execute.return_value = response([])
        store = SupabaseStore(client)

        rows = store.save_feedback_items(
            turn_id="turn-1",
            session_id="session-1",
            user_id="firebase-user",
            feedback={
                "strengths": ["Strong"],
                "weaknesses": ["Weak"],
                "suggestions": ["Improve"],
            },
        )

        self.assertEqual(
            [row["feedback_type"] for row in rows],
            ["strength", "weakness", "suggestion"],
        )

    def test_get_recent_turns_returns_oldest_to_newest(self):
        client = mock.MagicMock()
        query = client.table.return_value.select.return_value.eq.return_value
        query.order.return_value.limit.return_value.execute.return_value = response(
            [
                {"id": "turn-3", "turn_number": 3},
                {"id": "turn-2", "turn_number": 2},
                {"id": "turn-1", "turn_number": 1},
            ]
        )
        store = SupabaseStore(client)
        store._hydrate_turn = mock.Mock(side_effect=lambda row: row)

        turns = store.get_recent_turns("session-1", limit=3)

        self.assertEqual([turn["turn_number"] for turn in turns], [1, 2, 3])

    def test_get_user_memory_returns_default_when_missing(self):
        client = mock.MagicMock()
        query = client.table.return_value.select.return_value.eq.return_value
        query.limit.return_value.execute.return_value = response([])
        store = SupabaseStore(client)

        memory = store.get_user_memory("firebase-user")

        self.assertEqual(memory["user_id"], "firebase-user")
        self.assertEqual(memory["global"]["total_turns"], 0)
        self.assertIn("find_evidence", memory["mode_state"])

    def test_reset_user_memory_only_upserts_memory(self):
        client = mock.MagicMock()
        table = client.table.return_value
        table.upsert.return_value.execute.return_value = response([])
        store = SupabaseStore(client)

        memory = store.reset_user_memory("firebase-user")

        self.assertEqual(memory["global"]["total_turns"], 0)
        table.delete.assert_not_called()
        table.upsert.assert_called_once()

    def test_evidence_alias_updates_find_evidence_only(self):
        client = mock.MagicMock()
        table = client.table.return_value
        query = table.select.return_value.eq.return_value
        query.limit.return_value.execute.return_value = response([])
        table.upsert.return_value.execute.return_value = response([])
        store = SupabaseStore(client)

        memory = store.update_user_memory_after_turn(
            user_id="firebase-user",
            mode="evidence_practice",
            topic="Topic",
            topic_category="Education",
            user_argument="Argument",
            ai_result={
                "cer": {"claim": 70, "evidence": 40, "reasoning": 60, "total": 55},
                "feedback": {
                    "strengths": [],
                    "weaknesses": ["Needs evidence"],
                    "suggestions": ["Add a source"],
                },
            },
        )

        self.assertEqual(memory["mode_state"]["find_evidence"]["turn_count"], 1)
        self.assertEqual(memory["mode_state"]["claim_writing"]["turn_count"], 0)


if __name__ == "__main__":
    unittest.main()
