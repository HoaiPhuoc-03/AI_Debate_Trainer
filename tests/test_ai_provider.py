import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.services import ai_service  # noqa: E402


MARKER_RESPONSE = """
[REBUTTAL]
Không nên kết luận quá nhanh rằng lựa chọn này luôn đúng, vì tác động thực tế phụ thuộc vào bối cảnh và cách triển khai. Nếu người học có kế hoạch rõ ràng, giới hạn thời gian và được hỗ trợ phù hợp, rủi ro có thể giảm đáng kể. Lập luận hiện tại cũng chưa xét đến các ngoại lệ như nhu cầu tài chính hoặc cơ hội rèn kỹ năng. Vì vậy, kết luận cần điều kiện cụ thể hơn thay vì áp dụng cho mọi trường hợp.

[CER]
Claim: 70/100
Evidence: 40/100
Reasoning: 65/100
Overall: 59/100

[FEEDBACK]
Strengths:
- Có lập trường rõ.

Weaknesses:
- Thiếu dẫn chứng cụ thể.

Suggestions:
- Thêm ví dụ thực tế.
""".strip()


class AIGroqOnlyTests(unittest.TestCase):
    def setUp(self):
        self.original_key = settings.GROQ_API_KEY
        self.original_model = settings.GROQ_MODEL

    def tearDown(self):
        settings.GROQ_API_KEY = self.original_key
        settings.GROQ_MODEL = self.original_model

    def test_call_groq_without_key_returns_friendly_error(self):
        settings.GROQ_API_KEY = ""

        result = ai_service.call_groq([{"role": "user", "content": "hello"}])

        self.assertFalse(result["ok"])
        self.assertEqual(result["provider"], "groq")
        self.assertIn("GROQ_API_KEY", result["error"])

    @mock.patch("app.services.ai_service.call_groq")
    def test_generate_analysis_uses_groq_marker_output(self, mocked_groq):
        mocked_groq.return_value = {
            "ok": True,
            "text": MARKER_RESPONSE,
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "error": "",
        }

        result = ai_service.generate_debate_analysis(
            topic="Sinh viên có nên đi làm thêm năm nhất?",
            stance="support",
            difficulty="intermediate",
            user_argument="Tôi nghĩ sinh viên không nên đi làm thêm năm nhất vì ảnh hưởng việc học.",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "groq")
        self.assertEqual(result["cer"]["claim"], 70.0)
        mocked_groq.assert_called_once()

    @mock.patch("app.services.ai_service.call_groq")
    def test_groq_error_does_not_use_sample_rebuttal(self, mocked_groq):
        mocked_groq.return_value = {
            "ok": False,
            "text": ai_service.GROQ_FRIENDLY_ERROR,
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "error": "rate limit",
        }

        result = ai_service.generate_debate_analysis(
            topic="Sinh viên có nên đi làm thêm năm nhất?",
            stance="support",
            difficulty="intermediate",
            user_argument="Tôi nghĩ sinh viên không nên đi làm thêm năm nhất vì ảnh hưởng việc học.",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["rebuttal"], ai_service.GROQ_FRIENDLY_ERROR)
        self.assertEqual(result["cer"]["overall"], 0.0)

    @mock.patch("app.services.ai_service.call_groq")
    def test_bad_groq_format_reports_error_without_sample_rebuttal(self, mocked_groq):
        mocked_groq.return_value = {
            "ok": True,
            "text": "not a structured answer",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "error": "",
        }

        result = ai_service.generate_debate_analysis(
            topic="Sinh viên có nên đi làm thêm năm nhất?",
            stance="support",
            difficulty="intermediate",
            user_argument="Tôi nghĩ sinh viên không nên đi làm thêm năm nhất vì ảnh hưởng việc học.",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["rebuttal"], ai_service.GROQ_FORMAT_ERROR)


if __name__ == "__main__":
    unittest.main()
