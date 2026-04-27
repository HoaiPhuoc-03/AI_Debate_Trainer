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
    "weaknesses": ["AI output was missing structured feedback."],
    "suggestions": ["Try again with a clearer argument or regenerate the response."],
}


def clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(10.0, score))


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
    return {
        "claim": claim,
        "evidence": evidence,
        "reasoning": reasoning,
        "overall": round((claim + evidence + reasoning) / 3, 2),
        "total": round((claim + evidence + reasoning) / 3, 2),
    }


def _build_feedback(feedback_text: str) -> dict:
    if not feedback_text:
        return {
            "strengths": [],
            "weaknesses": ["AI output was missing feedback."],
            "suggestions": ["Ask the AI to regenerate the response in the required format."],
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
                "weaknesses": ["AI output was empty."],
                "suggestions": ["Please try again after the AI service is ready."],
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
