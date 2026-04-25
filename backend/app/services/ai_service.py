import httpx

from app.core.config import settings
from app.services.output_parser import DEFAULT_CER, parse_debate_output
from app.services.prompt_builder import build_debate_prompt


DEFAULT_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Không thể tạo phản hồi AI trong lượt này."],
    "suggestions": ["Hãy thử lại sau hoặc chuyển sang chế độ demo."],
}


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
    language: str = "vi",
    input_mode: str | None = None,
) -> dict:
    prompt = build_debate_prompt(
        topic=topic,
        stance=stance,
        difficulty=difficulty,
        user_argument=user_argument,
        age_group=age_group or "adult",
        debate_level=debate_level or "intermediate",
        language=language or "vi",
    )

    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "options": {
                    "num_predict": 420,
                    "temperature": 0.35,
                },
            },
            timeout=180.0,
        )

        response.raise_for_status()
        raw_text = extract_text_from_ollama(response.json())
        parsed = parse_debate_output(raw_text)
        return {
            **parsed,
            "content_flags": [],
            "error": "",
        }

    except Exception as exc:
        return _error_analysis(str(exc))


def generate_debate_turn_analysis(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
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
        language=language,
        input_mode=input_mode,
    )
    return {
        "ok": analysis["ok"],
        "text": analysis["rebuttal"],
        "error": analysis["error"],
    }
