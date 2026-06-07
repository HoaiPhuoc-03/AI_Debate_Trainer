from copy import deepcopy

from app.services.prompt_builder import normalize_practice_mode


MEMORY_MODES = (
    "free_debate",
    "claim_writing",
    "find_evidence",
    "quick_rebuttal",
    "full_argument",
)


def normalize_memory_mode(mode: str | None) -> str:
    normalized = normalize_practice_mode(mode)
    return normalized if normalized in MEMORY_MODES else "free_debate"


def default_user_memory(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "version": 1,
        "global": {
            "total_turns": 0,
            "avg_scores": {
                "claim": 0.0,
                "evidence": 0.0,
                "reasoning": 0.0,
                "overall": 0.0,
            },
            "topic_preferences": [],
            "recurring_weaknesses": [],
            "recurring_suggestions": [],
        },
        "mode_state": {
            mode: {
                "turn_count": 0,
                "common_weaknesses": [],
                "common_suggestions": [],
                "previous_claim_patterns": [],
                "evidence_patterns": [],
            }
            for mode in MEMORY_MODES
        },
    }


def merge_user_memory(memory: dict | None, user_id: str) -> dict:
    merged = default_user_memory(user_id)
    source = deepcopy(memory or {})
    source_global = source.get("global") or {}
    merged["global"].update(
        {key: value for key, value in source_global.items() if key != "avg_scores"}
    )
    merged["global"]["avg_scores"].update(source_global.get("avg_scores") or {})

    for raw_mode, state in (source.get("mode_state") or {}).items():
        mode = normalize_memory_mode(raw_mode)
        if isinstance(state, dict):
            merged["mode_state"][mode].update(state)

    merged["user_id"] = user_id
    merged["version"] = int(source.get("version") or merged["version"])
    return merged


def unique_recent(existing: list, additions: list, limit: int = 8) -> list:
    values = []
    seen = set()
    for item in [*(additions or []), *(existing or [])]:
        clean = str(item or "").strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            values.append(clean)
        if len(values) >= limit:
            break
    return values


def update_memory_after_turn(
    memory: dict | None,
    *,
    user_id: str,
    mode: str | None,
    topic_category: str | None,
    ai_result: dict,
) -> dict:
    updated = merge_user_memory(memory, user_id)
    normalized_mode = normalize_memory_mode(mode)
    global_state = updated["global"]
    mode_state = updated["mode_state"][normalized_mode]
    previous_turns = int(global_state.get("total_turns") or 0)
    next_turns = previous_turns + 1
    cer = ai_result.get("cer") or {}

    for key in ("claim", "evidence", "reasoning", "overall"):
        score = float(cer.get(key, cer.get("total", 0.0)) or 0.0)
        old_avg = float(global_state["avg_scores"].get(key) or 0.0)
        global_state["avg_scores"][key] = round(
            ((old_avg * previous_turns) + score) / next_turns,
            2,
        )

    feedback = ai_result.get("feedback") or {}
    weaknesses = list(feedback.get("weaknesses") or [])
    suggestions = list(feedback.get("suggestions") or [])
    global_state["total_turns"] = next_turns
    global_state["topic_preferences"] = unique_recent(
        global_state.get("topic_preferences", []),
        [topic_category] if topic_category else [],
    )
    global_state["recurring_weaknesses"] = unique_recent(
        global_state.get("recurring_weaknesses", []),
        weaknesses,
    )
    global_state["recurring_suggestions"] = unique_recent(
        global_state.get("recurring_suggestions", []),
        suggestions,
    )

    mode_state["turn_count"] = int(mode_state.get("turn_count") or 0) + 1
    mode_state["common_weaknesses"] = unique_recent(
        mode_state.get("common_weaknesses", []),
        weaknesses,
    )
    mode_state["common_suggestions"] = unique_recent(
        mode_state.get("common_suggestions", []),
        suggestions,
    )
    if normalized_mode == "find_evidence" and float(cer.get("evidence", 0.0) or 0.0) < 60:
        mode_state["evidence_patterns"] = unique_recent(
            mode_state.get("evidence_patterns", []),
            ["thiếu bằng chứng cụ thể"],
        )
    return updated
