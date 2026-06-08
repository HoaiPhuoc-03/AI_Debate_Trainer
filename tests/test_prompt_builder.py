import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.prompt_builder import build_cer_rubric_prompt, build_groq_messages, build_practice_prompt_messages, normalize_practice_mode  # noqa: E402


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

        self.assertIn('Viết "ai_rebuttal"', prompt)
        self.assertIn("KHÔNG dùng tiếng Anh", prompt)
        self.assertIn("CỔNG BẰNG CHỨNG", prompt)
        self.assertIn("evidence_score", prompt)
        self.assertIn("4–6 câu phản biện", prompt)
        self.assertIn("Tuy nhiên", prompt)
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

        self.assertIn("KHÔNG dùng tiếng Anh", system_prompt)
        self.assertIn("ai_rebuttal", user_prompt)
        self.assertIn("CHỐNG DỒN ĐIỂM", system_prompt)
        self.assertIn("evidence_score", user_prompt)
        self.assertLess(len(system_prompt), 5000)
        self.assertLess(len(user_prompt), 3000)

    def test_practice_mode_prompt_includes_round_prompt_context(self):
        messages = build_groq_messages(
            topic="Có nên cho học sinh dùng AI trong học tập?",
            stance="support",
            difficulty="intermediate",
            user_argument="OECD 2023 cho thấy học sinh dùng AI có thể cá nhân hóa tốc độ học.",
            mode="find_evidence",
            practice_prompt="AI giúp học sinh tự chủ hơn trong việc học.",
            practice_round=2,
            language="vi",
        )

        user_prompt = messages[1]["content"]

        self.assertIn("=== ĐỀ BÀI LUYỆN TẬP ===", user_prompt)
        self.assertIn("Claim mẫu do Lumi đưa ra", user_prompt)
        self.assertIn("AI giúp học sinh tự chủ hơn", user_prompt)
        self.assertIn("Lượt: 2", user_prompt)

    def test_quick_rebuttal_prompt_uses_flaw_detection_rubric(self):
        messages = build_groq_messages(
            topic="Dùng AI viết bài có phải là gian lận không?",
            stance="support",
            difficulty="intermediate",
            user_argument="Câu này yếu vì nói ai cũng thấy lợi ích nhưng không chứng minh lợi ích là gì.",
            mode="quick_rebuttal",
            practice_mode="quick_rebuttal",
            practice_prompt="Dùng AI viết bài chắc chắn đúng vì ai cũng thấy lợi ích của nó.",
            practice_fallacy_hint="thiếu bằng chứng / dựa vào số đông",
            practice_target_flaws=["thiếu bằng chứng", "dựa vào số đông"],
            practice_round=1,
            language="vi",
        )

        combined = "\n".join(message["content"] for message in messages)

        self.assertIn("MODE: QUICK_REBUTTAL", combined)
        self.assertIn("flaw_detection", combined)
        self.assertIn("counter_example", combined)
        self.assertIn("Return mode_scores", combined)
        self.assertIn("Fallacy hint: thiếu bằng chứng / dựa vào số đông", combined)
        self.assertIn("Target flaws: thiếu bằng chứng, dựa vào số đông", combined)
        self.assertIn("not writing a full argument", combined)
        self.assertIn("not writing a full CER argument", combined)
        self.assertIn("claim = quality of flaw detection", combined)
        self.assertIn("evidence = quality of counterexample or targeted rebuttal", combined)
        self.assertNotIn("TRỌNG TÂM: Chấm ĐẦY ĐỦ", combined)

    def test_other_practice_modes_do_not_use_quick_rebuttal_rubric(self):
        messages = build_groq_messages(
            topic="Dùng AI viết bài có phải là gian lận không?",
            stance="support",
            difficulty="intermediate",
            user_argument="OECD 2023 cho thấy AI có thể hỗ trợ cá nhân hóa học tập.",
            mode="find_evidence",
            practice_mode="find_evidence",
            practice_prompt="AI giúp học sinh tự chủ hơn trong việc học.",
            language="vi",
        )

        combined = "\n".join(message["content"] for message in messages)

        self.assertIn("evidence_score", combined)
        self.assertNotIn("MODE: QUICK_REBUTTAL", combined)
        self.assertNotIn("flaw_detection", combined)

    def test_build_practice_prompt_messages_requests_claim_prompt_json(self):
        messages = build_practice_prompt_messages(
            mode="evidence_practice",
            topic="Có nên học trực tuyến thay thế bài tập về nhà?",
            difficulty="Trung cấp",
            round=1,
            previous_prompts=["Claim cũ về học trực tuyến"],
            previous_topics=["Học trực tuyến"],
        )

        combined = "\n".join(message["content"] for message in messages)

        self.assertIn('"mode": "find_evidence"', combined)
        self.assertIn('"prompt_type": "claim_prompt"', combined)
        self.assertIn("Previous prompts", combined)
        self.assertIn("Generate a new prompt that is different from previous prompts", combined)
        self.assertIn('"topic"', combined)
        self.assertIn('"claim"', combined)
        self.assertIn('"prompt"', combined)
        self.assertIn("Không tự đưa bằng chứng", combined)

    def test_normalize_practice_mode_accepts_claim_aliases(self):
        self.assertEqual(normalize_practice_mode("claim_practice"), "claim_writing")
        self.assertEqual(normalize_practice_mode("Luy\u1ec7n vi\u1ebft Claim"), "claim_writing")


if __name__ == "__main__":
    unittest.main()
