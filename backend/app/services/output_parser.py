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


def parse_debate_output(raw_text: str) -> dict:
    raw_text = raw_text or ""
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

    rebuttal = extract_section(raw_text, "REBUTTAL")
    cer_text = extract_section(raw_text, "CER")
    feedback_text = extract_section(raw_text, "FEEDBACK")

    if not rebuttal:
        return {
            "ok": False,
            "rebuttal": _short_text(raw_text),
            "cer": DEFAULT_CER.copy(),
            "feedback": DEFAULT_FEEDBACK.copy(),
            "raw_text": raw_text,
        }

    cer = _build_cer(cer_text) if cer_text else DEFAULT_CER.copy()
    feedback = _build_feedback(feedback_text)

    ok = bool(cer_text and feedback_text)
    return {
        "ok": ok,
        "rebuttal": rebuttal,
        "cer": cer,
        "feedback": feedback,
        "raw_text": raw_text,
    }
