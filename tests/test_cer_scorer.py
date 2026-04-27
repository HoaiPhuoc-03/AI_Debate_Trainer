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
