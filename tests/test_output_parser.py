import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.output_parser import parse_debate_output  # noqa: E402


VALID_OUTPUT = """
[REBUTTAL]
Việc cấm hoàn toàn có thể quá cực đoan vì điện thoại cũng hỗ trợ học tập nếu được quản lý đúng cách.

[CER]
Claim: 7
Evidence: 3
Reasoning: 6

[FEEDBACK]
Strengths:
- Có quan điểm rõ ràng.
Weaknesses:
- Thiếu bằng chứng cụ thể.
Suggestions:
- Hãy bổ sung ví dụ hoặc số liệu.
""".strip()


class OutputParserTests(unittest.TestCase):
    def test_parses_full_valid_output(self):
        parsed = parse_debate_output(VALID_OUTPUT)

        self.assertTrue(parsed["ok"])
        self.assertTrue(parsed["rebuttal"])
        self.assertEqual(parsed["cer"]["claim"], 7.0)
        self.assertEqual(parsed["cer"]["evidence"], 3.0)
        self.assertEqual(parsed["cer"]["reasoning"], 6.0)
        self.assertEqual(parsed["cer"]["total"], 5.33)
        self.assertEqual(parsed["feedback"]["strengths"], ["Có quan điểm rõ ràng."])
        self.assertEqual(parsed["feedback"]["weaknesses"], ["Thiếu bằng chứng cụ thể."])
        self.assertEqual(parsed["feedback"]["suggestions"], ["Hãy bổ sung ví dụ hoặc số liệu."])

    def test_missing_feedback_returns_default_feedback(self):
        raw = """
[REBUTTAL]
Phản biện vẫn có nội dung.

[CER]
Claim: 6
Evidence: 4
Reasoning: 5
""".strip()
        parsed = parse_debate_output(raw)

        self.assertFalse(parsed["ok"])
        self.assertEqual(parsed["cer"]["total"], 5.0)
        self.assertTrue(parsed["feedback"]["weaknesses"])
        self.assertTrue(parsed["feedback"]["suggestions"])

    def test_missing_cer_returns_zero_scores(self):
        raw = """
[REBUTTAL]
Phản biện vẫn có nội dung.

[FEEDBACK]
Strengths:
- Có ý chính.
Weaknesses:
- Thiếu số liệu.
Suggestions:
- Thêm ví dụ.
""".strip()
        parsed = parse_debate_output(raw)

        self.assertFalse(parsed["ok"])
        self.assertEqual(parsed["cer"]["claim"], 0.0)
        self.assertEqual(parsed["cer"]["total"], 0.0)

    def test_clamps_scores_outside_zero_to_ten(self):
        raw = """
[REBUTTAL]
Phản biện.

[CER]
Claim: 12
Evidence: -2
Reasoning: 8.5

[FEEDBACK]
Strengths:
- Rõ ý.
Weaknesses:
- Có điểm yếu.
Suggestions:
- Cải thiện bằng chứng.
""".strip()
        parsed = parse_debate_output(raw)

        self.assertEqual(parsed["cer"]["claim"], 10.0)
        self.assertEqual(parsed["cer"]["evidence"], 0.0)
        self.assertEqual(parsed["cer"]["reasoning"], 8.5)
        self.assertEqual(parsed["cer"]["total"], 6.17)

    def test_empty_raw_text_returns_safe_fallback(self):
        parsed = parse_debate_output("")

        self.assertFalse(parsed["ok"])
        self.assertEqual(parsed["rebuttal"], "AI không trả về nội dung hợp lệ.")
        self.assertEqual(parsed["cer"]["total"], 0.0)
        self.assertTrue(parsed["feedback"]["weaknesses"])

    def test_parses_vietnamese_bullet_lists(self):
        raw = """
[REBUTTAL]
Phản biện ngắn.

[CER]
Claim: 8
Evidence: 7
Reasoning: 9

[FEEDBACK]
Strengths:
• Luận điểm rõ ràng.
- Biết nêu quan điểm.
Weaknesses:
* Cần thêm dẫn chứng.
Suggestions:
- Bổ sung một ví dụ thực tế.
- Giải thích liên hệ giữa ví dụ và kết luận.
""".strip()
        parsed = parse_debate_output(raw)

        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["feedback"]["strengths"], ["Luận điểm rõ ràng.", "Biết nêu quan điểm."])
        self.assertEqual(parsed["feedback"]["weaknesses"], ["Cần thêm dẫn chứng."])
        self.assertEqual(
            parsed["feedback"]["suggestions"],
            ["Bổ sung một ví dụ thực tế.", "Giải thích liên hệ giữa ví dụ và kết luận."],
        )


if __name__ == "__main__":
    unittest.main()
