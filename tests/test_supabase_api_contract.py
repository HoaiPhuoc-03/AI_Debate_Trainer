import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.api import debate as debate_api  # noqa: E402
from app.main import app  # noqa: E402


class SupabaseApiContractTests(unittest.TestCase):
    def test_empty_supabase_progress_contract_returns_200(self):
        empty = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "avg_claim_score": 0.0,
            "avg_evidence_score": 0.0,
            "avg_reasoning_score": 0.0,
            "overall_score": 0.0,
            "streak_days": 0,
            "recent_topics": [],
            "topic_category_breakdown": [],
            "weekly_avg_score": 0.0,
            "monthly_avg_score": 0.0,
            "recent_trend_delta": 0.0,
            "best_topic": None,
            "worst_topic": None,
            "skill_strength": "claim",
            "skill_weakness": "claim",
        }
        app.dependency_overrides[debate_api.get_debate_user] = (
            lambda: {"id": "demo-user"}
        )
        try:
            with mock.patch.object(
                debate_api,
                "get_progress_overview",
                return_value=empty,
            ):
                result = TestClient(app).get("/api/v1/debate/progress/overview")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["total_sessions"], 0)
        self.assertEqual(result.json()["recent_topics"], [])

    def test_debate_turn_contract_is_unchanged(self):
        session = {
            "session_id": "session-1",
            "user_id": "firebase-user",
            "topic": "Topic",
            "stance": "support",
            "difficulty": "Advanced",
            "input_mode": "text",
            "mode": "find_evidence",
            "status": "active",
            "turn_count": 0,
            "max_turns": 5,
            "topic_category": "Education",
        }
        analysis = {
            "ok": True,
            "is_valid": True,
            "status": "success",
            "rebuttal": "AI rebuttal",
            "cer": {
                "claim": 75,
                "evidence": 60,
                "reasoning": 70,
                "overall": 68,
                "total": 68,
            },
            "cer_breakdown": None,
            "feedback": {
                "strengths": ["Clear claim"],
                "weaknesses": [],
                "suggestions": [],
            },
            "content_flags": [],
            "timings": {},
        }
        saved = {
            "turn_id": "turn-1",
            "turn_number": 1,
            "session": {**session, "turn_count": 1},
        }
        app.dependency_overrides[debate_api.get_debate_user] = (
            lambda: {"id": "firebase-user"}
        )
        patches = [
            mock.patch.object(debate_api, "get_session", return_value=session),
            mock.patch.object(debate_api, "get_session_turns", return_value=[]),
            mock.patch.object(debate_api, "get_user_memory", return_value={
                "mode_state": {"find_evidence": {}}
            }),
            mock.patch.object(
                debate_api.ai_service,
                "generate_debate_analysis",
                return_value=analysis,
            ),
            mock.patch.object(debate_api, "save_debate_turn", return_value=saved),
            mock.patch.object(debate_api, "update_user_memory_after_turn"),
            mock.patch.object(debate_api, "get_session_memory", return_value={}),
            mock.patch.object(debate_api, "update_session_memory"),
        ]
        try:
            with patches[0], patches[1], patches[2], patches[3], patches[4], \
                 patches[5], patches[6], patches[7]:
                result = TestClient(app).post(
                    "/api/v1/debate/turn",
                    json={
                        "session_id": "session-1",
                        "user_argument": "A supported argument.",
                        "practice_mode": "evidence_practice",
                        "practice_prompt_id": "prompt-1",
                    },
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertEqual(data["session_id"], "session-1")
        self.assertEqual(data["ai_rebuttal"], "AI rebuttal")
        self.assertEqual(data["cer"]["total"], 68.0)
        self.assertEqual(data["feedback"]["strengths"], ["Clear claim"])
        self.assertEqual(data["turn_number"], 1)
        self.assertEqual(data["status"], "active")


if __name__ == "__main__":
    unittest.main()
