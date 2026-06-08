import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.cer_scorer import (  # noqa: E402
    normalize_cer_to_100,
    parse_cer_rubric_output,
    validate_user_argument,
)
from app.services.ai_service import _needs_rebuttal_repair  # noqa: E402


class CERRubricTests(unittest.TestCase):
    def test_parse_llm_json_rubric_output(self):
        raw = """
```json
{
  "is_valid": true,
  "claim_score": 68,
  "evidence_score": 32,
  "reasoning_score": 55,
  "overall_score": 52.9,
  "claim_breakdown": {"clarity": 30, "relevance": 23, "specificity": 15},
  "evidence_breakdown": {"presence": 15, "specificity": 7, "relevance": 10},
  "reasoning_breakdown": {"logical_connection": 25, "causal_explanation": 18, "fallacy_control": 12},
  "claim_explanation": "Rõ nhưng chưa đủ cụ thể.",
  "evidence_explanation": "Thiếu ví dụ.",
  "reasoning_explanation": "Có lý do nhưng còn đơn giản.",
  "strengths": ["Có quan điểm chính rõ."],
  "weaknesses": ["Thiếu bằng chứng cụ thể."],
  "suggestions": ["Thêm ví dụ hoặc số liệu."]
}
```
""".strip()

        result = parse_cer_rubric_output(raw)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["cer"]["claim"], 68.0)
        self.assertEqual(result["cer"]["evidence"], 32.0)
        self.assertEqual(result["cer"]["reasoning"], 55.0)
        self.assertEqual(result["cer"]["overall"], 52.0)
        self.assertEqual(result["cer_breakdown"]["claim"]["clarity"], 30.0)
        self.assertEqual(result["feedback"]["weaknesses"], ["Thiếu bằng chứng cụ thể."])

    def test_parse_error_uses_safe_default_scores(self):
        result = parse_cer_rubric_output("not json")

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["cer"]["claim"], 50.0)
        self.assertEqual(result["cer"]["evidence"], 40.0)
        self.assertEqual(result["cer"]["reasoning"], 50.0)
        self.assertEqual(result["cer"]["overall"], 47.0)
        self.assertTrue(result["feedback"]["weaknesses"])

    def test_quick_rebuttal_parse_error_uses_mode_specific_feedback(self):
        result = parse_cer_rubric_output("not json", mode="quick_rebuttal")
        feedback_text = " ".join(
            item
            for group in result["feedback"].values()
            for item in group
        )

        self.assertTrue(result["is_valid"])
        self.assertIn("cer", result)
        self.assertIn("feedback", result)
        self.assertIn("lỗi", feedback_text)
        self.assertNotIn("Không có lập luận logic", feedback_text)
        self.assertNotIn("Thiếu bằng chứng cụ thể", feedback_text)
        self.assertNotIn("C-E-R", feedback_text)

    def test_quick_rebuttal_json_keeps_contract_and_overall_score(self):
        raw = """
{
  "is_valid": true,
  "ai_rebuttal": "Bạn đã bắt đúng cụm yếu trong lập luận và giải thích được vì sao khẳng định đó chưa được chứng minh.",
  "evidence_quote": "NONE",
  "checklist": {"has_real_evidence": false, "identified_weak_argument": true, "has_counter_example": true},
  "claim_score": 72,
  "evidence_score": 58,
  "reasoning_score": 66,
  "overall_score": 64,
  "claim_breakdown": {"clarity": 30, "relevance": 22, "specificity": 20},
  "evidence_breakdown": {"presence": 25, "specificity": 18, "relevance": 15},
  "reasoning_breakdown": {"logical_connection": 28, "causal_explanation": 24, "fallacy_control": 14}
}
""".strip()

        result = parse_cer_rubric_output(raw, mode="quick_rebuttal")

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["cer"]["claim"], 72.0)
        self.assertEqual(result["cer"]["evidence"], 58.0)
        self.assertEqual(result["cer"]["reasoning"], 66.0)
        self.assertEqual(result["cer"]["overall"], 64.0)
        self.assertTrue(result["feedback"]["strengths"])
        self.assertTrue(result["feedback"]["weaknesses"])
        self.assertTrue(result["feedback"]["suggestions"])

    def test_parse_groq_marker_rubric_output(self):
        raw = """
[REBUTTAL]
Không nên kết luận quá nhanh rằng sinh viên năm nhất chắc chắn không nên đi làm thêm, vì vấn đề nằm ở cách cân bằng thời gian và loại công việc. Nếu công việc ít giờ, liên quan đến ngành học hoặc giúp rèn kỹ năng mềm, nó có thể hỗ trợ việc học thay vì chỉ gây hại. Lập luận này cũng bỏ qua khác biệt về hoàn cảnh tài chính của từng sinh viên. Vì vậy, phản đối hoàn toàn là chưa đủ linh hoạt.

[CER]
Claim: 72/100
Evidence: 38/100
Reasoning: 64/100
Overall: 59/100

[FEEDBACK]
Strengths:
- Có quan điểm rõ.
- Nêu được hệ quả với việc học.

Weaknesses:
- Thiếu ví dụ cụ thể.

Suggestions:
- Thêm điều kiện về số giờ làm.
- Nêu một dẫn chứng thực tế.
""".strip()

        result = parse_cer_rubric_output(raw)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["cer"]["claim"], 72.0)
        self.assertEqual(result["cer"]["evidence"], 38.0)
        self.assertEqual(result["cer"]["reasoning"], 64.0)
        self.assertEqual(result["cer"]["overall"], 59.0)
        self.assertEqual(result["feedback"]["strengths"], ["Có quan điểm rõ.", "Nêu được hệ quả với việc học."])
        self.assertEqual(result["cer_breakdown"]["claim"]["clarity"], 28.8)

    def test_invalid_input_validation(self):
        validation = validate_user_argument("Sinh viên đi làm thêm", "ok tùy")

        self.assertFalse(validation["is_valid"])
        self.assertEqual(validation["reason"], "too_short")

    def test_normalize_cer_to_100_keeps_hundred_scale(self):
        cer = normalize_cer_to_100({"claim": 75, "evidence": 45, "reasoning": 65, "overall": 62})

        self.assertEqual(cer["claim"], 75.0)
        self.assertEqual(cer["evidence"], 45.0)
        self.assertEqual(cer["reasoning"], 65.0)
        self.assertEqual(cer["overall"], 62.0)
        self.assertEqual(cer["total"], 62.0)

    def test_normalize_cer_to_100_supports_legacy_zero_to_one(self):
        cer = normalize_cer_to_100({"claim": 0.7, "evidence": 0.5, "reasoning": 0.6, "total": 0.6})

        self.assertEqual(cer["claim"], 70.0)
        self.assertEqual(cer["evidence"], 50.0)
        self.assertEqual(cer["reasoning"], 60.0)
        self.assertEqual(cer["overall"], 60.0)

    def test_ai_service_detects_invalid_or_template_rebuttal(self):
        self.assertTrue(_needs_rebuttal_repair("<rebuttal>"))
        self.assertTrue(_needs_rebuttal_repair("Lập luận của bạn có thể thuyết phục hơn nếu cung cấp số liệu cụ thể."))

        natural_rebuttal = (
            "Ở góc nhìn phản biện, kết luận này chưa đủ chắc vì nó bỏ qua điều kiện quản lý và bối cảnh sử dụng. "
            "Nếu có quy định rõ, người học vẫn có thể khai thác công cụ mà không biến nó thành đường tắt gian lận."
        )
        self.assertFalse(_needs_rebuttal_repair(natural_rebuttal))


if __name__ == "__main__":
    unittest.main()
