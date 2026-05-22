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


def clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, score))


def extract_section(text: str, section_name: str) -> str:
    section = re.escape(section_name)
    pattern = rf"\[{section}\]\s*(.*?)(?=\n\s*\[[^\]]+\]|\Z)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_score(label: str, text: str) -> float:
    pattern = rf"{re.escape(label)}\s*:\s*(-?\d+(?:\.\d+)?)(?:\s*/\s*(\d+))?"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        val = float(match.group(1))
        denom = match.group(2)
        if denom == "10":
            return val * 10.0
        return clamp_score(val)
    return 0.0


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

    rebuttal = extract_section(raw_text, "PHẢN BIỆN LẠI") or extract_section(raw_text, "REBUTTAL")
    cer_text = extract_section(raw_text, "ĐIỂM SỐ") or extract_section(raw_text, "CER")
    
    feedback_analysis = extract_section(raw_text, "PHÂN TÍCH CER")
    feedback_suggestion = extract_section(raw_text, "GỢI Ý CẢI THIỆN")
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

    if feedback_analysis or feedback_suggestion:
        sentences = [s.strip() for s in re.split(r'[.!?]+', feedback_analysis) if s.strip()]
        strengths = [sentences[0] + "."] if len(sentences) > 0 else []
        weaknesses = [sentences[1] + "."] if len(sentences) > 1 else []
        suggestions = [feedback_suggestion.strip()] if feedback_suggestion.strip() else []
        feedback = {
            "strengths": strengths,
            "weaknesses": weaknesses or ["Cần làm rõ hơn bằng chứng và suy luận."],
            "suggestions": suggestions or ["Bổ sung ví dụ cụ thể và giải thích quan hệ nhân quả."],
        }
    else:
        feedback = _build_feedback(feedback_text)

    ok = bool(cer_text and (feedback_text or feedback_analysis or feedback_suggestion))
    return {
        "ok": ok,
        "rebuttal": rebuttal,
        "cer": cer,
        "feedback": feedback,
        "raw_text": raw_text,
    }