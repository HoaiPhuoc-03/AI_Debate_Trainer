import sys
import re
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.practice_prompt_service import (  # noqa: E402
    FALLACY_TEMPLATES,
    QUICK_REBUTTAL_INSTRUCTION,
    _build_quick_rebuttal_prompt_from_topic,
    _build_topic_prompt,
    _clean_sentence,
    _sanitize_weak_argument,
    _topic_to_claim_subject,
    build_practice_prompt,
    canonical_mode,
    get_quick_rebuttal_prompt_from_bank,
    topic_to_subject_statement,
)
from app.data.quick_rebuttal_prompts import QUICK_REBUTTAL_PROMPTS  # noqa: E402
from app.services.prompt_builder import (  # noqa: E402
    build_cer_messages,
    normalize_practice_mode,
    practice_prompt_type_for_mode,
)


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


class PracticePromptServiceTests(unittest.TestCase):
    def test_aliases_map_to_existing_repo_modes(self):
        self.assertEqual(canonical_mode("claim_practice"), "claim_writing")
        self.assertEqual(canonical_mode("evidence_practice"), "find_evidence")
        self.assertEqual(canonical_mode("argument_builder"), "full_argument")
        self.assertEqual(canonical_mode("cer"), "full_argument")
        self.assertEqual(normalize_practice_mode("cer"), "full_argument")
        self.assertEqual(practice_prompt_type_for_mode("cer"), "argument_builder")

    def test_cer_alias_builds_full_argument_scoring_context(self):
        messages = build_cer_messages(
            topic="Chủ đề cũ",
            stance="Ủng hộ",
            difficulty="Trung cấp",
            user_argument="Đây là claim có evidence và reasoning.",
            practice_mode="cer",
            practice_prompt="Có nên giới hạn thời gian sử dụng TikTok?",
            practice_round=2,
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("Chủ đề xây dựng lập luận do Lumi đưa ra", messages[1]["content"])
        self.assertIn("Lượt: 2", messages[1]["content"])
        self.assertIn("Claim, Evidence và Reasoning", messages[1]["content"])

    def test_build_practice_prompt_avoids_exact_repeat(self):
        first = build_practice_prompt("quick_rebuttal", round_number=0)
        second = build_practice_prompt(
            "quick_rebuttal",
            used_prompts=[first["prompt"]],
            round_number=0,
        )

        self.assertEqual(second["mode"], "quick_rebuttal")
        self.assertNotEqual(second["prompt"], first["prompt"])
        self.assertIn(
            second["source"],
            {"local_prompt_bank", "topic_bank", "topic_bank_variant", "fallback_variant"},
        )

    def test_claim_writing_uses_topic_bank(self):
        result = build_practice_prompt("claim_writing", session_id="s1", round_number=1)

        self.assertEqual(result["mode"], "claim_writing")
        self.assertEqual(result["source"], "topic_bank")
        self.assertEqual(result["prompt_type"], "scenario_prompt")
        self.assertIn("Chủ đề:", result["prompt"])
        self.assertTrue(result["topic"])
        self.assertTrue(result["topic_id"])

    def test_find_evidence_uses_topic_bank_claim(self):
        result = build_practice_prompt("find_evidence", session_id="s1", round_number=2)

        self.assertEqual(result["mode"], "find_evidence")
        self.assertEqual(result["source"], "topic_bank")
        self.assertEqual(result["prompt_type"], "claim_prompt")
        self.assertEqual(result["prompt"], result["claim"])
        self.assertTrue(result["claim"])
        self.assertTrue(result["topic"])

    def test_quick_rebuttal_uses_topic_bank_weak_argument(self):
        result = build_practice_prompt("quick_rebuttal", session_id="s1", round_number=3)

        self.assertEqual(result["mode"], "quick_rebuttal")
        self.assertEqual(result["source"], "local_prompt_bank")
        self.assertEqual(result["prompt_type"], "weak_argument")
        self.assertTrue(result["weak_argument"])
        self.assertTrue(result["fallacy_hint"])
        self.assertTrue(result["target_flaws"])
        self.assertTrue(result["expected_rebuttal_points"])
        self.assertGreaterEqual(sentence_count(result["weak_argument"]), 4)
        self.assertLessEqual(sentence_count(result["weak_argument"]), 6)
        self.assertEqual(result["prompt"], result["weak_argument"])
        self.assertEqual(result["instruction"], QUICK_REBUTTAL_INSTRUCTION)
        self.assertNotIn("Luận điểm yếu:", result["prompt"])
        self.assertNotIn("Lập luận yếu:", result["prompt"])
        self.assertNotIn("Lập luận yếu Lập luận yếu", result["prompt"])
        self.assertNotIn("Hãy chỉ ra", result["prompt"])
        self.assertNotRegex(result["prompt"], r"\?\s*(chắc chắn|rõ ràng|đương nhiên|vì)\b")

    def test_quick_rebuttal_local_bank_has_fifty_six_sentence_prompts(self):
        self.assertEqual(len(QUICK_REBUTTAL_PROMPTS), 50)
        self.assertEqual(
            [item["id"] for item in QUICK_REBUTTAL_PROMPTS],
            [f"qr_{index:03d}" for index in range(1, 51)],
        )
        for item in QUICK_REBUTTAL_PROMPTS:
            self.assertEqual(sentence_count(item["weak_argument"]), 6)
            self.assertTrue(item["topic_id"])
            self.assertTrue(item["topic"])
            self.assertTrue(item["fallacy_hint"])
            self.assertGreaterEqual(len(item["target_flaws"]), 2)
            self.assertGreaterEqual(len(item["expected_rebuttal_points"]), 2)

    def test_quick_rebuttal_local_bank_matches_by_topic_id_or_title(self):
        bank_item = QUICK_REBUTTAL_PROMPTS[0]
        by_id = get_quick_rebuttal_prompt_from_bank(
            {"id": bank_item["topic_id"], "title": "Tiêu đề khác"},
            round_number=1,
        )
        by_title = get_quick_rebuttal_prompt_from_bank(
            {"id": "unknown", "title": bank_item["topic"]},
            round_number=2,
        )

        self.assertEqual(by_id["weak_argument"], bank_item["weak_argument"])
        self.assertEqual(by_title["weak_argument"], bank_item["weak_argument"])
        self.assertEqual(by_id["source"], "local_prompt_bank")
        self.assertEqual(by_id["instruction"], QUICK_REBUTTAL_INSTRUCTION)
        self.assertEqual(
            by_id["expected_rebuttal_points"],
            bank_item["expected_rebuttal_points"],
        )

    def test_quick_rebuttal_local_bank_returns_none_for_unknown_topic(self):
        self.assertIsNone(
            get_quick_rebuttal_prompt_from_bank(
                {"id": "unknown", "title": "Chủ đề chưa có trong bank"},
                round_number=1,
            )
        )

        fallback = _build_topic_prompt(
            "quick_rebuttal",
            {
                "id": "unknown",
                "title": "Chủ đề chưa có trong bank",
                "category": "Test",
                "difficulty": "Cơ bản",
            },
            round_number=1,
        )
        self.assertEqual(fallback["source"], "topic_bank")
        self.assertTrue(fallback["weak_argument"])

    def test_quick_rebuttal_has_at_least_eight_fallacy_templates(self):
        hints = {item["fallacy_hint"] for item in FALLACY_TEMPLATES}

        self.assertGreaterEqual(len(FALLACY_TEMPLATES), 8)
        self.assertTrue(
            {
                "khái quát hóa vội vàng",
                "dựa vào số đông",
                "thiếu bằng chứng",
                "nguyên nhân giả",
                "tuyệt đối hóa",
                "đánh tráo vấn đề",
                "người rơm",
                "lưỡng phân giả",
            }.issubset(hints)
        )
        for item in FALLACY_TEMPLATES:
            self.assertTrue(item["target_flaws"])
            rendered = _sanitize_weak_argument(
                item["template"].format(
                    subject_statement="việc học sinh được dùng AI để làm bài tập",
                    subject_statement_cap="Việc học sinh được dùng AI để làm bài tập",
                )
            )
            self.assertGreaterEqual(sentence_count(rendered), 4)
            self.assertLessEqual(sentence_count(rendered), 6)

    def test_clean_sentence_normalizes_spacing_and_terminal_punctuation(self):
        self.assertEqual(
            _clean_sentence("  học sinh dùng AI  , nhưng thiếu kiểm chứng "),
            "Học sinh dùng AI, nhưng thiếu kiểm chứng.",
        )

    def test_topic_to_claim_subject_converts_common_question_forms(self):
        self.assertEqual(
            topic_to_subject_statement(
                "Học sinh có nên được dùng AI để làm bài tập?"
            ),
            "việc học sinh được dùng AI để làm bài tập",
        )
        self.assertEqual(
            topic_to_subject_statement(
                "Robot có nên được dùng để chăm sóc người cao tuổi?"
            ),
            "việc robot được dùng để chăm sóc người cao tuổi",
        )
        self.assertEqual(
            _topic_to_claim_subject(
                "Điểm số có còn là thước đo tốt cho năng lực học sinh?"
            ),
            "việc điểm số là thước đo tốt cho năng lực học sinh",
        )
        self.assertEqual(
            _topic_to_claim_subject(
                "Có nên giới hạn thời gian sử dụng TikTok ở thanh thiếu niên?"
            ),
            "việc giới hạn thời gian sử dụng TikTok ở thanh thiếu niên",
        )
        self.assertEqual(
            _topic_to_claim_subject("Trẻ em có nên được dùng smartphone từ sớm?"),
            "việc trẻ em được dùng smartphone từ sớm",
        )

    def test_sanitize_weak_argument_removes_labels_instruction_and_broken_question(self):
        result = _sanitize_weak_argument(
            "Lập luận yếu: Điểm số có còn là thước đo tốt? "
            "chắc chắn đúng vì ai cũng dùng. "
            "Hãy chỉ ra lỗ hổng, giả định sai hoặc phản ví dụ."
        )

        self.assertEqual(
            result,
            "Điểm số có còn là thước đo tốt chắc chắn đúng vì ai cũng dùng.",
        )
        self.assertNotIn("? chắc chắn", result)
        self.assertNotIn("Lập luận yếu", result)
        self.assertNotIn("Hãy chỉ ra", result)

    def test_quick_rebuttal_topic_builder_is_deterministic_and_returns_raw_text(self):
        topic = {
            "id": "score-measure",
            "title": "Điểm số có còn là thước đo tốt cho năng lực học sinh?",
            "category": "Giáo dục",
            "difficulty": "Trung cấp",
        }

        first = _build_quick_rebuttal_prompt_from_topic(topic, round_number=2)
        second = _build_quick_rebuttal_prompt_from_topic(topic, round_number=2)

        self.assertEqual(first, second)
        self.assertEqual(first["prompt"], first["weak_argument"])
        self.assertEqual(first["instruction"], QUICK_REBUTTAL_INSTRUCTION)
        self.assertTrue(first["fallacy_hint"])
        self.assertTrue(first["target_flaws"])
        self.assertGreaterEqual(sentence_count(first["weak_argument"]), 4)
        self.assertNotIn("Lập luận yếu:", first["weak_argument"])
        self.assertNotIn("Luận điểm yếu:", first["weak_argument"])
        self.assertNotIn("? chắc chắn", first["weak_argument"])
        self.assertTrue(first["weak_argument"].endswith("."))

    def test_full_argument_uses_topic_bank_cer_instruction(self):
        result = build_practice_prompt("full_argument", session_id="s1", round_number=4)

        self.assertEqual(result["mode"], "full_argument")
        self.assertEqual(result["source"], "topic_bank")
        self.assertEqual(result["prompt_type"], "argument_builder")
        self.assertIn("Claim, Evidence và Reasoning", result["instruction"])
        self.assertTrue(result["topic"])
        self.assertTrue(result["topic_id"])
        self.assertTrue(result["category"])
        self.assertTrue(result["difficulty"])

    def test_alias_uses_topic_bank_mode(self):
        result = build_practice_prompt("evidence_practice", session_id="s1")

        self.assertEqual(result["mode"], "find_evidence")
        self.assertEqual(result["source"], "topic_bank")

    @mock.patch("app.services.practice_prompt_service.list_topics")
    @mock.patch("app.services.practice_prompt_service.recommended_topics")
    def test_avoids_previous_topics_when_alternative_exists(self, mocked_recommended, mocked_list):
        mocked_recommended.return_value = []
        mocked_list.return_value = [
            {
                "id": "topic-a",
                "title": "Topic A",
                "category": "Test",
                "difficulty": "Cơ bản",
            },
            {
                "id": "topic-b",
                "title": "Topic B",
                "category": "Test",
                "difficulty": "Cơ bản",
            },
        ]

        result = build_practice_prompt(
            "claim_writing",
            session_id="s1",
            previous_topics=["Topic A"],
        )

        self.assertEqual(result["topic"], "Topic B")

    @mock.patch("app.services.practice_prompt_service.list_topics")
    @mock.patch("app.services.practice_prompt_service.recommended_topics")
    def test_topic_bank_failure_uses_prompt_bank_fallback(self, mocked_recommended, mocked_list):
        mocked_list.side_effect = RuntimeError("topic bank failed")
        mocked_recommended.side_effect = RuntimeError("topic bank failed")

        result = build_practice_prompt("quick_rebuttal", round_number=0)

        self.assertEqual(result["mode"], "quick_rebuttal")
        self.assertEqual(result["source"], "prompt_bank_fallback")
        self.assertIn("prompt", result)
        self.assertTrue(result["weak_argument"])
        self.assertTrue(result["fallacy_hint"])
        self.assertTrue(result["target_flaws"])
        self.assertGreaterEqual(sentence_count(result["weak_argument"]), 4)


if __name__ == "__main__":
    unittest.main()
