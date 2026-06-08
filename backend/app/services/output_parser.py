import json
import re


DEFAULT_CER = {
    "claim": 0.0,
    "evidence": 0.0,
    "reasoning": 0.0,
    "overall": 0.0,
    "total": 0.0,
}
DEFAULT_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Phản hồi AI chưa có cấu trúc đầy đủ."],
    "suggestions": ["Hãy thử lại với lập luận rõ ràng hơn hoặc tạo lại phản hồi."],
}
DEFAULT_MODE_SCORES = {
    "flaw_detection": 0.0,
    "counter_example": 0.0,
    "explanation": 0.0,
    "focus": 0.0,
    "overall": 0.0,
}
QUICK_REBUTTAL_FALLBACK_FEEDBACK = {
    "strengths": ["Bạn đã có nỗ lực phản biện lại luận điểm yếu."],
    "weaknesses": ["Cần chỉ rõ lỗi chính trong luận điểm yếu và giải thích vì sao lỗi đó làm lập luận kém thuyết phục."],
    "suggestions": ["Hãy gọi tên lỗi/ngụy biện, trích cụm yếu trong luận điểm và thêm một phản ví dụ ngắn."],
}


def clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, score))


def extract_section(text: str, section_name: str) -> str:
    section = re.escape(section_name)
    pattern = rf"\[{section}\]\s*(.*?)(?=\n\[[A-Z_]+\]\s*|\Z)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_score(label: str, text: str) -> float:
    pattern = rf"{re.escape(label)}\s*:\s*(-?\d+(?:\.\d+)?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return clamp_score(match.group(1)) if match else 0.0


def parse_bullets(section_text: str) -> list[str]:
    items = []
    for line in section_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        clean = re.sub(r"^[-*•]\s*", "", clean).strip()
        if clean:
            items.append(clean)
    return items[:3]


def _feedback_subsection(feedback_text: str, label: str) -> str:
    labels = "Strengths|Weaknesses|Suggestions"
    pattern = rf"{re.escape(label)}\s*:\s*(.*?)(?=\n(?:{labels})\s*:|\Z)"
    match = re.search(pattern, feedback_text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _build_cer(cer_text: str) -> dict:
    claim = parse_score("Claim", cer_text)
    evidence = parse_score("Evidence", cer_text)
    reasoning = parse_score("Reasoning", cer_text)
    # Use the same weighted formula as cer_scorer: claim*0.3 + evidence*0.3 + reasoning*0.4
    overall = round(claim * 0.3 + evidence * 0.3 + reasoning * 0.4, 1)
    return {
        "claim": claim,
        "evidence": evidence,
        "reasoning": reasoning,
        "overall": overall,
        "total": overall,
    }


def _is_quick_rebuttal_mode(mode: str | None) -> bool:
    key = str(mode or "").strip().casefold().replace("-", "_").replace(" ", "_")
    return key in {"quick_rebuttal", "rebuttal", "phan_bien_nhanh"}


def _quick_rebuttal_mode_scores_from_cer(cer: dict) -> dict:
    return {
        "flaw_detection": clamp_score(cer.get("claim")),
        "counter_example": clamp_score(cer.get("evidence")),
        "explanation": clamp_score(cer.get("reasoning")),
        "focus": clamp_score(cer.get("overall") or cer.get("total")),
        "overall": clamp_score(cer.get("overall") or cer.get("total")),
    }


def _quick_rebuttal_overall(
    flaw_detection: float,
    counter_example: float,
    explanation: float,
    focus: float,
) -> float:
    return round(
        flaw_detection * 0.40
        + explanation * 0.25
        + counter_example * 0.20
        + focus * 0.15,
        1,
    )


def _quick_rebuttal_mode_scores_from_payload(payload: dict) -> dict:
    payload = payload or {}
    raw_scores = payload.get("mode_scores") or {}
    raw_cer = payload.get("cer") or {}

    flaw = clamp_score(raw_scores.get("flaw_detection"))
    counter = clamp_score(raw_scores.get("counter_example"))
    explanation = clamp_score(raw_scores.get("explanation"))
    focus = clamp_score(raw_scores.get("focus"))

    if not raw_scores or raw_scores.get("flaw_detection") is None:
        flaw = clamp_score(raw_cer.get("claim"))
    if not raw_scores or raw_scores.get("counter_example") is None:
        counter = clamp_score(raw_cer.get("evidence"))
    if not raw_scores or raw_scores.get("explanation") is None:
        explanation = clamp_score(raw_cer.get("reasoning"))
    if not raw_scores or raw_scores.get("focus") is None:
        focus = clamp_score(raw_cer.get("focus", raw_cer.get("overall") or raw_cer.get("total")))

    raw_overall = raw_scores.get("overall")
    if raw_overall is not None:
        overall = clamp_score(raw_overall)
    elif not raw_scores and (raw_cer.get("overall") is not None or raw_cer.get("total") is not None):
        overall = clamp_score(raw_cer.get("overall", raw_cer.get("total")))
    else:
        overall = _quick_rebuttal_overall(flaw, counter, explanation, focus)

    return {
        "flaw_detection": flaw,
        "counter_example": counter,
        "explanation": explanation,
        "focus": focus,
        "overall": overall,
    }


def _quick_rebuttal_compat_cer(mode_scores: dict) -> dict:
    # Quick Rebuttal compatibility mapping:
    # claim = flaw_detection
    # evidence = counter_example
    # reasoning = explanation
    # This is not normal CER scoring.
    overall = clamp_score(mode_scores.get("overall"))
    return {
        "claim": clamp_score(mode_scores.get("flaw_detection")),
        "evidence": clamp_score(mode_scores.get("counter_example")),
        "reasoning": clamp_score(mode_scores.get("explanation")),
        "overall": overall,
        "total": overall,
    }


def _coerce_feedback_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:3]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _strip_json_code_block(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _quick_rebuttal_feedback(payload: dict) -> dict:
    raw_feedback = payload.get("feedback") or {}
    feedback = {
        "strengths": _coerce_feedback_list(payload.get("strengths", raw_feedback.get("strengths"))),
        "weaknesses": _coerce_feedback_list(payload.get("weaknesses", raw_feedback.get("weaknesses"))),
        "suggestions": _coerce_feedback_list(payload.get("suggestions", raw_feedback.get("suggestions"))),
    }
    if not any(feedback.values()):
        return {key: list(value) for key, value in QUICK_REBUTTAL_FALLBACK_FEEDBACK.items()}
    return feedback


def _quick_rebuttal_json_result(raw_text: str, payload: dict) -> dict:
    mode_scores = _quick_rebuttal_mode_scores_from_payload(payload)
    rebuttal = str(payload.get("ai_rebuttal") or payload.get("rebuttal") or "").strip()
    return {
        "ok": bool(rebuttal),
        "rebuttal": rebuttal or "Lumi chưa tạo được nhận xét quick rebuttal.",
        "cer": _quick_rebuttal_compat_cer(mode_scores),
        "mode_scores": mode_scores,
        "feedback": _quick_rebuttal_feedback(payload),
        "raw_text": raw_text,
    }


def _build_feedback(feedback_text: str) -> dict:
    if not feedback_text:
        return {
            "strengths": [],
            "weaknesses": ["AI chưa tạo được phản hồi chi tiết."],
            "suggestions": ["Vui lòng yêu cầu AI tạo lại phản hồi theo đúng định dạng."],
        }
    return {
        "strengths": parse_bullets(_feedback_subsection(feedback_text, "Strengths")),
        "weaknesses": parse_bullets(_feedback_subsection(feedback_text, "Weaknesses")),
        "suggestions": parse_bullets(_feedback_subsection(feedback_text, "Suggestions")),
    }


def _short_text(text: str, limit: int = 500) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def parse_debate_output(raw_text: str, mode: str | None = None) -> dict:
    raw_text = raw_text or ""
    quick_rebuttal = _is_quick_rebuttal_mode(mode)
    if quick_rebuttal and not raw_text.strip():
        return {
            "ok": False,
            "rebuttal": "AI không trả về nội dung hợp lệ.",
            "cer": _quick_rebuttal_compat_cer(DEFAULT_MODE_SCORES),
            "mode_scores": DEFAULT_MODE_SCORES.copy(),
            "feedback": {key: list(value) for key, value in QUICK_REBUTTAL_FALLBACK_FEEDBACK.items()},
            "raw_text": raw_text,
        }
    if not raw_text.strip():
        return {
            "ok": False,
            "rebuttal": "AI không trả về nội dung hợp lệ.",
            "cer": DEFAULT_CER.copy(),
            "feedback": {
                "strengths": [],
                "weaknesses": ["Phản hồi AI trống rỗng."],
                "suggestions": ["Vui lòng thử lại sau khi dịch vụ AI sẵn sàng."],
            },
            "raw_text": raw_text,
        }

    if quick_rebuttal:
        try:
            payload = json.loads(_strip_json_code_block(raw_text))
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            return _quick_rebuttal_json_result(raw_text, payload)

    rebuttal = extract_section(raw_text, "REBUTTAL")
    cer_text = extract_section(raw_text, "CER")
    feedback_text = extract_section(raw_text, "FEEDBACK")

    if quick_rebuttal and not rebuttal:
        return {
            "ok": False,
            "rebuttal": _short_text(raw_text),
            "cer": _quick_rebuttal_compat_cer(DEFAULT_MODE_SCORES),
            "mode_scores": DEFAULT_MODE_SCORES.copy(),
            "feedback": {key: list(value) for key, value in QUICK_REBUTTAL_FALLBACK_FEEDBACK.items()},
            "raw_text": raw_text,
        }

    if not rebuttal:
        return {
            "ok": False,
            "rebuttal": _short_text(raw_text),
            "cer": DEFAULT_CER.copy(),
            "feedback": DEFAULT_FEEDBACK.copy(),
            "raw_text": raw_text,
        }

    cer = _build_cer(cer_text) if cer_text else DEFAULT_CER.copy()
    mode_scores = None
    if quick_rebuttal:
        mode_scores = _quick_rebuttal_mode_scores_from_cer(cer)
        cer = _quick_rebuttal_compat_cer(mode_scores)
    feedback = _build_feedback(feedback_text)

    ok = bool(cer_text and feedback_text)
    if quick_rebuttal:
        return {
            "ok": ok,
            "rebuttal": rebuttal,
            "cer": cer,
            "mode_scores": mode_scores,
            "feedback": feedback,
            "raw_text": raw_text,
        }
    return {
        "ok": ok,
        "rebuttal": rebuttal,
        "cer": cer,
        "feedback": feedback,
        "raw_text": raw_text,
    }
