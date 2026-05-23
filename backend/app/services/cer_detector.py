import re
from typing import Any


MISSING_FEEDBACK = {
    "claim": "Bạn chưa nêu một lập trường hoặc kết luận rõ ràng.",
    "evidence": "Bạn chưa đưa ra dẫn chứng, ví dụ, số liệu hoặc nguồn cụ thể.",
    "reasoning": "Bạn chưa giải thích vì sao dẫn chứng hoặc ý chính dẫn tới kết luận.",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().casefold())


def _has_pattern(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.UNICODE) for pattern in patterns)


def detect_cer_components(user_input: str) -> dict[str, Any]:
    """Detect whether the user's text explicitly contains C, E, and R.

    This detector is intentionally strict. It does not infer missing CER parts
    from context or from what a generous judge might assume the user meant.
    """
    text = _normalize_text(user_input)
    word_count = len(re.findall(r"\w+", text, flags=re.UNICODE))

    claim_patterns = [
        r"\b(tôi nghĩ|tôi cho rằng|theo tôi|quan điểm của tôi|tôi tin|mình nghĩ)\b",
        r"\b(nên|không nên|cần|phải|không được|nên được|cần phải)\b.+",
        r"\b(là đúng|là sai|có hại|có lợi|tốt hơn|xấu hơn|quan trọng|cần thiết)\b",
    ]
    evidence_patterns = [
        r"\b(ví dụ|chẳng hạn|chẳng hạn như|cụ thể là|trường hợp|tình huống)\b",
        r"\b(theo|nghiên cứu|khảo sát|báo cáo|thống kê|dữ liệu|số liệu|nguồn)\b",
        r"\b\d+(?:[,.]\d+)?\s*(%|phần trăm|triệu|nghìn|ngàn|năm|người|học sinh|sinh viên)\b",
        r"\b(năm|tháng)\s+\d{4}\b",
    ]
    reasoning_patterns = [
        r"\b(vì|bởi vì|do|do đó|vì vậy|cho nên|khiến|làm cho|dẫn đến|dẫn tới)\b",
        r"\b(nguyên nhân là|hệ quả là|kết quả là|điều này cho thấy|điều này dẫn tới)\b",
        r"\bnếu\b.+\b(thì|sẽ)\b",
    ]

    has_claim = word_count >= 4 and _has_pattern(claim_patterns, text)
    has_evidence = word_count >= 5 and _has_pattern(evidence_patterns, text)

    has_reasoning = word_count >= 6 and _has_pattern(reasoning_patterns, text)
    if re.search(r"\b(vì|bởi vì|do đó|vì vậy|cho nên|khiến|làm cho|dẫn đến|dẫn tới)\b", text):
        has_reasoning = word_count >= 6

    return {
        "has_claim": bool(has_claim),
        "has_evidence": bool(has_evidence),
        "has_reasoning": bool(has_reasoning),
        "components": {
            "claim": {
                "exists": bool(has_claim),
                "feedback": "" if has_claim else MISSING_FEEDBACK["claim"],
            },
            "evidence": {
                "exists": bool(has_evidence),
                "feedback": "" if has_evidence else MISSING_FEEDBACK["evidence"],
            },
            "reasoning": {
                "exists": bool(has_reasoning),
                "feedback": "" if has_reasoning else MISSING_FEEDBACK["reasoning"],
            },
        },
    }


def component_exists(component_detection: dict[str, Any] | None, component: str) -> bool:
    if not component_detection:
        return True
    if f"has_{component}" in component_detection:
        return bool(component_detection[f"has_{component}"])
    component_info = (component_detection.get("components") or {}).get(component) or {}
    return bool(component_info.get("exists", True))
