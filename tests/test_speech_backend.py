import asyncio
import sys
import unittest
from pathlib import Path
from unittest import mock

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

    @mock.patch("app.api.speech.transcribe_audio")
    def test_stt_alias_endpoint_uses_same_response_contract(self, mocked_transcribe):
        mocked_transcribe.return_value = {
            "ok": True,
            "text": "Toi ung ho quan diem nay.",
            "raw_text": "Toi ung ho quan diem nay.",
            "provider": "groq",
            "model": "whisper-large-v3",
            "error": "",
        }

        response = self.client.post(
            "/api/v1/speech/stt",
            content=b"fake-webm-audio",
            headers={"Content-Type": "audio/webm"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript"], "Toi ung ho quan diem nay.")

    def test_transcribe_endpoint_rejects_unsupported_content_type(self):
        response = self.client.post(
            "/api/v1/speech/transcribe",
            content=b"not-audio",
            headers={"Content-Type": "text/plain"},
        )

        self.assertEqual(response.status_code, 415)

    def test_speech_service_rejects_empty_audio(self):
        with mock.patch.object(speech_service.settings, "VOICE_STT_PROVIDER", "elevenlabs"):
            result = speech_service.transcribe_audio(b"", content_type="audio/webm", language="en")

        self.assertFalse(result["ok"])
        self.assertEqual(result["provider"], "elevenlabs")
        self.assertEqual(result["error"], speech_service.EMPTY_AUDIO_ERROR)

    @mock.patch("app.services.speech_service.cleanup_voice_transcript")
    @mock.patch("app.services.speech_service.transcribe_groq_audio")
    def test_stt_provider_groq_uses_groq_with_session_prompt(self, mocked_transcribe, mocked_cleanup):
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

        with mock.patch.object(speech_service.settings, "VOICE_STT_PROVIDER", "groq"):
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

    @mock.patch("app.services.speech_service.cleanup_voice_transcript")
    @mock.patch("app.services.speech_service.transcribe_elevenlabs_audio", new_callable=mock.AsyncMock)
    def test_default_stt_provider_is_elevenlabs(self, mocked_elevenlabs, mocked_cleanup):
        mocked_elevenlabs.return_value = "Ban ghi am tu ElevenLabs."
        mocked_cleanup.return_value = {
            "text": "Ban ghi am tu ElevenLabs.",
            "raw_text": "Ban ghi am tu ElevenLabs.",
            "provider": "groq",
            "model": "llama-test",
            "error": "",
        }

        with (
            mock.patch.object(speech_service.settings, "VOICE_STT_PROVIDER", "elevenlabs"),
            mock.patch.object(speech_service.settings, "VOICE_STT_FALLBACK", ""),
            mock.patch.object(speech_service.settings, "ELEVENLABS_STT_MODEL", "scribe_v2"),
        ):
            result = speech_service.transcribe_audio(b"fake-webm", content_type="audio/webm", language="vi")

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "elevenlabs")
        self.assertEqual(result["model"], "scribe_v2")
        mocked_elevenlabs.assert_awaited_once_with(b"fake-webm", filename="speech.webm")

    @mock.patch("app.services.speech_service.cleanup_voice_transcript")
    @mock.patch("app.services.speech_service.transcribe_groq_audio")
    @mock.patch("app.services.speech_service.transcribe_elevenlabs_audio", new_callable=mock.AsyncMock)
    def test_stt_falls_back_to_groq_when_elevenlabs_fails(
        self,
        mocked_elevenlabs,
        mocked_groq,
        mocked_cleanup,
    ):
        mocked_elevenlabs.side_effect = RuntimeError("ElevenLabs STT loi")
        mocked_groq.return_value = {
            "ok": True,
            "text": "Fallback Groq transcript.",
            "provider": "groq",
            "model": "whisper-large-v3",
            "error": "",
        }
        mocked_cleanup.return_value = {
            "text": "Fallback Groq transcript.",
            "raw_text": "Fallback Groq transcript.",
            "provider": "groq",
            "model": "llama-test",
            "error": "",
        }

        with (
            mock.patch.object(speech_service.settings, "VOICE_STT_PROVIDER", "elevenlabs"),
            mock.patch.object(speech_service.settings, "VOICE_STT_FALLBACK", "groq"),
        ):
            result = speech_service.transcribe_audio(b"fake-webm", content_type="audio/webm", language="vi")

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "groq")
        mocked_groq.assert_called_once()

    def test_invalid_stt_provider_returns_clear_error(self):
        with mock.patch.object(speech_service.settings, "VOICE_STT_PROVIDER", "bad-provider"):
            result = speech_service.transcribe_audio(b"fake-webm", content_type="audio/webm", language="vi")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "INVALID_PROVIDER")
        self.assertIn("VOICE_STT_PROVIDER không hợp lệ", result["error"])

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

    @mock.patch("app.api.speech.synthesize_text", new_callable=mock.AsyncMock)
    def test_synthesize_endpoint_returns_audio_blob(self, mocked_synthesize):
        mocked_synthesize.return_value = {
            "ok": True,
            "audio": b"fake-mp3-audio",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": "vi-VN-NamMinhNeural",
            "error": "",
        }

        response = self.client.post(
            "/api/v1/speech/synthesize",
            json={"text": "Lumi phan bien luot nay."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertEqual(response.headers["x-speech-provider"], "edge")
        self.assertEqual(response.content, b"fake-mp3-audio")
        mocked_synthesize.assert_awaited_once_with("Lumi phan bien luot nay.")

    @mock.patch("app.api.speech.synthesize_text", new_callable=mock.AsyncMock)
    def test_tts_alias_endpoint_uses_same_audio_contract(self, mocked_synthesize):
        mocked_synthesize.return_value = {
            "ok": True,
            "audio": b"fake-mp3-audio",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": "vi-VN-NamMinhNeural",
            "error": "",
        }

        response = self.client.post("/api/v1/speech/tts", json={"text": "Noi thu."})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"fake-mp3-audio")

    def test_speech_service_rejects_empty_tts_text(self):
        result = asyncio.run(speech_service.synthesize_text("   "))

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], speech_service.EMPTY_TTS_TEXT_ERROR)

    @mock.patch("app.services.speech_service._synthesize_with_edge", new_callable=mock.AsyncMock)
    def test_tts_always_uses_edge(self, mocked_edge):
        mocked_edge.return_value = {
            "ok": True,
            "audio": b"edge-audio",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": "vi-VN-NamMinhNeural",
            "error": "",
            "error_code": "",
        }

        result = asyncio.run(speech_service.synthesize_text("Noi thu."))

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "edge")
        mocked_edge.assert_awaited_once_with("Noi thu.")

if __name__ == "__main__":
    unittest.main()
