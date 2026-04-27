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


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text or "", flags=re.UNICODE))


def _clamp(value: Any, minimum: float = 0.0, maximum: float = 100.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(minimum, min(maximum, number))


def _score_to_100(value: Any) -> float:
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


def invalid_cer_result(reason: str = "invalid") -> dict:
    return {
        "is_valid": False,
        "status": "invalid",
        "rebuttal": INVALID_REBUTTAL,
        "cer": {"claim": 0.0, "evidence": 0.0, "reasoning": 0.0, "overall": 0.0, "total": 0.0},
        "cer_breakdown": DEFAULT_BREAKDOWN.copy(),
        "feedback": INVALID_FEEDBACK.copy(),
        "raw_scoring_text": "",
        "scoring_error": reason,
    }


def fallback_cer_result(error: str = "parse_error") -> dict:
    claim = 50.0
    evidence = 40.0
    reasoning = 50.0
    overall = _weighted_overall(claim, evidence, reasoning)
    return {
        "is_valid": True,
        "status": "success",
        "rebuttal": "AI chưa tạo được phản biện chi tiết, nhưng hệ thống đã chấm điểm cơ bản cho lập luận.",
        "cer": {
            "claim": claim,
            "evidence": evidence,
            "reasoning": reasoning,
            "overall": overall,
            "total": overall,
        },
        "cer_breakdown": FALLBACK_BREAKDOWN.copy(),
        "feedback": {
            "strengths": ["Lập luận có thể hiện một quan điểm ban đầu."],
            "weaknesses": ["Hệ thống chưa parse được đầy đủ điểm rubric từ AI."],
            "suggestions": ["Hãy bổ sung claim rõ, dẫn chứng cụ thể và giải thích liên kết logic."],
        },
        "raw_scoring_text": "",
        "scoring_error": error,
    }


def parse_cer_rubric_output(raw_text: str) -> dict:
    try:
        payload = json.loads(strip_json_code_block(raw_text))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        result = fallback_cer_result(str(exc))
        result["raw_scoring_text"] = raw_text or ""
        return result

    is_valid = bool(payload.get("is_valid", True))
    if not is_valid:
        result = invalid_cer_result(str(payload.get("status") or "invalid"))
        result["raw_scoring_text"] = raw_text or ""
        return result

    rebuttal = str(payload.get("ai_rebuttal") or payload.get("rebuttal") or "").strip()

    claim_breakdown = payload.get("claim_breakdown") or {}
    evidence_breakdown = payload.get("evidence_breakdown") or {}
    reasoning_breakdown = payload.get("reasoning_breakdown") or {}
    breakdown = {
        "claim": {
            "clarity": round(_clamp(claim_breakdown.get("clarity"), 0.0, 40.0), 1),
            "relevance": round(_clamp(claim_breakdown.get("relevance"), 0.0, 30.0), 1),
            "specificity": round(_clamp(claim_breakdown.get("specificity"), 0.0, 30.0), 1),
        },
        "evidence": {
            "presence": round(_clamp(evidence_breakdown.get("presence"), 0.0, 40.0), 1),
            "specificity": round(_clamp(evidence_breakdown.get("specificity"), 0.0, 30.0), 1),
            "relevance": round(_clamp(evidence_breakdown.get("relevance"), 0.0, 30.0), 1),
        },
        "reasoning": {
            "logical_connection": round(_clamp(reasoning_breakdown.get("logical_connection"), 0.0, 40.0), 1),
            "causal_explanation": round(_clamp(reasoning_breakdown.get("causal_explanation"), 0.0, 40.0), 1),
            "fallacy_control": round(_clamp(reasoning_breakdown.get("fallacy_control"), 0.0, 20.0), 1),
        },
    }

    claim = _score_to_100(payload.get("claim_score"))
    evidence = _score_to_100(payload.get("evidence_score"))
    reasoning = _score_to_100(payload.get("reasoning_score"))
    if claim == 0.0:
        claim = _sum_breakdown(breakdown["claim"], {"clarity": 40, "relevance": 30, "specificity": 30})
    if evidence == 0.0:
        evidence = _sum_breakdown(breakdown["evidence"], {"presence": 40, "specificity": 30, "relevance": 30})
    if reasoning == 0.0:
        reasoning = _sum_breakdown(
            breakdown["reasoning"],
            {"logical_connection": 40, "causal_explanation": 40, "fallacy_control": 20},
        )
    overall = _weighted_overall(claim, evidence, reasoning)

    return {
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
            "strengths": _clean_list(payload.get("strengths")),
            "weaknesses": _clean_list(payload.get("weaknesses"), ["Cần làm rõ hơn bằng chứng và suy luận."]),
            "suggestions": _clean_list(payload.get("suggestions"), ["Bổ sung ví dụ cụ thể và giải thích quan hệ nhân quả."]),
        },
        "raw_scoring_text": raw_text or "",
        "scoring_error": "",
    }


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
