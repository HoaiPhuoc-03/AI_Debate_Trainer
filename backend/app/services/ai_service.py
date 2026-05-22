import time

from app.core.config import settings
from app.services.cer_scorer import (
    DEFAULT_BREAKDOWN,
    INVALID_REBUTTAL,
    invalid_cer_result,
    parse_cer_rubric_output,
    validate_user_argument,
)
from app.services.groq_client import (
    GROQ_FRIENDLY_ERROR,
    call_groq as _call_groq,
    sanitize_error,
)
from app.services.output_parser import DEFAULT_CER
from app.services.prompt_builder import build_cer_messages
from app.services.prompt_builder import build_groq_messages  # noqa: F401


DEFAULT_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Không thể tạo phản hồi AI trong lượt này."],
    "suggestions": ["Vui lòng kiểm tra Groq API key, model hoặc kết nối mạng rồi thử lại."],
}

GROQ_FORMAT_ERROR = "Groq trả về nội dung chưa đúng định dạng. Vui lòng thử lại."


def _sanitize_error(message: str) -> str:
    return sanitize_error(message)


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


def build_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str | None = None,
    language: str = "vi",
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
) -> list[dict[str, str]]:
    # Use build_cer_messages() which returns a proper [system, user] pair.
    # GEPA design: the system prompt is written IN Vietnamese so the model's
    # output register is locked at identity level, not instruction level.
    # turn_history injects recent turns so the rebuttal evolves each turn.
    return build_cer_messages(
        topic=topic,
        stance=stance,
        difficulty=difficulty,
        user_argument=user_argument,
        age_group=age_group,
        debate_level=debate_level,
        input_mode=input_mode or "text",
        language=language,
        turn_history=turn_history,
        mode=mode,
    )


def call_groq(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 700,
    temperature: float = 0.35,
) -> dict:
    return _call_groq(
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )


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
        # New fields from the updated prompt — passed through for callers that
        # want to show the evidence gate result or the scoring checklist.
        "evidence_quote": rubric.get("evidence_quote", ""),
        "checklist": rubric.get("checklist", {}),
        "scoring_error": rubric.get("scoring_error", ""),
        "content_flags": [],
        "raw_text": rubric.get("raw_scoring_text", ""),
        "raw_scoring_text": rubric.get("raw_scoring_text", ""),
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
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
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
            turn_history=turn_history,
            mode=mode,
        )
        build_prompt_ms = int((time.perf_counter() - build_start) * 1000)

        llm_start = time.perf_counter()
        llm_result = call_groq(groq_messages, max_tokens=1400, temperature=0.65)
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

        # Only hard-error when the rubric itself is marked invalid or errored.
        # Do NOT gate on scoring_error alone — fallback_cer_result also sets it
        # to "parse_error", which previously caused every fallback to be thrown
        # away and replaced with a generic error response.
        if rubric.get("status") == "error" or (not rubric.get("is_valid") and rubric.get("status") != "invalid"):
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
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
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
        turn_history=turn_history,
        mode=mode,
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
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
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
        turn_history=turn_history,
        mode=mode,
    )
    return {
        "ok": analysis["ok"],
        "text": analysis["rebuttal"],
        "provider": analysis.get("provider", ""),
        "model": analysis.get("model", ""),
        "error": analysis["error"],
    }