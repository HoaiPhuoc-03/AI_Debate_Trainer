import re
import time

import httpx

from app.core.config import settings
from app.services.cer_scorer import (
    DEFAULT_BREAKDOWN,
    INVALID_REBUTTAL,
    invalid_cer_result,
    parse_cer_rubric_output,
    validate_user_argument,
)
from app.services.output_parser import DEFAULT_CER


DEFAULT_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Không thể tạo phản hồi AI trong lượt này."],
    "suggestions": ["Vui lòng kiểm tra Groq API key, model hoặc kết nối mạng rồi thử lại."],
}

GROQ_FRIENDLY_ERROR = "Groq API hiện không phản hồi. Vui lòng kiểm tra GROQ_API_KEY hoặc thử lại sau."
GROQ_FORMAT_ERROR = "Groq trả về nội dung chưa đúng định dạng. Vui lòng thử lại."


def _sanitize_error(message: str) -> str:
    sanitized = str(message or "")
    sanitized = re.sub(r"(key=)[^&\s']+", r"\1***", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1***", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"gsk_[A-Za-z0-9_\-]+", "gsk_***", sanitized)
    return sanitized


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


def _language_name(language: str) -> str:
    return "tiếng Việt" if language == "vi" else "English"


def build_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str | None = None,
    language: str = "vi",
) -> list[dict[str, str]]:
    output_language = _language_name(language or "vi")
    system_prompt = f"""
Bạn là AI Debate Trainer, một huấn luyện viên tranh biện bằng {output_language}.
Luôn phản biện lại lập luận của người dùng, không đồng ý hoàn toàn.
Chấm CER theo thang 100 gồm Claim, Evidence, Reasoning.
Trả đúng format, không thêm markdown code block.
""".strip()
    user_prompt = f"""
Chủ đề: {topic}
Lập trường người dùng: {stance}
Độ khó: {difficulty}
Nhóm tuổi: {age_group or "adult"}
Trình độ tranh biện: {debate_level or "intermediate"}
Cách nhập lập luận: {input_mode or "text"}
Ngôn ngữ trả lời: {output_language}

Lập luận người dùng:
{user_argument}

Format bắt buộc:
[REBUTTAL]
Viết 4-7 câu phản biện trực tiếp, có lý do rõ ràng.

[CER]
Claim: x/100
Evidence: y/100
Reasoning: z/100
Overall: t/100

[FEEDBACK]
Strengths:
- ...
- ...

Weaknesses:
- ...
- ...

Suggestions:
- ...
- ...

Yêu cầu giọng điệu:
- Nếu age_group=teen: giọng khích lệ, dễ hiểu.
- Nếu age_group=adult: rõ ràng, có cấu trúc.
- Nếu age_group=senior: dễ đọc, mạch lạc, ít thuật ngữ.
- Nếu debate_level=basic: giải thích đơn giản.
- Nếu debate_level=intermediate: phản biện có cấu trúc.
- Nếu debate_level=advanced: phản biện sâu hơn, chỉ ra giả định ẩn/ngoại lệ/lỗi logic.
- Nếu input_mode=voice: không trừ điểm nặng vì transcript nói tự nhiên hơi thiếu dấu.
""".strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


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
            "error": _sanitize_error(str(exc)),
        }


def _error_analysis(message: str, *, provider: str = "groq", model: str = "") -> dict:
    message = _sanitize_error(message)
    return {
        "ok": False,
        "is_valid": True,
        "status": "error",
        "rebuttal": message if message in {GROQ_FRIENDLY_ERROR, GROQ_FORMAT_ERROR} else GROQ_FRIENDLY_ERROR,
        "cer": DEFAULT_CER.copy(),
        "cer_breakdown": DEFAULT_BREAKDOWN.copy(),
        "feedback": DEFAULT_FEEDBACK.copy(),
        "raw_text": "",
        "raw_scoring_text": "",
        "provider": provider,
        "model": model,
        "content_flags": [
            {
                "type": "ai_error",
                "severity": "medium",
                "message": message,
            }
        ],
        "error": message,
    }


def _rubric_to_analysis(rubric: dict, *, provider: str = "groq", model: str = "", llm_error: str = "") -> dict:
    rebuttal = rubric.get("rebuttal") or ""
    if _needs_rebuttal_repair(rebuttal):
        return _error_analysis(GROQ_FORMAT_ERROR, provider=provider, model=model)

    return {
        "ok": bool(rebuttal and rubric["is_valid"] and rubric.get("status") != "error"),
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
        "provider": provider,
        "model": model,
        "error": llm_error,
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
            "provider": "",
            "model": "",
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
        build_start = time.perf_counter()
        groq_messages = build_messages(
            topic=topic,
            stance=stance,
            difficulty=difficulty,
            user_argument=user_argument,
            age_group=age_group or "adult",
            debate_level=debate_level or "intermediate",
            input_mode=input_mode or "text",
            language=language or "vi",
        )
        build_prompt_ms = int((time.perf_counter() - build_start) * 1000)

        llm_start = time.perf_counter()
        llm_result = call_groq(groq_messages, max_tokens=700, temperature=0.35)
        llm_ms = int((time.perf_counter() - llm_start) * 1000)
        if not llm_result["ok"]:
            return _error_analysis(
                llm_result["text"] or llm_result["error"],
                provider=llm_result.get("provider", "groq"),
                model=llm_result.get("model", ""),
            )

        parse_start = time.perf_counter()
        rubric = parse_cer_rubric_output(llm_result["text"])
        parse_output_ms = int((time.perf_counter() - parse_start) * 1000)
        if rubric.get("scoring_error"):
            return _error_analysis(
                GROQ_FORMAT_ERROR,
                provider=llm_result.get("provider", "groq"),
                model=llm_result.get("model", ""),
            )

        analysis = _rubric_to_analysis(
            rubric,
            provider=llm_result.get("provider", "groq"),
            model=llm_result.get("model", ""),
            llm_error=llm_result.get("error", ""),
        )
        analysis["timings"] = {
            "build_prompt_ms": build_prompt_ms,
            "llm_ms": llm_ms,
            "provider": analysis.get("provider", "groq"),
            "parse_output_ms": parse_output_ms,
            "total_ai_ms": build_prompt_ms + llm_ms + parse_output_ms,
        }
        return analysis

    except Exception as exc:
        return _error_analysis(_sanitize_error(str(exc)), provider="groq", model=settings.GROQ_MODEL)


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
        "provider": analysis.get("provider", ""),
        "model": analysis.get("model", ""),
        "error": analysis["error"],
    }
