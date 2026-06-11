import json
import re
from typing import Any


INVALID_REBUTTAL = (
    "[THÔNG BÁO] Nội dung chưa phải là một lập luận hợp lệ. "
    "Vui lòng nhập lại lập luận rõ ràng hơn."
)

INVALID_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Lập luận chưa đủ rõ hoặc chưa hợp lệ để chấm điểm."],
    "suggestions": ["Hãy nêu rõ quan điểm, lý do và bằng chứng hỗ trợ cho lập luận."],
}

CLAIM_STRENGTHS_FALLBACK = [
    "Luận điểm thể hiện lập trường rõ ràng.",
    "Câu khẳng định ngắn gọn và tập trung vào chủ đề.",
]
CLAIM_WEAKNESSES_FALLBACK = [
    "Phạm vi của luận điểm có thể được giới hạn cụ thể hơn.",
    "Cách diễn đạt có thể khách quan và gãy gọn hơn.",
]
CLAIM_SUGGESTIONS_FALLBACK = [
    "Cố gắng xác định rõ đối tượng và phạm vi tác động trong luận điểm.",
    "Tránh sử dụng các từ ngữ quá chung chung hoặc mang tính chủ quan.",
]


def _filter_claim_feedback(items: list[str], fallback: list[str]) -> list[str]:
    forbidden = [
        "bằng chứng",
        "chứng cứ",
        "dẫn chứng",
        "số liệu",
        "ví dụ",
        "nguồn dẫn",
        "trích dẫn",
        "minh họa",
        "tài liệu",
        "evidence",
        "example",
        "statistics",
        "proof",
    ]
    filtered = [
        item
        for item in items
        if not any(word in item.casefold() for word in forbidden)
    ]
    return filtered or ([fallback[0]] if fallback else [])


QUICK_REBUTTAL_INVALID_FEEDBACK = {
    "strengths": [],
    "weaknesses": ["Câu trả lời chưa đủ rõ để xác định bạn đã bắt đúng lỗi trong luận điểm yếu hay chưa."],
    "suggestions": ["Hãy chỉ ra cụm yếu trong luận điểm, gọi tên lỗi/ngụy biện và giải thích ngắn vì sao lỗi đó làm lập luận kém thuyết phục."],
}

QUICK_REBUTTAL_FALLBACK_FEEDBACK = {
    "strengths": ["Đã có nỗ lực phản biện lại luận điểm yếu."],
    "weaknesses": ["Cần chỉ rõ lỗi chính trong luận điểm yếu và giải thích vì sao lỗi đó làm lập luận kém thuyết phục."],
    "suggestions": ["Hãy gọi tên lỗi/ngụy biện, trích cụm yếu trong luận điểm và thêm một phản ví dụ ngắn."],
}

DEFAULT_BREAKDOWN = {
    "claim": {"clarity": 0.0, "relevance": 0.0, "specificity": 0.0},
    "evidence": {"presence": 0.0, "specificity": 0.0, "relevance": 0.0},
    "reasoning": {
        "logical_connection": 0.0,
        "causal_explanation": 0.0,
        "fallacy_control": 0.0,
    },
}

FALLBACK_BREAKDOWN = {
    "claim": {"clarity": 20.0, "relevance": 20.0, "specificity": 10.0},
    "evidence": {"presence": 15.0, "specificity": 10.0, "relevance": 15.0},
    "reasoning": {
        "logical_connection": 20.0,
        "causal_explanation": 20.0,
        "fallacy_control": 10.0,
    },
}

QUICK_REBUTTAL_FALLBACK_BREAKDOWN = {
    "claim": {"clarity": 18.0, "relevance": 15.0, "specificity": 10.0},
    "evidence": {"presence": 14.0, "specificity": 10.0, "relevance": 12.0},
    "reasoning": {
        "logical_connection": 18.0,
        "causal_explanation": 16.0,
        "fallacy_control": 10.0,
    },
}

DEFAULT_MODE_SCORES = {
    "flaw_detection": 0.0,
    "counter_example": 0.0,
    "explanation": 0.0,
    "focus": 0.0,
    "overall": 0.0,
}

FALLBACK_MODE_SCORES = DEFAULT_MODE_SCORES.copy()


def _is_quick_rebuttal_mode(mode: str | None) -> bool:
    key = str(mode or "").strip().casefold().replace("-", "_").replace(" ", "_")
    return key in {"quick_rebuttal", "rebuttal", "phan_bien_nhanh"}


def _is_claim_writing_mode(mode: str | None) -> bool:
    key = str(mode or "").strip().casefold().replace("-", "_").replace(" ", "_")
    return key in {"claim_writing", "claim", "claim_practice"}


def _compute_qr_overall(
    flaw_detection: float,
    counter_example: float,
    explanation: float,
    focus: float,
) -> float:
    """Weighted overall for quick_rebuttal mode.

    Weights: flaw_detection 40%, explanation 25%, counter_example 20%, focus 15%.
    """
    return round(
        flaw_detection * 0.40
        + explanation * 0.25
        + counter_example * 0.20
        + focus * 0.15,
        1,
    )


def build_quick_rebuttal_mode_scores(payload: dict) -> dict:
    """Extract mode_scores from LLM JSON output for quick_rebuttal mode.

    Handles three scenarios:
    1. LLM returns mode_scores directly
    2. LLM returns only CER fields → map to mode_scores
    3. Missing fields → safe defaults
    """
    payload = payload or {}
    # Scenario 1: LLM returned mode_scores
    raw_ms = payload.get("mode_scores") or {}
    flaw = _score_to_100(raw_ms.get("flaw_detection"))
    counter = _score_to_100(raw_ms.get("counter_example"))
    explanation = _score_to_100(raw_ms.get("explanation"))
    focus = _score_to_100(raw_ms.get("focus"))
    raw_cer = payload.get("cer") or {}

    # Scenario 2: fallback individual missing fields to legacy CER-compatible keys.
    if not raw_ms or raw_ms.get("flaw_detection") is None:
        flaw = _score_to_100(payload.get("claim_score", raw_cer.get("claim")))
    if not raw_ms or raw_ms.get("counter_example") is None:
        counter = _score_to_100(payload.get("evidence_score", raw_cer.get("evidence")))
    if not raw_ms or raw_ms.get("explanation") is None:
        explanation = _score_to_100(payload.get("reasoning_score", raw_cer.get("reasoning")))
    if not raw_ms or raw_ms.get("focus") is None:
        checklist = payload.get("checklist") or {}
        if "stays_focused" in checklist:
            focus = 75.0 if checklist.get("stays_focused") else 40.0
        else:
            focus = _score_to_100(raw_cer.get("focus", raw_cer.get("overall") or payload.get("overall_score")))

    # Overall: prefer LLM value, fallback to weighted formula
    raw_overall = raw_ms.get("overall") if raw_ms.get("overall") is not None else None
    if raw_overall is None and not raw_ms:
        raw_overall = payload.get("overall_score", raw_cer.get("overall", raw_cer.get("total")))
    if raw_overall is not None and str(raw_overall).strip() not in ("", "null"):
        overall = _score_to_100(raw_overall)
    else:
        overall = _compute_qr_overall(flaw, counter, explanation, focus)

    return {
        "flaw_detection": flaw,
        "counter_example": counter,
        "explanation": explanation,
        "focus": focus,
        "overall": overall,
    }


def build_quick_rebuttal_compat_cer(mode_scores: dict) -> dict:
    """Build CER-compatible dict from quick_rebuttal mode_scores.

    Quick Rebuttal compatibility mapping:
      claim     = flaw_detection
      evidence  = counter_example
      reasoning = explanation
    This is NOT normal CER scoring — it exists only to keep the
    existing frontend/API contract stable.
    """
    mode_scores = mode_scores or {}
    overall = _score_to_100(mode_scores.get("overall", 0.0))
    # Quick Rebuttal compatibility mapping:
    # claim = flaw_detection
    # evidence = counter_example
    # reasoning = explanation
    # This is only to keep the existing frontend/API contract stable.
    return {
        "claim": _score_to_100(mode_scores.get("flaw_detection", 0.0)),
        "evidence": _score_to_100(mode_scores.get("counter_example", 0.0)),
        "reasoning": _score_to_100(mode_scores.get("explanation", 0.0)),
        "overall": overall,
        "total": overall,
    }


def _feedback_defaults_for_mode(mode: str | None) -> dict[str, list[str]]:
    if _is_quick_rebuttal_mode(mode):
        return QUICK_REBUTTAL_FALLBACK_FEEDBACK
    if _is_claim_writing_mode(mode):
        return {
            "strengths": CLAIM_STRENGTHS_FALLBACK,
            "weaknesses": CLAIM_WEAKNESSES_FALLBACK,
            "suggestions": CLAIM_SUGGESTIONS_FALLBACK,
        }
    return {
        "strengths": [],
        "weaknesses": ["Cần làm rõ hơn bằng chứng và suy luận."],
        "suggestions": ["Bổ sung ví dụ cụ thể và giải thích quan hệ nhân quả."],
    }


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text or "", flags=re.UNICODE))


def _clamp(value: Any, minimum: float = 0.0, maximum: float = 100.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(minimum, min(maximum, number))


def _score_to_100(value: Any) -> float:
    """Convert any score value to 0–100 float.

    Handles:
    - int/float: used directly
    - str: strip non-numeric chars and parse (handles '37', '"37"', '<37>')
    - fractional (0, 1]: multiply by 100
    Returns 0.0 on failure.
    """
    if isinstance(value, str):
        # Strip surrounding quotes, angle brackets, whitespace, and non-numeric
        # characters except period and minus (for negative guard)
        cleaned = re.sub(r'[^0-9.\-]', '', value.strip().strip('"\"<>'))
        try:
            value = float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0
    number = _clamp(value)
    if 0.0 < number <= 1.0:
        number *= 100.0
    return round(_clamp(number), 1)


def _clean_list(value: Any, default: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:3]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return list(default or [])


def _remove_chinese_characters(text: str) -> str:
    # Programmatic filtering disabled first to test prompt-level improvements
    return text



def _extract_section(text: str, section_name: str) -> str:
    section = re.escape(section_name)
    pattern = rf"\[{section}\]\s*(.*?)(?=\n\[[A-Z_]+\]\s*|\Z)"
    match = re.search(pattern, text or "", flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_marker_score(label: str, text: str) -> float:
    pattern = rf"{re.escape(label)}\s*:\s*(-?\d+(?:\.\d+)?)\s*(?:/100)?"
    match = re.search(pattern, text or "", flags=re.IGNORECASE)
    return _score_to_100(match.group(1)) if match else 0.0


def _feedback_subsection(feedback_text: str, label: str) -> str:
    labels = "Strengths|Weaknesses|Suggestions"
    pattern = rf"{re.escape(label)}\s*:\s*(.*?)(?=\n(?:{labels})\s*:|\Z)"
    match = re.search(pattern, feedback_text or "", flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_bullets(section_text: str) -> list[str]:
    items = []
    for line in (section_text or "").splitlines():
        clean = re.sub(r"^[-*•]\s*", "", line.strip()).strip()
        if clean:
            items.append(clean)
    return items[:3]


def _proportional_breakdown(score: float, weights: dict[str, float]) -> dict[str, float]:
    return {key: round(_clamp(score * weight, 0.0, cap), 1) for key, (weight, cap) in weights.items()}


def _parse_marker_rubric_output(raw_text: str, mode: str | None = None) -> dict:
    rebuttal = _extract_section(raw_text, "REBUTTAL")
    cer_text = _extract_section(raw_text, "CER")
    feedback_text = _extract_section(raw_text, "FEEDBACK")
    if not rebuttal or not cer_text:
        result = fallback_cer_result("missing_marker_sections", mode=mode)
        result["raw_scoring_text"] = raw_text or ""
        return result

    claim = _parse_marker_score("Claim", cer_text)
    evidence = _parse_marker_score("Evidence", cer_text)
    reasoning = _parse_marker_score("Reasoning", cer_text)
    overall = _parse_marker_score("Overall", cer_text) or _weighted_overall(claim, evidence, reasoning)

    strengths = _parse_bullets(_feedback_subsection(feedback_text, "Strengths"))
    weaknesses = _parse_bullets(_feedback_subsection(feedback_text, "Weaknesses"))
    suggestions = _parse_bullets(_feedback_subsection(feedback_text, "Suggestions"))
    feedback_defaults = _feedback_defaults_for_mode(mode)
    if _is_claim_writing_mode(mode):
        strengths = _filter_claim_feedback(
            strengths or feedback_defaults["strengths"],
            CLAIM_STRENGTHS_FALLBACK,
        )
        weaknesses = _filter_claim_feedback(
            weaknesses or feedback_defaults["weaknesses"],
            CLAIM_WEAKNESSES_FALLBACK,
        )
        suggestions = _filter_claim_feedback(
            suggestions or feedback_defaults["suggestions"],
            CLAIM_SUGGESTIONS_FALLBACK,
        )

    result = {
        "is_valid": True,
        "status": "success",
        "rebuttal": rebuttal,
        "cer": {
            "claim": claim,
            "evidence": evidence,
            "reasoning": reasoning,
            "overall": round(_clamp(overall), 1),
            "total": round(_clamp(overall), 1),
        },
        "cer_breakdown": {
            "claim": _proportional_breakdown(
                claim,
                {
                    "clarity": (0.4, 40.0),
                    "relevance": (0.3, 30.0),
                    "specificity": (0.3, 30.0),
                },
            ),
            "evidence": _proportional_breakdown(
                evidence,
                {
                    "presence": (0.4, 40.0),
                    "specificity": (0.3, 30.0),
                    "relevance": (0.3, 30.0),
                },
            ),
            "reasoning": _proportional_breakdown(
                reasoning,
                {
                    "logical_connection": (0.4, 40.0),
                    "causal_explanation": (0.4, 40.0),
                    "fallacy_control": (0.2, 20.0),
                },
            ),
        },
        "feedback": {
            "strengths": strengths or feedback_defaults["strengths"],
            "weaknesses": weaknesses or feedback_defaults["weaknesses"],
            "suggestions": suggestions or feedback_defaults["suggestions"],
        },
        "raw_scoring_text": raw_text or "",
        "scoring_error": "",
    }
    if _is_quick_rebuttal_mode(mode):
        ms_payload = {
            "claim_score": claim,
            "evidence_score": evidence,
            "reasoning_score": reasoning,
        }
        ms = build_quick_rebuttal_mode_scores(ms_payload)
        result["mode_scores"] = ms
        result["cer"] = build_quick_rebuttal_compat_cer(ms)
    return result



def _weighted_overall(claim: float, evidence: float, reasoning: float) -> float:
    return round((claim * 0.3) + (evidence * 0.3) + (reasoning * 0.4), 1)


def _sum_breakdown(group: dict[str, Any], caps: dict[str, float]) -> float:
    total = 0.0
    for key, cap in caps.items():
        total += _clamp(group.get(key), 0.0, cap)
    return round(_clamp(total), 1)


def validate_user_argument(topic: str, user_argument: str) -> dict:
    argument = (user_argument or "").strip()
    lowered = argument.casefold()
    words = _word_count(argument)

    if not argument:
        return {"is_valid": False, "reason": "empty"}
    if len(argument) < 8 or words < 3:
        return {"is_valid": False, "reason": "too_short"}
    if len(set(re.findall(r"\w+", lowered, flags=re.UNICODE))) <= 1 and words >= 3:
        return {"is_valid": False, "reason": "spam"}
    if re.fullmatch(r"[\W_]+", argument, flags=re.UNICODE):
        return {"is_valid": False, "reason": "spam"}

    toxic_terms = [
        "đồ ngu",
        "do ngu",
        "câm miệng",
        "cam mieng",
        "chết đi",
        "chet di",
    ]
    if any(term in lowered for term in toxic_terms):
        return {"is_valid": False, "reason": "unsafe"}

    return {"is_valid": True, "reason": ""}


def strip_json_code_block(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def invalid_cer_result(reason: str = "invalid", mode: str | None = None) -> dict:
    feedback = QUICK_REBUTTAL_INVALID_FEEDBACK.copy() if _is_quick_rebuttal_mode(mode) else INVALID_FEEDBACK.copy()
    result = {
        "is_valid": False,
        "status": "invalid",
        "rebuttal": INVALID_REBUTTAL,
        "cer": {"claim": 0.0, "evidence": 0.0, "reasoning": 0.0, "overall": 0.0, "total": 0.0},
        "cer_breakdown": DEFAULT_BREAKDOWN.copy(),
        "feedback": feedback,
        "raw_scoring_text": "",
        "scoring_error": reason,
    }
    if _is_quick_rebuttal_mode(mode):
        result["mode_scores"] = DEFAULT_MODE_SCORES.copy()
    return result



def fallback_cer_result(error: str = "parse_error", mode: str | None = None) -> dict:
    quick_rebuttal = _is_quick_rebuttal_mode(mode)
    claim = 0.0 if quick_rebuttal else 50.0
    evidence = 0.0 if quick_rebuttal else 40.0
    reasoning = 0.0 if quick_rebuttal else 50.0
    overall = 0.0 if quick_rebuttal else _weighted_overall(claim, evidence, reasoning)
    feedback = QUICK_REBUTTAL_FALLBACK_FEEDBACK.copy() if quick_rebuttal else {
        "strengths": ["Lập luận có thể hiện một quan điểm ban đầu."],
        "weaknesses": ["Hệ thống chưa parse được đầy đủ điểm rubric từ AI."],
        "suggestions": ["Hãy bổ sung claim rõ, dẫn chứng cụ thể và giải thích liên kết logic."],
    }
    result = {
        "is_valid": True,
        "status": "success",
        "rebuttal": (
            "Lumi chưa đọc được điểm rubric chi tiết, nhưng sẽ chấm tạm theo kỹ năng bắt lỗi lập luận yếu."
            if quick_rebuttal
            else "AI chưa tạo được phản biện chi tiết, nhưng hệ thống đã chấm điểm cơ bản cho lập luận."
        ),
        "cer": {
            "claim": claim,
            "evidence": evidence,
            "reasoning": reasoning,
            "overall": overall,
            "total": overall,
        },
        "cer_breakdown": QUICK_REBUTTAL_FALLBACK_BREAKDOWN.copy() if quick_rebuttal else FALLBACK_BREAKDOWN.copy(),
        "feedback": feedback,
        "raw_scoring_text": "",
        "scoring_error": error,
    }
    if quick_rebuttal:
        result["mode_scores"] = FALLBACK_MODE_SCORES.copy()
        result["cer"] = build_quick_rebuttal_compat_cer(result["mode_scores"])
    return result



def parse_cer_rubric_output(raw_text: str, mode: str | None = None) -> dict:
    try:
        payload = json.loads(strip_json_code_block(raw_text))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        if _extract_section(raw_text, "REBUTTAL"):
            return _parse_marker_rubric_output(raw_text, mode=mode)
        result = fallback_cer_result(str(exc), mode=mode)
        result["raw_scoring_text"] = raw_text or ""
        return result

    is_valid = bool(payload.get("is_valid", True))
    if not is_valid:
        result = invalid_cer_result(str(payload.get("status") or "invalid"), mode=mode)
        result["raw_scoring_text"] = raw_text or ""
        return result

    rebuttal = str(payload.get("ai_rebuttal") or payload.get("rebuttal") or "").strip()
    quick_rebuttal = _is_quick_rebuttal_mode(mode)
    claim_mode = _is_claim_writing_mode(mode)
    rebuttal = _remove_chinese_characters(rebuttal)

    # Extract fact check items to check if evidence could not be verified on the internet
    fact_check_raw = payload.get("fact_check")
    fact_check = []
    has_unverified = False
    if isinstance(fact_check_raw, list):
        for item in fact_check_raw:
            if isinstance(item, dict):
                v = str(item.get("verdict") or "unverifiable").strip().lower()
                fact_check.append({
                    "claim_text": _remove_chinese_characters(str(item.get("claim_text") or "").strip()),
                    "verdict": v,
                    "explanation": _remove_chinese_characters(str(item.get("explanation") or "").strip()),
                    "source_url": _remove_chinese_characters(str(item.get("source_url") or "").strip()) or None,
                })
        # If there are fact check items, and none of them are verified, it can't be verified on the internet
        if fact_check and all(item["verdict"] != "verified" for item in fact_check):
            has_unverified = True

    # Python-side evidence gate: if the model found no evidence (quote is
    # "NONE" or absent, or checklist says has_real_evidence=False), or if the evidence
    # failed verification on the internet, hard-zero the entire evidence score and breakdown.
    evidence_quote = str(payload.get("evidence_quote") or "").strip().upper()
    checklist = payload.get("checklist") or {}
    has_real_evidence = bool(checklist.get("has_real_evidence", True))
    evidence_gate_zero = (
        False
        if (quick_rebuttal or claim_mode)
        else ((evidence_quote == "NONE") or (not has_real_evidence) or has_unverified)
    )

    claim_breakdown = payload.get("claim_breakdown") or {}
    evidence_breakdown = payload.get("evidence_breakdown") or {}
    reasoning_breakdown = payload.get("reasoning_breakdown") or {}

    # Helper: parse a breakdown sub-score, clamped to its sub-dimension cap.
    # Uses _score_to_100 so string values like "<0–40>" or "\"18\"" are safely
    # stripped to numeric before clamping — handles models that echo the template.
    def _bd(group: dict, key: str, cap: float) -> float:
        raw = group.get(key)
        val = _score_to_100(raw)
        return round(min(val, cap), 1)

    breakdown = {
        "claim": {
            "clarity": _bd(claim_breakdown, "clarity", 40.0),
            "relevance": _bd(claim_breakdown, "relevance", 30.0),
            "specificity": _bd(claim_breakdown, "specificity", 30.0),
        },
        "evidence": {
            # Gate: zero out all evidence sub-scores when no real evidence was found.
            "presence": 0.0 if (evidence_gate_zero or claim_mode) else _bd(evidence_breakdown, "presence", 40.0),
            "specificity": 0.0 if (evidence_gate_zero or claim_mode) else _bd(
                evidence_breakdown,
                "evidence_specificity" if "evidence_specificity" in evidence_breakdown else "specificity",
                30.0),
            "relevance": 0.0 if (evidence_gate_zero or claim_mode) else _bd(
                evidence_breakdown,
                "evidence_relevance" if "evidence_relevance" in evidence_breakdown else "relevance",
                30.0),
        },
        "reasoning": {
            "logical_connection": 0.0 if claim_mode else _bd(reasoning_breakdown, "logical_connection", 40.0),
            "causal_explanation": 0.0 if claim_mode else _bd(reasoning_breakdown, "causal_explanation", 40.0),
            "fallacy_control": 0.0 if claim_mode else _bd(reasoning_breakdown, "fallacy_control", 20.0),
        },
    }


    claim = _score_to_100(payload.get("claim_score"))
    # If the evidence gate zeroed the breakdown, the top-level score must also be 0.
    evidence = 0.0 if (evidence_gate_zero or claim_mode) else _score_to_100(payload.get("evidence_score"))
    reasoning = 0.0 if claim_mode else _score_to_100(payload.get("reasoning_score"))

    # Only fall back to breakdown summation when the score is genuinely absent
    # (i.e. the key is missing or the value is literally None/empty-string).
    # Do NOT fall back just because the value is 0 — evidence can legitimately
    # be 0, and claim/reasoning can be 0 for very poor arguments.
    claim_raw = payload.get("claim_score")
    evidence_raw = payload.get("evidence_score")
    reasoning_raw = payload.get("reasoning_score")

    if claim_raw is None or str(claim_raw).strip() in ("", "null"):
        claim = _sum_breakdown(breakdown["claim"], {"clarity": 40, "relevance": 30, "specificity": 30})
    if not (evidence_gate_zero or claim_mode) and (evidence_raw is None or str(evidence_raw).strip() in ("", "null")):
        evidence = _sum_breakdown(breakdown["evidence"], {"presence": 40, "specificity": 30, "relevance": 30})
    if not claim_mode and (reasoning_raw is None or str(reasoning_raw).strip() in ("", "null")):
        reasoning = _sum_breakdown(
            breakdown["reasoning"],
            {"logical_connection": 40, "causal_explanation": 40, "fallacy_control": 20},
        )
    overall_raw = payload.get("overall_score")
    if claim_mode:
        overall = claim
    elif quick_rebuttal and overall_raw is not None and str(overall_raw).strip() not in ("", "null"):
        overall = _score_to_100(overall_raw)
    else:
        overall = _weighted_overall(claim, evidence, reasoning)
    feedback_defaults = _feedback_defaults_for_mode(mode)
    raw_feedback = payload.get("feedback") or {}

    # Extract new mode-specific fields from the LLM response.
    evidence_source_links = [_remove_chinese_characters(link) for link in _clean_list(payload.get("evidence_source_links"), [])]
    better_source_suggestions = [_remove_chinese_characters(s) for s in _clean_list(payload.get("better_source_suggestions"), [])]
    model_claim = payload.get("model_claim")
    if model_claim and str(model_claim).strip().upper() == "NONE":
        model_claim = None
    elif model_claim:
        model_claim = str(model_claim).strip()

    strengths = _clean_list(
        payload.get("strengths", raw_feedback.get("strengths")),
        feedback_defaults["strengths"],
    )
    weaknesses = _clean_list(
        payload.get("weaknesses", raw_feedback.get("weaknesses")),
        feedback_defaults["weaknesses"],
    )
    suggestions = _clean_list(
        payload.get("suggestions", raw_feedback.get("suggestions")),
        feedback_defaults["suggestions"],
    )
    if claim_mode:
        strengths = _filter_claim_feedback(strengths, CLAIM_STRENGTHS_FALLBACK)
        weaknesses = _filter_claim_feedback(weaknesses, CLAIM_WEAKNESSES_FALLBACK)
        suggestions = _filter_claim_feedback(suggestions, CLAIM_SUGGESTIONS_FALLBACK)

    result = {
        "is_valid": True,
        "status": "success",
        "rebuttal": rebuttal,
        "cer": {
            "claim": claim,
            "evidence": evidence,
            "reasoning": reasoning,
            "overall": overall,
            "total": overall,
        },
        "cer_breakdown": breakdown,
        "feedback": {
            "strengths": [_remove_chinese_characters(item) for item in strengths],
            "weaknesses": [_remove_chinese_characters(item) for item in weaknesses],
            "suggestions": [_remove_chinese_characters(item) for item in suggestions],
        },
        "fact_check": fact_check,
        "evidence_source_links": evidence_source_links,
        "better_source_suggestions": better_source_suggestions,
        "model_claim": model_claim,
        "raw_scoring_text": raw_text or "",
        "scoring_error": "",
    }
    if quick_rebuttal:
        ms = build_quick_rebuttal_mode_scores(payload)
        result["mode_scores"] = ms
        # Overwrite CER with compat mapping so scores are consistent
        result["cer"] = build_quick_rebuttal_compat_cer(ms)
    return result



def normalize_cer_to_100(cer: dict | None) -> dict:
    cer = cer or {}

    def normalize(value) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        if 0.0 < number <= 1.0:
            number *= 100.0
        return round(_clamp(number), 1)

    claim = normalize(cer.get("claim"))
    evidence = normalize(cer.get("evidence"))
    reasoning = normalize(cer.get("reasoning"))
    overall = cer.get("overall", cer.get("total"))
    overall_score = normalize(overall) if overall is not None else _weighted_overall(claim, evidence, reasoning)
    return {
        "claim": claim,
        "evidence": evidence,
        "reasoning": reasoning,
        "overall": round(overall_score, 1),
        "total": round(overall_score, 1),
    }
