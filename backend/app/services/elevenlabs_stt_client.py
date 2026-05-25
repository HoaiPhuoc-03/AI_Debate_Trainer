import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


ELEVENLABS_STT_FRIENDLY_ERROR = (
    "ElevenLabs STT hiện không phản hồi. "
    "Vui lòng kiểm tra cấu hình ElevenLabs hoặc thử lại sau."
)

CONTENT_TYPE_BY_EXTENSION = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
}


def _sanitize_error(message: str) -> str:
    sanitized = str(message or "")
    sanitized = re.sub(r"(xi-api-key[\"':\s]+)[A-Za-z0-9_\-\.]+", r"\1***", sanitized, flags=re.IGNORECASE)
    if settings.ELEVENLABS_API_KEY:
        sanitized = sanitized.replace(settings.ELEVENLABS_API_KEY, "***")
    return sanitized


def _content_type_from_filename(filename: str) -> str:
    lower = str(filename or "").strip().lower()
    for extension, content_type in CONTENT_TYPE_BY_EXTENSION.items():
        if lower.endswith(extension):
            return content_type
    return "application/octet-stream"


def _pick_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()
    if not isinstance(payload, dict):
        return ""

    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    transcripts = payload.get("transcripts")
    if isinstance(transcripts, list):
        parts = [_pick_text(item) for item in transcripts]
        return " ".join(part for part in parts if part).strip()
    if isinstance(transcripts, dict):
        parts = [_pick_text(item) for item in transcripts.values()]
        return " ".join(part for part in parts if part).strip()

    return ""


def _http_error_message(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    detail = ""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("message") or payload.get("error") or response.text
    except ValueError:
        detail = response.text

    detail = _sanitize_error(str(detail)).strip()
    if detail:
        return f"ElevenLabs STT HTTP {response.status_code}: {detail}"
    return _sanitize_error(str(exc)) or ELEVENLABS_STT_FRIENDLY_ERROR


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    api_key = settings.ELEVENLABS_API_KEY.strip()
    base_url = settings.ELEVENLABS_STT_BASE_URL.strip()
    model = settings.ELEVENLABS_STT_MODEL.strip()

    if not api_key:
        raise RuntimeError("Thiếu ELEVENLABS_API_KEY để dùng ElevenLabs STT.")
    if not base_url:
        raise RuntimeError("Thiếu ELEVENLABS_STT_BASE_URL để dùng ElevenLabs STT.")
    if not model:
        raise RuntimeError("Thiếu ELEVENLABS_STT_MODEL để dùng ElevenLabs STT.")

    safe_filename = str(filename or "speech.webm").strip() or "speech.webm"
    content_type = _content_type_from_filename(safe_filename)

    try:
        logger.info(
            "ElevenLabs STT request: URL=%s, model=%s, audio_size=%s bytes, filename=%s",
            base_url,
            model,
            len(audio_bytes),
            safe_filename,
        )
        async with httpx.AsyncClient(timeout=settings.ELEVENLABS_STT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                base_url,
                headers={"xi-api-key": api_key},
                data={"model_id": model},
                files={"file": (safe_filename, audio_bytes, content_type)},
            )
        logger.info("ElevenLabs STT response: status=%s", response.status_code)
        response.raise_for_status()
        payload = response.json()
        text = _pick_text(payload)
        if not text:
            raise RuntimeError("ElevenLabs STT không trả về transcript text.")
        return text
    except httpx.TimeoutException as exc:
        raise RuntimeError(_sanitize_error(str(exc)) or "ElevenLabs STT bị timeout.") from exc
    except (httpx.ConnectError, httpx.NetworkError) as exc:
        raise RuntimeError(_sanitize_error(str(exc)) or "Không kết nối được ElevenLabs STT.") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(_http_error_message(exc)) from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(_sanitize_error(str(exc)) or ELEVENLABS_STT_FRIENDLY_ERROR) from exc
