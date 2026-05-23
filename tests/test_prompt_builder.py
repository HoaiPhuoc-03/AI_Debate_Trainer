import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.prompt_builder import build_cer_rubric_prompt, build_groq_messages  # noqa: E402


class PromptBuilderTests(unittest.TestCase):
    def test_cer_prompt_requires_vietnamese_only_rebuttal(self):
        prompt = build_cer_rubric_prompt(
            topic="Sinh viên có nên đi làm thêm năm nhất?",
            stance="support",
            difficulty="intermediate",
            user_argument="Tôi nghĩ sinh viên nên đi làm thêm để tự chủ tài chính.",
            age_group="adult",
            debate_level="intermediate",
            input_mode="text",
            language="vi",
        )

        self.assertIn('Write "ai_rebuttal" only in tiếng Việt.', prompt)
        self.assertIn("Do not mix English into the rebuttal.", prompt)
        self.assertIn("If there is no named source", prompt)
        self.assertIn("evidence_score = 0 and all evidence breakdown values = 0", prompt)
        self.assertIn("Write a 4–6 sentence rebuttal", prompt)
        self.assertIn("Open with the counter-position.", prompt)
        self.assertLess(len(prompt), 7000)

    def test_groq_messages_force_vietnamese_response_contract(self):
        messages = build_groq_messages(
            topic="Mạng xã hội có hại cho xã hội",
            stance="support",
            difficulty="intermediate",
            user_argument="Mạng xã hội làm con người mất tập trung.",
            age_group="adult",
            debate_level="intermediate",
            input_mode="text",
            language="vi",
        )

        system_prompt = messages[0]["content"]
        user_prompt = messages[1]["content"]

        self.assertIn("Respond only in tiếng Việt.", system_prompt)
        self.assertIn("Write the rebuttal only in tiếng Việt.", user_prompt)
        self.assertIn("Avoid score clustering; use the full range.", user_prompt)
        self.assertIn("If there is no named evidence, Evidence = 0.", user_prompt)
        self.assertLess(len(system_prompt), 5000)
        self.assertLess(len(user_prompt), 3000)


if __name__ == "__main__":
    unittest.main()
