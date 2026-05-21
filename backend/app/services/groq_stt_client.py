import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


GROQ_STT_FRIENDLY_ERROR = (
    "Groq Whisper Speech-to-Text hiện không phản hồi. "
    "Vui lòng kiểm tra GROQ_API_KEY hoặc thử lại sau."
)


def sanitize_groq_stt_error(message: str) -> str:
    sanitized = str(message or "")
    sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1***", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"gsk_[A-Za-z0-9_\-]+", "gsk_***", sanitized)
    if settings.GROQ_API_KEY:
        sanitized = sanitized.replace(settings.GROQ_API_KEY, "***")
    return sanitized


def _pick_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, dict):
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return ""


def _groq_http_error_message(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    detail = ""
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code") or ""
        elif isinstance(payload, dict):
            detail = payload.get("message") or payload.get("detail") or response.text
    except ValueError:
        detail = response.text

    detail = sanitize_groq_stt_error(detail).strip()
    if detail:
        return f"Groq STT HTTP {response.status_code}: {detail}"
    return sanitize_groq_stt_error(str(exc)) or GROQ_STT_FRIENDLY_ERROR


def transcribe_groq_audio(
    audio_bytes: bytes,
    *,
    filename: str = "speech.webm",
    content_type: str = "audio/webm",
    language: str | None = None,
    prompt: str | None = None,
) -> dict:
    if not settings.GROQ_API_KEY.strip():
        return {
            "ok": False,
            "text": "",
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": "GROQ_API_KEY is missing.",
            "error_code": "MISSING_CONFIG",
        }

    data = {
        "model": settings.GROQ_STT_MODEL,
        "response_format": "json",
        "temperature": "0",
    }
    if language:
        data["language"] = language
    clean_prompt = str(prompt or "").strip()
    if clean_prompt:
        data["prompt"] = clean_prompt

    try:
        logger.info(
            "Groq STT request: URL=%s, model=%s, audio_size=%s bytes, content_type=%s",
            settings.GROQ_STT_BASE_URL,
            settings.GROQ_STT_MODEL,
            len(audio_bytes),
            content_type,
        )
        response = httpx.post(
            settings.GROQ_STT_BASE_URL,
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            data=data,
            files={"file": (filename, audio_bytes, content_type)},
            timeout=settings.GROQ_STT_TIMEOUT_SECONDS,
        )
        logger.info("Groq STT response: status=%s", response.status_code)
        response.raise_for_status()
        payload = response.json()
        text = _pick_text(payload)
        if not text:
            raise ValueError("Groq transcription response did not contain transcript text")
        return {
            "ok": True,
            "text": text,
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": "",
            "error_code": "",
        }
    except httpx.TimeoutException as exc:
        logger.error("Groq STT timeout: %s", exc)
        return {
            "ok": False,
            "text": "",
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": sanitize_groq_stt_error(str(exc)) or GROQ_STT_FRIENDLY_ERROR,
            "error_code": "TIMEOUT",
        }
    except (httpx.ConnectError, httpx.NetworkError) as exc:
        logger.error("Groq STT network error: %s", exc)
        return {
            "ok": False,
            "text": "",
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": sanitize_groq_stt_error(str(exc)) or GROQ_STT_FRIENDLY_ERROR,
            "error_code": "NETWORK_ERROR",
        }
    except httpx.HTTPStatusError as exc:
        logger.error("Groq STT HTTP error: status=%s, body=%s", exc.response.status_code, exc.response.text)
        return {
            "ok": False,
            "text": "",
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": _groq_http_error_message(exc),
            "error_code": "HTTP_ERROR",
        }
    except Exception as exc:
        logger.error("Groq STT unknown error: %s", exc, exc_info=True)
        return {
            "ok": False,
            "text": "",
            "provider": "groq",
            "model": settings.GROQ_STT_MODEL,
            "error": sanitize_groq_stt_error(str(exc)) or GROQ_STT_FRIENDLY_ERROR,
            "error_code": "UNKNOWN_ERROR",
        }
