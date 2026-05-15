import re

import httpx

from app.core.config import settings


GROQ_FRIENDLY_ERROR = "Groq API hiện không phản hồi. Vui lòng kiểm tra GROQ_API_KEY hoặc thử lại sau."


def sanitize_error(message: str) -> str:
    sanitized = str(message or "")
    sanitized = re.sub(r"(key=)[^&\s']+", r"\1***", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1***", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"gsk_[A-Za-z0-9_\-]+", "gsk_***", sanitized)
    return sanitized


def call_groq(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 700,
    temperature: float = 0.35,
) -> dict:
    if not settings.GROQ_API_KEY.strip():
        return {
            "ok": False,
            "text": GROQ_FRIENDLY_ERROR,
            "provider": "groq",
            "model": settings.GROQ_MODEL,
            "error": "GROQ_API_KEY is missing.",
        }

    try:
        response = httpx.post(
            settings.GROQ_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "top_p": 0.9,
                "max_tokens": max_tokens,
            },
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Groq response did not contain choices[0].message.content")
        return {
            "ok": True,
            "text": text.strip(),
            "provider": "groq",
            "model": settings.GROQ_MODEL,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "text": GROQ_FRIENDLY_ERROR,
            "provider": "groq",
            "model": settings.GROQ_MODEL,
            "error": sanitize_error(str(exc)),
        }
