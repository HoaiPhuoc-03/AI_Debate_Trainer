import json
import re
import asyncio
import logging
import socket
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.services.elevenlabs_stt_client import transcribe_audio as transcribe_elevenlabs_audio
from app.services.groq_client import call_groq
from app.services.groq_stt_client import transcribe_groq_audio
from app.services.normalization import normalize_stance

logger = logging.getLogger(__name__)


SUPPORTED_AUDIO_TYPES = {
    "audio/webm": "speech.webm",
    "audio/ogg": "speech.ogg",
    "audio/wav": "speech.wav",
    "audio/wave": "speech.wav",
    "audio/x-wav": "speech.wav",
    "audio/flac": "speech.flac",
    "audio/x-flac": "speech.flac",
    "audio/mpeg": "speech.mp3",
    "audio/mp3": "speech.mp3",
    "audio/mp4": "speech.m4a",
    "audio/x-m4a": "speech.m4a",
}

EMPTY_AUDIO_ERROR = "Audio rỗng. Hãy ghi âm lại."
TOO_LARGE_AUDIO_ERROR = "Audio quá lớn. Hãy ghi âm ngắn hơn."
UNSUPPORTED_AUDIO_ERROR = "Định dạng audio chưa được hỗ trợ."
EMPTY_TTS_TEXT_ERROR = "Nội dung đọc không được để trống."
TOO_LONG_TTS_TEXT_ERROR = "Nội dung đọc quá dài. Hãy rút gọn phản biện trước khi phát."

EDGE_TTS_FRIENDLY_ERROR = (
    "Edge TTS hiện không phản hồi. "
    "Vui lòng kiểm tra kết nối internet hoặc thử lại sau."
)
EDGE_TTS_DEPENDENCY_ERROR = (
    "Backend thiếu thư viện edge-tts. "
    "Hãy khởi động ứng dụng bằng scripts\\run_windows_app.ps1."
)
EDGE_TTS_MAX_ATTEMPTS = 5
EDGE_TTS_RETRY_BASE_SECONDS = 1.5
INVALID_STT_PROVIDER_ERROR = (
    "VOICE_STT_PROVIDER không hợp lệ. Chỉ hỗ trợ 'groq' hoặc 'elevenlabs'."
)


def normalize_speech_language(language: str | None) -> str:
    normalized = str(language or "vi").strip().lower().replace("_", "-")
    if normalized.startswith("vi"):
        return "vi"
    return "vi"


def normalize_voice_provider(provider: str | None) -> str:
    normalized = str(provider or "").strip().lower().replace("_", "-")
    aliases = {
        "edge-tts": "edge",
        "groq-whisper": "groq",
        "eleven-labs": "elevenlabs",
    }
    return aliases.get(normalized, normalized)


def format_stt_stance(stance: str | None) -> str:
    normalized = normalize_stance(stance)
    labels = {
        "support": "Ủng hộ",
        "oppose": "Phản đối",
    }
    return labels.get(normalized, "Ủng hộ")


def run_async_blocking(async_fn, *args, **kwargs):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(async_fn(*args, **kwargs))

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(async_fn(*args, **kwargs))).result()


def validate_audio_request(audio_bytes: bytes, content_type: str) -> tuple[bool, str, str]:
    if not audio_bytes:
        return False, EMPTY_AUDIO_ERROR, "EMPTY_AUDIO"
    if len(audio_bytes) > settings.SPEECH_MAX_AUDIO_BYTES:
        return False, TOO_LARGE_AUDIO_ERROR, "AUDIO_TOO_LARGE"
    if content_type not in SUPPORTED_AUDIO_TYPES:
        return False, UNSUPPORTED_AUDIO_ERROR, "UNSUPPORTED_FORMAT"
    return True, "", ""


def build_groq_stt_prompt(session_context: dict | None = None) -> str:
    context = session_context or {}
    topic = str(context.get("topic") or "").strip()
    stance = format_stt_stance(context.get("stance"))
    difficulty = str(context.get("difficulty") or "").strip()
    parts = [
        "Đây là bản ghi âm tiếng Việt trong ứng dụng luyện tranh biện.",
        "Hãy phiên âm đúng tiếng Việt, giữ thuật ngữ theo chủ đề, không dịch sang tiếng Anh.",
    ]
    if topic:
        parts.append(f"Chủ đề: {topic}.")
    if stance:
        parts.append(f"Lập trường người nói: {stance}.")
    if difficulty:
        parts.append(f"Độ khó: {difficulty}.")
    return " ".join(parts)


def _extract_json_object(text: str) -> dict:
    clean = str(text or "").strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    try:
        payload = json.loads(clean)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
        if not match:
            return {}
        try:
            payload = json.loads(match.group(0))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}


def cleanup_voice_transcript(raw_text: str, *, session_context: dict | None = None) -> dict:
    raw = str(raw_text or "").strip()
    if not raw:
        return {"text": "", "raw_text": "", "provider": "", "model": "", "error": ""}

    context = session_context or {}
    topic = str(context.get("topic") or "").strip()
    stance = format_stt_stance(context.get("stance"))
    difficulty = str(context.get("difficulty") or "").strip()
    context_hint = (
        f"Chủ đề tranh biện: {topic or 'không có chủ đề cụ thể'}\n"
        f"Lập trường người nói: {stance or 'không rõ'}\n"
        f"Độ khó: {difficulty or 'không rõ'}"
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là bộ sửa transcript tiếng Việt cho ứng dụng luyện tranh biện bằng giọng nói. "
                "Nhiệm vụ của bạn là biến transcript thô từ STT thành câu tiếng Việt tự nhiên, đúng ngữ cảnh tranh biện nhất. "
                "Hãy sửa mạnh các cụm bị nghe sai theo ngữ cảnh, nhất là cụm vô nghĩa hoặc lệch chủ đề nhưng gần âm. "
                "Được sửa dấu câu, chính tả, từ bị nhận nhầm, thứ tự câu và cách ngắt ý. "
                "Không thêm luận điểm mới, không thêm bằng chứng mới, không đổi lập trường, không làm văn phong khác ý người nói. "
                "Không bịa thêm nội dung, không suy diễn ý mới ngoài những gì transcript thô và ngữ cảnh hỗ trợ. "
                "Chú ý các cụm từ khẳng định/phủ định như có, không, nên, không nên; phải giữ nguyên chiều ý của người nói. "
                "Nếu không chắc một cụm nào, hãy giữ gần với âm thanh gốc thay vì tự bịa nội dung. "
                'Chỉ trả về JSON hợp lệ duy nhất dạng {"transcript":"..."}.'
            ),
        },
        {
            "role": "user",
            "content": (
                f"{context_hint}\n\n"
                f"Transcript thô từ STT:\n{raw}\n\n"
                "Hãy sửa transcript này theo ngữ cảnh trên. "
                "Ưu tiên khôi phục ý người nói trong một lượt tranh biện ngắn, không giải thích thêm."
            ),
        },
    ]
    result = call_groq(messages, max_tokens=260, temperature=0.0)
    if not result["ok"]:
        return {
            "text": raw,
            "raw_text": raw,
            "provider": result.get("provider", "groq"),
            "model": result.get("model", ""),
            "error": result.get("error") or result.get("text", ""),
        }

    payload = _extract_json_object(result["text"])
    cleaned = str(payload.get("transcript") or "").strip()
    if not cleaned:
        cleaned = result["text"].strip().strip('"')
    if not cleaned:
        cleaned = raw

    return {
        "text": cleaned,
        "raw_text": raw,
        "provider": result.get("provider", "groq"),
        "model": result.get("model", ""),
        "error": result.get("error", ""),
    }

def _apply_transcript_cleanup(result: dict, *, session_context: dict | None = None) -> dict:
    if result.get("ok"):
        cleanup = cleanup_voice_transcript(result["text"], session_context=session_context)
        result["raw_text"] = cleanup["raw_text"]
        result["text"] = cleanup["text"]
        result["cleanup_provider"] = cleanup["provider"]
        result["cleanup_model"] = cleanup["model"]
        result["cleanup_error"] = cleanup["error"]
    return result


def _transcribe_with_groq(
    audio_bytes: bytes,
    *,
    content_type: str,
    language: str | None = None,
    session_context: dict | None = None,
) -> dict:
    logger.info("[STT] Using provider: groq")
    result = transcribe_groq_audio(
        audio_bytes,
        filename=SUPPORTED_AUDIO_TYPES[content_type],
        content_type=content_type,
        language=normalize_speech_language(language),
        prompt=build_groq_stt_prompt(session_context),
    )
    return _apply_transcript_cleanup(result, session_context=session_context)


def _transcribe_with_elevenlabs(
    audio_bytes: bytes,
    *,
    content_type: str,
    session_context: dict | None = None,
) -> dict:
    logger.info("[STT] Using provider: elevenlabs")
    text = run_async_blocking(
        transcribe_elevenlabs_audio,
        audio_bytes,
        filename=SUPPORTED_AUDIO_TYPES[content_type],
    )
    result = {
        "ok": True,
        "text": text,
        "provider": "elevenlabs",
        "model": settings.ELEVENLABS_STT_MODEL,
        "error": "",
        "error_code": "",
    }
    return _apply_transcript_cleanup(result, session_context=session_context)


def transcribe_audio(
    audio_bytes: bytes,
    *,
    content_type: str,
    language: str | None = None,
    session_context: dict | None = None,
) -> dict:
    provider = normalize_voice_provider(settings.VOICE_STT_PROVIDER) or "groq"
    fallback = normalize_voice_provider(settings.VOICE_STT_FALLBACK)

    is_valid, message, error_code = validate_audio_request(audio_bytes, content_type)
    if not is_valid:
        return {
            "ok": False,
            "text": "",
            "provider": provider,
            "model": settings.GROQ_STT_MODEL if provider == "groq" else settings.ELEVENLABS_STT_MODEL,
            "error": message,
            "error_code": error_code,
        }

    if provider == "groq":
        return _transcribe_with_groq(
            audio_bytes,
            content_type=content_type,
            language=language,
            session_context=session_context,
        )

    if provider == "elevenlabs":
        try:
            return _transcribe_with_elevenlabs(
                audio_bytes,
                content_type=content_type,
                session_context=session_context,
            )
        except Exception as exc:
            if fallback == "groq":
                logger.info("[STT] ElevenLabs failed, fallback to Groq Whisper")
                return _transcribe_with_groq(
                    audio_bytes,
                    content_type=content_type,
                    language=language,
                    session_context=session_context,
                )
            return {
                "ok": False,
                "text": "",
                "provider": "elevenlabs",
                "model": settings.ELEVENLABS_STT_MODEL,
                "error": str(exc),
                "error_code": "PROVIDER_ERROR",
            }

    return {
        "ok": False,
        "text": "",
        "provider": provider,
        "model": "",
        "error": INVALID_STT_PROVIDER_ERROR,
        "error_code": "INVALID_PROVIDER",
    }


async def synthesize_text(text: str) -> dict:
    clean = sanitize_tts_text(text)
    if not clean:
        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": EMPTY_TTS_TEXT_ERROR,
            "error_code": "EMPTY_TEXT",
        }
    if len(clean) > settings.SPEECH_TTS_MAX_CHARS:
        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": TOO_LONG_TTS_TEXT_ERROR,
            "error_code": "TEXT_TOO_LONG",
        }

    return await _synthesize_with_edge(clean)


def sanitize_tts_text(text: str) -> str:
    clean = str(text or "").strip()
    clean = re.sub(r"```(?:\w+)?\s*([\s\S]*?)```", r"\1", clean)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"[*_#>]+", "", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


async def _synthesize_with_edge(clean: str) -> dict:
    """
    Tổng hợp giọng nói bằng edge-tts (Microsoft Edge TTS).
    Trả về bytes audio MP3 trực tiếp trong memory - không ghi file.
    """
    logger.info("[TTS] Using provider: edge")
    connector = None
    try:
        import aiohttp
        import edge_tts

        for attempt in range(1, EDGE_TTS_MAX_ATTEMPTS + 1):
            # The Edge websocket can connect over IPv6 but return an empty
            # stream on some Windows networks. Use a fresh IPv4 connection.
            connector = aiohttp.TCPConnector(family=socket.AF_INET)
            try:
                communicate = edge_tts.Communicate(
                    text=clean,
                    voice=settings.EDGE_TTS_VOICE,
                    rate=settings.EDGE_TTS_RATE,
                    connector=connector,
                )
                audio_chunks: list[bytes] = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        data = chunk.get("data")
                        if data:
                            audio_chunks.append(data)

                audio_bytes = b"".join(audio_chunks)
                if audio_bytes:
                    return {
                        "ok": True,
                        "audio": audio_bytes,
                        "content_type": "audio/mpeg",
                        "provider": "edge",
                        "model": settings.EDGE_TTS_VOICE,
                        "error": "",
                        "error_code": "",
                    }
            except edge_tts.exceptions.NoAudioReceived:
                logger.warning(
                    "[TTS] Edge returned no audio on attempt %s/%s",
                    attempt,
                    EDGE_TTS_MAX_ATTEMPTS,
                )
            finally:
                if not connector.closed:
                    await connector.close()
                connector = None

            if attempt < EDGE_TTS_MAX_ATTEMPTS:
                retry_delay = EDGE_TTS_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
                await asyncio.sleep(retry_delay)

        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": EDGE_TTS_FRIENDLY_ERROR,
            "error_code": "EMPTY_AUDIO_RESPONSE",
        }
    except asyncio.TimeoutError:
        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": EDGE_TTS_FRIENDLY_ERROR,
            "error_code": "TIMEOUT",
        }
    except ModuleNotFoundError as exc:
        if exc.name not in {"aiohttp", "edge_tts"}:
            raise
        logger.exception("[TTS] edge-tts dependency is missing")
        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": EDGE_TTS_DEPENDENCY_ERROR,
            "error_code": "MISSING_DEPENDENCY",
        }
    except Exception as exc:
        return {
            "ok": False,
            "audio": b"",
            "content_type": "audio/mpeg",
            "provider": "edge",
            "model": settings.EDGE_TTS_VOICE,
            "error": str(exc) or EDGE_TTS_FRIENDLY_ERROR,
            "error_code": "UNKNOWN_ERROR",
        }
    finally:
        if connector is not None and not connector.closed:
            await connector.close()
