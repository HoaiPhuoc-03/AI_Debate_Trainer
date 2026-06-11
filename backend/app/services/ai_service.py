import json
import re
import time
import unicodedata
from difflib import SequenceMatcher

from app.core.config import settings
from app.data.topics import list_topics
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
from app.services.prompt_builder import (
    build_cer_messages,
    build_practice_prompt_messages,
    normalize_practice_mode,
    practice_instruction_for_mode,
    practice_prompt_type_for_mode,
)
from app.services.practice_prompt_service import _claim_from_topic


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
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
    practice_round: int | None = None,
    memory_context: dict | None = None,
    user_search_context: str = "",
    ai_search_context: str = "",
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
        practice_mode=practice_mode,
        practice_prompt=practice_prompt,
        practice_fallacy_hint=practice_fallacy_hint,
        practice_target_flaws=practice_target_flaws,
        practice_round=practice_round,
        memory_context=memory_context,
        user_search_context=user_search_context,
        ai_search_context=ai_search_context,
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


def _rubric_to_analysis(
    rubric: dict,
    *,
    provider: str = "groq",
    model: str = "",
    llm_error: str = "",
    mode: str | None = None,
) -> dict:
    rebuttal = rubric.get("rebuttal") or ""
    if normalize_practice_mode(mode) != "quick_rebuttal" and _needs_rebuttal_repair(rebuttal):
        return _error_analysis(GROQ_FORMAT_ERROR, provider=provider, model=model)

    return {
        "ok": bool(rebuttal and rubric["is_valid"] and rubric.get("status") != "error"),
        "is_valid": bool(rubric["is_valid"]),
        "status": rubric["status"],
        "rebuttal": rebuttal,
        "cer": rubric["cer"],
        "mode_scores": rubric.get("mode_scores"),
        "cer_breakdown": rubric["cer_breakdown"],
        "feedback": rubric["feedback"],
        # New fields from the updated prompt — passed through for callers that
        # want to show the evidence gate result or the scoring checklist.
        "evidence_quote": rubric.get("evidence_quote", ""),
        "checklist": rubric.get("checklist", {}),
        "scoring_error": rubric.get("scoring_error", ""),
        # Mode-specific fields: fact-checking, source links, and source suggestions.
        "fact_check": rubric.get("fact_check", []),
        "evidence_source_links": rubric.get("evidence_source_links", []),
        "better_source_suggestions": rubric.get("better_source_suggestions", []),
        "content_flags": [],
        "raw_text": rubric.get("raw_scoring_text", ""),
        "raw_scoring_text": rubric.get("raw_scoring_text", ""),
        "model_claim": rubric.get("model_claim"),
        "provider": provider,
        "model": model,
        "error": llm_error,
    }


def _text_key(value: str | None) -> str:
    text = unicodedata.normalize("NFD", str(value or "").strip().casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^\w]+", " ", text)
    return " ".join(text.split())


def _history_items(items: list[str] | None) -> list[str]:
    return [str(item).strip() for item in (items or []) if str(item or "").strip()]


def _too_similar(value: str, previous_values: list[str] | None) -> bool:
    key = _text_key(value)
    if not key:
        return False
    for previous in _history_items(previous_values):
        previous_key = _text_key(previous)
        if not previous_key:
            continue
        if key == previous_key or key in previous_key or previous_key in key:
            return True
        if SequenceMatcher(None, key, previous_key).ratio() >= 0.82:
            return True
    return False


def _choose_fallback_topic(topic: str, difficulty: str | None, round: int, previous_topics: list[str] | None) -> dict:
    avoided = {_text_key(item) for item in _history_items(previous_topics)}
    if topic:
        avoided.add(_text_key(topic))

    preferred = list_topics(difficulty=difficulty) if difficulty else []
    candidates = preferred or list_topics()
    filtered = [
        item for item in candidates
        if _text_key(item.get("title")) not in avoided and _text_key(item.get("id")) not in avoided
    ]
    if not filtered and preferred:
        filtered = [
            item for item in list_topics()
            if _text_key(item.get("title")) not in avoided and _text_key(item.get("id")) not in avoided
        ]
    if not filtered:
        filtered = candidates or list_topics()
    if not filtered:
        return {"title": topic or "Một chủ đề xã hội mới", "description": ""}
    index = max(int(round or 1), 1) - 1
    return filtered[index % len(filtered)]


def _prompt_conflicts_with_history(prompt: str, prompt_topic: str, previous_prompts: list[str] | None, previous_topics: list[str] | None) -> bool:
    if _too_similar(prompt, previous_prompts):
        return True
    if _too_similar(prompt_topic, previous_topics):
        return True
    if prompt_topic and _too_similar(prompt, previous_topics):
        return True
    return False


def _fallback_practice_prompt(
    mode: str,
    topic: str,
    difficulty: str | None = None,
    round: int = 1,
    previous_topics: list[str] | None = None,
    warning: str = "Không tạo được đề bài mới từ AI, đang dùng đề bài mẫu.",
) -> dict:
    normalized = normalize_practice_mode(mode)
    prompt_type = practice_prompt_type_for_mode(normalized)
    fallback_topic = _choose_fallback_topic(topic, difficulty, round, previous_topics)
    title = str(fallback_topic.get("title") or topic or "Một chủ đề xã hội mới").strip()
    description = str(fallback_topic.get("description") or "").strip()
    scenario = description or f"Hãy xem xét một tình huống cụ thể liên quan đến: {title}."
    claim = ""
    weak_argument = ""
    fallacy_hint = ""
    if normalized == "find_evidence":
        claim = _claim_from_topic(title, topic_id=fallback_topic.get("id"))
        prompt = claim
    elif normalized == "quick_rebuttal":
        weak_argument = f"{title} chắc chắn đúng vì nhiều người hiện nay đều đồng ý và làm theo."
        fallacy_hint = "dựa vào số đông / thiếu bằng chứng"
        prompt = weak_argument
    else:
        prompt = f"Tình huống: {title}. {scenario}"
    return {
        "status": "success",
        "mode": normalized,
        "prompt_type": prompt_type,
        "topic": title,
        "scenario": scenario if normalized == "claim_writing" else None,
        "claim": claim if normalized == "find_evidence" else None,
        "weak_argument": weak_argument if normalized == "quick_rebuttal" else None,
        "fallacy_hint": fallacy_hint if normalized == "quick_rebuttal" else None,
        "prompt": prompt,
        "instruction": practice_instruction_for_mode(normalized),
        "warning": warning,
        "suggested_angles": [],
    }


def _extract_json_object(text: str) -> dict:
    clean = (text or "").strip()
    if not clean:
        raise ValueError("empty practice prompt response")
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def generate_practice_prompt(
    mode: str,
    topic: str,
    difficulty: str | None = None,
    round: int = 1,
    language: str = "vi",
    previous_prompts: list[str] | None = None,
    previous_topics: list[str] | None = None,
    avoid_repeating: bool = True,
) -> dict:
    normalized = normalize_practice_mode(mode)
    if normalized not in {"claim_writing", "find_evidence", "quick_rebuttal"}:
        return _fallback_practice_prompt(normalized, topic, difficulty, round, previous_topics)

    try:
        attempts = 3 if avoid_repeating else 1
        rejected_prompts: list[str] = []
        for _ in range(attempts):
            selected_topic = topic
            if round > 1:
                fallback_topic = _choose_fallback_topic(topic, difficulty, round, previous_topics)
                selected_topic = fallback_topic.get("title") or topic

            messages = build_practice_prompt_messages(
                mode=normalized,
                topic=selected_topic,
                difficulty=difficulty or "Trung bình",
                round=round,
                language=language,
                previous_prompts=[*_history_items(previous_prompts), *rejected_prompts],
                previous_topics=previous_topics,
                avoid_repeating=avoid_repeating,
            )
            llm_result = call_groq(messages, max_tokens=520, temperature=0.85)
            if not llm_result["ok"]:
                continue
            parsed = _extract_json_object(llm_result["text"])
            prompt = str(parsed.get("prompt") or parsed.get("scenario") or parsed.get("claim") or parsed.get("weak_argument") or "").strip()
            prompt_topic = str(parsed.get("topic") or parsed.get("scenario") or parsed.get("claim") or parsed.get("weak_argument") or "").strip()
            if not prompt:
                continue
            if avoid_repeating and _prompt_conflicts_with_history(prompt, prompt_topic, previous_prompts, previous_topics):
                rejected_prompts.append(prompt)
                continue
            parsed_mode = normalize_practice_mode(parsed.get("mode") or normalized)
            return {
                "status": "success",
                "mode": parsed_mode,
                "prompt_type": parsed.get("prompt_type") or practice_prompt_type_for_mode(normalized),
                "topic": prompt_topic or None,
                "scenario": str(parsed.get("scenario") or "").strip() or None,
                "claim": str(parsed.get("claim") or "").strip() or None,
                "weak_argument": str(parsed.get("weak_argument") or "").strip() or None,
                "prompt": prompt,
                "instruction": str(parsed.get("instruction") or practice_instruction_for_mode(normalized)).strip(),
                "warning": None,
                "suggested_angles": parsed.get("suggested_angles") or [],
            }
        return _fallback_practice_prompt(
            normalized,
            topic,
            difficulty,
            round,
            previous_topics,
            warning="AI tạo đề bị trùng hoặc chưa hợp lệ, Lumi đã đổi sang đề mẫu khác.",
        )
    except Exception:
        return _fallback_practice_prompt(normalized, topic, difficulty, round, previous_topics)


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
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
    practice_round: int | None = None,
    memory_context: dict | None = None,
) -> dict:
    active_mode = normalize_practice_mode(practice_mode or mode)
    validation = validate_user_argument(topic, user_argument)
    if not validation["is_valid"]:
        invalid = invalid_cer_result(validation["reason"], mode=active_mode)
        return {
            "ok": False,
            "is_valid": False,
            "status": "invalid",
            "rebuttal": INVALID_REBUTTAL,
            "cer": invalid["cer"],
            "mode_scores": invalid.get("mode_scores"),
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
        user_search_context, ai_search_context = "", ""
        active_mode = normalize_practice_mode(practice_mode or mode)
        if active_mode in ("free_debate", "find_evidence", "full_argument"):
            try:
                from app.services.search_service import get_combined_search_context
                user_search_context, ai_search_context = get_combined_search_context(user_argument, topic, stance)
            except Exception:
                pass

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
            practice_mode=practice_mode,
            practice_prompt=practice_prompt,
            practice_fallacy_hint=practice_fallacy_hint,
            practice_target_flaws=practice_target_flaws,
            practice_round=practice_round,
            memory_context=memory_context,
            user_search_context=user_search_context,
            ai_search_context=ai_search_context,
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
        rubric = parse_cer_rubric_output(llm_result["text"], mode=active_mode)
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
            mode=active_mode,
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
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
    practice_round: int | None = None,
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
        practice_mode=practice_mode,
        practice_prompt=practice_prompt,
        practice_fallacy_hint=practice_fallacy_hint,
        practice_target_flaws=practice_target_flaws,
        practice_round=practice_round,
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
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_round: int | None = None,
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
        practice_mode=practice_mode,
        practice_prompt=practice_prompt,
        practice_round=practice_round,
    )
    return {
        "ok": analysis["ok"],
        "text": analysis["rebuttal"],
        "provider": analysis.get("provider", ""),
        "model": analysis.get("model", ""),
        "error": analysis["error"],
    }
