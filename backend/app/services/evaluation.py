from __future__ import annotations

import re
from typing import Any


PASS_THRESHOLD = 6
MAX_SCORE = 7
SCORE_TOLERANCE = 0.01

REBUTTAL_KEYWORDS = {
    "nhưng",
    "tuy nhiên",
    "mặt khác",
    "không hẳn",
    "điểm yếu",
    "có thể phản biện",
    "trường hợp ngoại lệ",
    "hạn chế",
    "vấn đề",
}

WEAKNESS_KEYWORDS = {
    "claim": {"quan điểm", "luận điểm", "lập trường", "khẳng định", "ý chính"},
    "evidence": {"bằng chứng", "ví dụ", "số liệu", "dẫn chứng", "minh chứng"},
    "reasoning": {"logic", "suy luận", "nhân quả", "kết luận", "lập luận", "liên kết"},
}

VIETNAMESE_COMMON_WORDS = {
    "và",
    "là",
    "của",
    "có",
    "không",
    "nên",
    "nhưng",
    "tuy",
    "nhiên",
    "lập",
    "luận",
    "bằng",
    "chứng",
}


def count_words_vi(text: str) -> int:
    return len(re.findall(r"[0-9A-Za-zÀ-ỹ]+", text or ""))


def is_valid_score(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return 0 <= float(value) <= 10


def total_is_correct(cer: dict) -> bool:
    if not all(is_valid_score(cer.get(key)) for key in ("claim", "evidence", "reasoning", "total")):
        return False
    expected = round((float(cer["claim"]) + float(cer["evidence"]) + float(cer["reasoning"])) / 3, 2)
    return abs(float(cer["total"]) - expected) <= SCORE_TOLERANCE


def detect_main_weakness(cer: dict) -> str:
    scores = {
        "claim": float(cer.get("claim", 0)),
        "evidence": float(cer.get("evidence", 0)),
        "reasoning": float(cer.get("reasoning", 0)),
    }
    return min(scores, key=scores.get)


def _flatten_feedback(feedback: dict) -> str:
    chunks: list[str] = []
    for key in ("strengths", "weaknesses", "suggestions"):
        value = feedback.get(key, [])
        if isinstance(value, list):
            chunks.extend(str(item) for item in value)
        elif value:
            chunks.append(str(value))
    return " ".join(chunks).lower()


def feedback_mentions_weakness(feedback: dict, weakness: str) -> bool:
    text = _flatten_feedback(feedback)
    return any(keyword in text for keyword in WEAKNESS_KEYWORDS.get(weakness, set()))


def looks_like_rebuttal(text: str) -> bool:
    clean = " ".join((text or "").split()).lower()
    if count_words_vi(clean) < 8:
        return False
    return any(keyword in clean for keyword in REBUTTAL_KEYWORDS)


def looks_vietnamese(text: str) -> bool:
    clean = (text or "").lower()
    if not clean.strip():
        return False

    cjk_or_cyrillic = re.findall(r"[\u0400-\u04ff\u4e00-\u9fff\uac00-\ud7af]", clean)
    if len(cjk_or_cyrillic) > 10:
        return False

    diacritics = re.findall(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", clean)
    common_hits = sum(1 for word in VIETNAMESE_COMMON_WORDS if re.search(rf"\b{re.escape(word)}\b", clean))
    return len(diacritics) >= 3 or common_hits >= 4


def build_combined_text(parsed_output: dict, raw_output: str) -> str:
    if raw_output and raw_output.strip():
        return raw_output

    feedback = parsed_output.get("feedback", {}) if isinstance(parsed_output, dict) else {}
    parts = [str(parsed_output.get("rebuttal", ""))] if isinstance(parsed_output, dict) else []
    if isinstance(feedback, dict):
        parts.append(_flatten_feedback(feedback))
    return " ".join(part for part in parts if part)


def _has_required_shape(parsed_output: dict) -> bool:
    if not isinstance(parsed_output, dict):
        return False
    cer = parsed_output.get("cer")
    feedback = parsed_output.get("feedback")
    if "rebuttal" not in parsed_output or not isinstance(cer, dict) or not isinstance(feedback, dict):
        return False
    if not all(key in cer for key in ("claim", "evidence", "reasoning", "total")):
        return False
    return all(key in feedback for key in ("strengths", "weaknesses", "suggestions"))


def _has_non_empty_feedback(feedback: dict) -> bool:
    if not isinstance(feedback, dict):
        return False
    for key in ("strengths", "weaknesses", "suggestions"):
        value = feedback.get(key)
        if not isinstance(value, list) or not any(str(item).strip() for item in value):
            return False
    return True


def evaluate_debate_output(case: dict, parsed_output: dict, raw_output: str = "") -> dict:
    """Score one AI Debate Trainer output with a transparent 7-point rule rubric."""
    parsed_output = parsed_output if isinstance(parsed_output, dict) else {}
    raw_output = raw_output or ""
    case_id = str(case.get("case_id", "unknown"))
    expected = case.get("expected", {}) if isinstance(case.get("expected"), dict) else {}

    cer = parsed_output.get("cer", {})
    feedback = parsed_output.get("feedback", {})
    rebuttal = str(parsed_output.get("rebuttal", "") or "")
    combined_text = build_combined_text(parsed_output, raw_output)
    max_words = expected.get("max_words", 300)
    if not isinstance(max_words, int) or max_words <= 0:
        max_words = 300

    format_valid = _has_required_shape(parsed_output)
    has_rebuttal = looks_like_rebuttal(rebuttal)
    has_valid_cer = isinstance(cer, dict) and total_is_correct(cer)
    has_feedback = _has_non_empty_feedback(feedback)
    main_weakness = detect_main_weakness(cer) if has_valid_cer else ""
    feedback_aligned = bool(has_feedback and main_weakness and feedback_mentions_weakness(feedback, main_weakness))
    within_word_limit = count_words_vi(combined_text) <= max_words
    language_valid = looks_vietnamese(combined_text)

    criteria = {
        "format_valid": format_valid,
        "has_rebuttal": has_rebuttal,
        "has_valid_cer": has_valid_cer,
        "has_feedback": has_feedback,
        "feedback_aligned": feedback_aligned,
        "within_word_limit": within_word_limit,
        "language_valid": language_valid,
    }

    score = sum(1 for passed in criteria.values() if passed)
    notes = [f"failed {name}" for name, passed in criteria.items() if not passed]
    if parsed_output.get("ok") is False:
        notes.append("parser reported non-ideal output")

    return {
        "case_id": case_id,
        "score": score,
        "max_score": MAX_SCORE,
        "passed": score >= PASS_THRESHOLD,
        "criteria": criteria,
        "notes": notes,
    }
