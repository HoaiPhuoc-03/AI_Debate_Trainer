import re

import httpx

from app.core.config import settings
from app.services.cer_scorer import (
    INVALID_REBUTTAL,
    fallback_cer_result,
    invalid_cer_result,
    parse_cer_rubric_output,
    validate_user_argument,
)
from app.services.output_parser import DEFAULT_CER
from app.services.prompt_builder import build_cer_rubric_prompt


DEFAULT_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Không thể tạo phản hồi AI trong lượt này."],
    "suggestions": ["Hãy thử lại sau hoặc chuyển sang chế độ demo."],
}

TIMEOUT_REBUTTAL = "AI phản hồi quá lâu hoặc không trả về phản biện hợp lệ. Vui lòng thử lại."


def _sanitize_error(message: str) -> str:
    return re.sub(r"(key=)[^&\s']+", r"\1***", str(message or ""))


def _shorten_text(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _needs_rebuttal_repair(text: str) -> bool:
    cleaned = (text or "").strip()
    lowered = cleaned.casefold()
    weak_markers = [
        "<rebuttal>",
        "ai chưa tạo",
        "chưa tạo được phản biện",
        "không phản hồi",
    ]
    coaching_markers = [
        "lập luận của bạn có thể",
        "lập luận của bạn chưa",
        "thuyết phục hơn nếu",
        "cần cung cấp",
        "hãy bổ sung",
        "bạn nên bổ sung",
        "thiếu bằng chứng",
        "chưa rõ ràng",
    ]
    looks_like_feedback = len(cleaned) < 280 and any(marker in lowered for marker in coaching_markers)
    return len(cleaned) < 80 or any(marker in lowered for marker in weak_markers) or looks_like_feedback


def _post_ollama(prompt: str, *, num_predict: int = 420, temperature: float = 0.35) -> str:
    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "num_predict": num_predict,
                "temperature": temperature,
                "top_p": 0.9,
                "num_ctx": 1536,
            },
        },
        timeout=settings.OLLAMA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return extract_text_from_ollama(response.json())


def extract_text_from_ollama(data: dict) -> str:
    # /api/chat -> message.content
    message = data.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    # /api/generate -> response
    response_text = data.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()

    return ""


def _error_analysis(message: str) -> dict:
    message = _sanitize_error(message)
    return {
        "ok": False,
        "rebuttal": "AI hiện không phản hồi. Vui lòng thử lại sau.",
        "cer": DEFAULT_CER.copy(),
        "feedback": DEFAULT_FEEDBACK.copy(),
        "raw_text": "",
        "content_flags": [
            {
                "type": "ai_error",
                "severity": "medium",
                "message": message,
            }
        ],
        "error": message,
    }


def generate_debate_analysis(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    input_mode: str | None = None,
) -> dict:
    validation = validate_user_argument(topic, user_argument)
    if not validation["is_valid"]:
        invalid = invalid_cer_result(validation["reason"])
        return {
            "ok": False,
            "is_valid": False,
            "status": "invalid",
            "rebuttal": INVALID_REBUTTAL,
            "cer": invalid["cer"],
            "cer_breakdown": invalid["cer_breakdown"],
            "feedback": invalid["feedback"],
            "raw_text": "",
            "raw_scoring_text": "",
            "content_flags": [
                {
                    "type": "invalid_argument",
                    "severity": "low",
                    "message": validation["reason"],
                }
            ],
            "error": "",
        }

    try:
        scoring_prompt = build_cer_rubric_prompt(
            topic=topic,
            stance=stance,
            difficulty=difficulty,
            user_argument=user_argument,
            age_group=age_group or "adult",
            debate_level=debate_level or "intermediate",
            input_mode=input_mode or "text",
            coach_model=coach_model or "socratic_v3",
            language=language or "vi",
        )
        try:
            raw_scoring_text = _post_ollama(scoring_prompt, num_predict=600, temperature=0.2)
            rubric = parse_cer_rubric_output(raw_scoring_text)
        except Exception as scoring_exc:
            rubric = fallback_cer_result(_sanitize_error(str(scoring_exc)))
            rubric["rebuttal"] = TIMEOUT_REBUTTAL

        rebuttal = rubric.get("rebuttal") or ""
        if _needs_rebuttal_repair(rebuttal):
            rebuttal = TIMEOUT_REBUTTAL
            rubric["status"] = "error"

        return {
            "ok": bool(rebuttal and rubric["is_valid"]),
            "is_valid": bool(rubric["is_valid"]),
            "status": rubric["status"],
            "rebuttal": rebuttal,
            "cer": rubric["cer"],
            "cer_breakdown": rubric["cer_breakdown"],
            "feedback": rubric["feedback"],
            "content_flags": [],
            "raw_text": rubric.get("raw_scoring_text", ""),
            "raw_scoring_text": rubric.get("raw_scoring_text", ""),
            "scoring_error": rubric.get("scoring_error", ""),
            "error": "",
        }

    except Exception as exc:
        return _error_analysis(_sanitize_error(str(exc)))


def generate_debate_turn_analysis(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    input_mode: str | None = None,
) -> dict:
    return generate_debate_analysis(
        topic=topic,
        stance=stance,
        difficulty=difficulty,
        user_argument=user_argument,
        age_group=age_group,
        debate_level=debate_level,
        coach_model=coach_model,
        language=language,
        input_mode=input_mode,
    )


def generate_rebuttal(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    input_mode: str | None = None,
) -> dict:
    analysis = generate_debate_analysis(
        topic=topic,
        stance=stance,
        difficulty=difficulty,
        user_argument=user_argument,
        age_group=age_group,
        debate_level=debate_level,
        coach_model=coach_model,
        language=language,
        input_mode=input_mode,
    )
    return {
        "ok": analysis["ok"],
        "text": analysis["rebuttal"],
        "error": analysis["error"],
    }
