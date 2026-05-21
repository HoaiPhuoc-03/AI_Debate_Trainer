import sys
import unittest
from pathlib import Path
from unittest import mock

import httpx
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from app.services import groq_stt_client, speech_service  # noqa: E402


class SpeechBackendTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @mock.patch("app.api.speech.transcribe_audio")
    def test_transcribe_endpoint_accepts_raw_audio_blob(self, mocked_transcribe):
        mocked_transcribe.return_value = {
            "ok": True,
            "text": "Students should practice debate every week.",
            "provider": "groq",
            "model": "whisper-large-v3",
            "error": "",
        }

        response = self.client.post(
            "/api/v1/speech/transcribe?language=en",
            content=b"fake-webm-audio",
            headers={"Content-Type": "audio/webm"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "transcript": "Students should practice debate every week.",
                "raw_transcript": "Students should practice debate every week.",
                "provider": "groq",
                "model": "whisper-large-v3",
            },
        )
        mocked_transcribe.assert_called_once_with(
            b"fake-webm-audio",
            content_type="audio/webm",
            language="vi",
            session_context=None,
        )

    def test_transcribe_endpoint_rejects_unsupported_content_type(self):
        response = self.client.post(
            "/api/v1/speech/transcribe",
            content=b"not-audio",
            headers={"Content-Type": "text/plain"},
        )

        self.assertEqual(response.status_code, 415)

    def test_speech_service_rejects_empty_audio(self):
        result = speech_service.transcribe_audio(b"", content_type="audio/webm", language="en")

        self.assertFalse(result["ok"])
        self.assertEqual(result["provider"], "groq")
        self.assertEqual(result["model"], "whisper-large-v3")
        self.assertEqual(result["error"], "Audio rỗng. Hãy ghi âm lại.")

    @mock.patch("app.services.speech_service.cleanup_voice_transcript")
    @mock.patch("app.services.speech_service.transcribe_groq_audio")
    def test_speech_service_uses_groq_stt_with_session_prompt(self, mocked_transcribe, mocked_cleanup):
        mocked_transcribe.return_value = {
            "ok": True,
            "text": "Toi ung ho sinh vien nam nhat di lam them.",
            "provider": "groq",
            "model": "whisper-large-v3",
            "error": "",
        }
        mocked_cleanup.return_value = {
            "text": "Toi ung ho sinh vien nam nhat di lam them.",
            "raw_text": "Toi ung ho sinh vien nam nhat di lam them.",
            "provider": "groq",
            "model": "llama-test",
            "error": "",
        }

        result = speech_service.transcribe_audio(
            b"fake-webm",
            content_type="audio/webm",
            language="vi",
            session_context={
                "topic": "Sinh vien nam nhat co nen di lam them?",
                "stance": "Ung ho",
                "difficulty": "Co ban",
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Toi ung ho sinh vien nam nhat di lam them.")
        mocked_transcribe.assert_called_once()
        _, kwargs = mocked_transcribe.call_args
        self.assertEqual(kwargs["filename"], "speech.webm")
        self.assertEqual(kwargs["content_type"], "audio/webm")
        self.assertEqual(kwargs["language"], "vi")
        self.assertIn("Sinh vien nam nhat co nen di lam them?", kwargs["prompt"])
        self.assertIn("Ung ho", kwargs["prompt"])
        self.assertIn("không dịch sang tiếng Anh", kwargs["prompt"])

    @mock.patch("app.services.groq_stt_client.httpx.post")
    def test_groq_stt_posts_audio_with_whisper_large_v3_and_prompt(self, mocked_post):
        response = mock.Mock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {"text": "Xin chao tu Groq Whisper."}
        mocked_post.return_value = response

        with (
            mock.patch.object(groq_stt_client.settings, "GROQ_API_KEY", "test-groq-key"),
            mock.patch.object(groq_stt_client.settings, "GROQ_STT_MODEL", "whisper-large-v3"),
        ):
            result = groq_stt_client.transcribe_groq_audio(
                b"fake-webm",
                filename="speech.webm",
                content_type="audio/webm",
                language="vi",
                prompt="Chu de: Sinh vien nam nhat co nen di lam them?",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Xin chao tu Groq Whisper.")
        _, kwargs = mocked_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-groq-key")
        self.assertNotIn("Content-Type", kwargs["headers"])
        self.assertEqual(kwargs["data"]["model"], "whisper-large-v3")
        self.assertEqual(kwargs["data"]["language"], "vi")
        self.assertEqual(kwargs["data"]["response_format"], "json")
        self.assertEqual(kwargs["data"]["temperature"], "0")
        self.assertIn("Sinh vien nam nhat", kwargs["data"]["prompt"])
        self.assertEqual(kwargs["files"]["file"], ("speech.webm", b"fake-webm", "audio/webm"))

    @mock.patch("app.services.speech_service.call_groq")
    def test_speech_cleanup_uses_session_topic_context(self, mocked_groq):
        mocked_groq.return_value = {
            "ok": True,
            "text": '{"transcript":"Toi la sinh vien nam nhat, co nen di lam them."}',
            "provider": "groq",
            "model": "llama-test",
            "error": "",
        }

        result = speech_service.cleanup_voice_transcript(
            "Toi la sinh vien nam nhat du gi tang them.",
            session_context={
                "topic": "sinh vien nam nhat co nen di lam them",
                "stance": "ung ho",
                "difficulty": "co ban",
            },
        )

        self.assertEqual(result["text"], "Toi la sinh vien nam nhat, co nen di lam them.")
        self.assertEqual(result["raw_text"], "Toi la sinh vien nam nhat du gi tang them.")
        self.assertIn("sinh vien nam nhat co nen di lam them", mocked_groq.call_args.args[0][1]["content"])
        self.assertIn("Không bịa thêm nội dung", mocked_groq.call_args.args[0][0]["content"])
        self.assertIn("có, không, nên, không nên", mocked_groq.call_args.args[0][0]["content"])

    @mock.patch("app.services.speech_service.call_groq")
    def test_speech_cleanup_runs_even_without_session_topic(self, mocked_groq):
        mocked_groq.return_value = {
            "ok": True,
            "text": '{"transcript":"Toi la sinh vien nam nhat, co nen di lam them."}',
            "provider": "groq",
            "model": "llama-test",
            "error": "",
        }

        result = speech_service.cleanup_voice_transcript("Toi la sinh vien nam nhat du gi tang them.")

        self.assertEqual(result["text"], "Toi la sinh vien nam nhat, co nen di lam them.")
        self.assertEqual(result["raw_text"], "Toi la sinh vien nam nhat du gi tang them.")
        mocked_groq.assert_called_once()
        self.assertIn("không có chủ đề cụ thể", mocked_groq.call_args.args[0][1]["content"])

    @mock.patch("app.api.speech.synthesize_text")
    def test_synthesize_endpoint_returns_zalo_audio_blob(self, mocked_synthesize):
        mocked_synthesize.return_value = {
            "ok": True,
            "audio": b"fake-wav-audio",
            "content_type": "audio/wav",
            "provider": "zalo_ai",
            "model": "zalo-ai-tts",
            "error": "",
        }

        response = self.client.post(
            "/api/v1/speech/synthesize",
            json={"text": "Lumi phan bien luot nay."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/wav")
        self.assertEqual(response.headers["x-speech-provider"], "zalo_ai")
        self.assertEqual(response.content, b"fake-wav-audio")
        mocked_synthesize.assert_called_once_with("Lumi phan bien luot nay.")

    def test_speech_service_rejects_empty_tts_text(self):
        result = speech_service.synthesize_text("   ")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "Nội dung đọc không được để trống.")

    @mock.patch("app.services.zalo_ai_client.httpx.post")
    def test_zalo_tts_rate_limit_is_reported_as_rate_limit(self, mocked_post):
        response = mock.Mock()
        response.status_code = 429
        response.text = '{"error_code":429,"error_message":"API rate limit exceeded"}'
        response.json.return_value = {
            "error_code": 429,
            "error_message": "API rate limit exceeded",
        }
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests",
            request=mock.Mock(),
            response=response,
        )
        mocked_post.return_value = response

        result = speech_service.synthesize_text("Lumi phan bien luot nay.")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "RATE_LIMIT")
        self.assertIn("Zalo AI HTTP 429", result["error"])

    @mock.patch("app.api.speech.synthesize_text")
    def test_synthesize_endpoint_returns_429_for_tts_rate_limit(self, mocked_synthesize):
        mocked_synthesize.return_value = {
            "ok": False,
            "audio": b"",
            "content_type": "audio/wav",
            "provider": "zalo_ai",
            "model": "zalo-ai-tts",
            "error": "Zalo AI HTTP 429: error_code=429: API rate limit exceeded",
            "error_code": "RATE_LIMIT",
        }

        response = self.client.post(
            "/api/v1/speech/synthesize",
            json={"text": "Lumi phan bien luot nay."},
        )

        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
