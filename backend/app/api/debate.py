import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.debate import (
    DebateTurnRequest,
    DebateTurnResponseV2,
    DebateTopicCategoriesResponse,
    DebateTopicsResponse,
    PracticePromptRequest,
    PracticePromptResponse,
    ProgressOverviewResponse,
    SessionInfoResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from app.services import ai_service
from app.services.auth_service import get_current_user, get_debate_user
from app.services.cer_scorer import normalize_cer_to_100
from app.services.practice_prompt_service import build_practice_prompt
from app.services.prompt_builder import normalize_practice_mode
from app.data.topics import list_categories, list_topics, recommended_topics
from app.services.normalization import (
    normalize_session_payload,
    normalize_stance,
    normalize_status,
    validate_debate_topic,
    validate_stance,
)
from app.services.session_store import (
    create_session,
    end_session,
    get_progress_overview,
    get_session,
    get_session_summary,
    get_session_turns,
    get_session_memory,
    get_user_memory,
    reset_user_memory,
    save_practice_prompt,
    save_debate_turn,
    update_session_memory,
    update_user_memory_after_turn,
)

router = APIRouter()
logger = logging.getLogger("uvicorn.error")
SINGLE_SKILL_MODES = {"claim_writing", "find_evidence", "quick_rebuttal", "full_argument"}


def _session_response(session: dict) -> dict:
    return {
        "session_id": session["session_id"],
        "topic": session["topic"],
        "topic_id": session.get("topic_id"),
        "topic_category": session.get("topic_category"),
        "topic_tags": session.get("topic_tags"),
        "custom_topic": session.get("custom_topic"),
        "stance": normalize_stance(session.get("stance")),
        "difficulty": session["difficulty"],
        "input_mode": session["input_mode"],
        "age_group": session.get("age_group") or "adult",
        "debate_level": session.get("debate_level") or "intermediate",
        "coach_model": session.get("coach_model") or "socratic_v3",
        "language": session.get("language") or "vi",
        "mode": session.get("mode") or "free_debate",
        "response_time": session.get("response_time"),
        "max_turns": int(session.get("max_turns") or 0),
        "turn_count": int(session.get("turn_count") or 0),
        "status": normalize_status(session.get("status")),
    }


@router.get("/topics", response_model=DebateTopicsResponse)
def get_debate_topics(
    category: str | None = None,
    difficulty: str | None = None,
    q: str | None = None,
    limit: int | None = None,
    tag: str | None = None,
):
    safe_limit = None
    if limit is not None:
        safe_limit = max(1, min(int(limit), 100))
    topics = list_topics(
        category=category,
        difficulty=difficulty,
        q=q,
        tag=tag,
        limit=safe_limit,
    )
    return {
        "status": "success",
        "topics": topics,
        "total": len(topics),
    }


@router.get("/topics/recommended", response_model=DebateTopicsResponse)
def get_recommended_debate_topics(
    user_id: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    limit: int = 12,
):
    # The current implementation uses local seed data only. The user_id
    # parameter is accepted now so Firestore history ranking can be added later
    # without changing the public endpoint contract.
    _ = user_id
    safe_limit = max(1, min(int(limit), 50))
    topics = recommended_topics(
        difficulty=difficulty,
        category=category,
        limit=safe_limit,
    )
    return {
        "status": "success",
        "topics": topics,
        "total": len(topics),
    }


@router.get("/topic-categories", response_model=DebateTopicCategoriesResponse)
def get_debate_topic_categories():
    return {
        "status": "success",
        "categories": list_categories(),
    }


@router.post("/session", response_model=StartSessionResponse)
def start_session(
    payload: StartSessionRequest,
    current_user: dict = Depends(get_debate_user),
):
    topic_validation = validate_debate_topic(payload.topic)
    if not topic_validation["is_valid"]:
        raise HTTPException(status_code=400, detail=topic_validation["message"])
    stance_validation = validate_stance(payload.stance)
    if not stance_validation["is_valid"]:
        raise HTTPException(status_code=400, detail=stance_validation["message"])
    normalized = normalize_session_payload(payload)
    session = create_session(user_id=current_user["id"], **normalized)
    return _session_response(session)


@router.post("/practice-prompt", response_model=PracticePromptResponse)
def create_practice_prompt(
    payload: PracticePromptRequest,
    current_user: dict = Depends(get_debate_user),
):
    topic_validation = validate_debate_topic(payload.topic)
    if not topic_validation["is_valid"]:
        raise HTTPException(status_code=400, detail=topic_validation["message"])
    if payload.session_id and not get_session(payload.session_id, user_id=current_user["id"]):
        raise HTTPException(status_code=404, detail="Session not found")

    result = build_practice_prompt(
        mode=payload.mode,
        topic=payload.topic,
        difficulty=payload.difficulty,
        category=payload.category,
        round_number=payload.round,
        session_id=payload.session_id,
        used_prompts=payload.previous_prompts,
        previous_topics=payload.previous_topics,
        avoid_repeating=payload.avoid_repeating,
    )
    saved = save_practice_prompt(
        session_id=payload.session_id,
        user_id=current_user["id"],
        mode=result["mode"],
        topic=result.get("topic") or payload.topic,
        topic_id=result.get("topic_id"),
        category=result.get("category") or payload.category,
        difficulty=result.get("difficulty") or payload.difficulty,
        prompt_type=result.get("prompt_type"),
        prompt_text=result.get("prompt"),
        instruction=result.get("instruction"),
        round_number=payload.round,
        metadata={
            "source": result.get("source"),
            "warning": result.get("warning"),
            "fallacy_hint": result.get("fallacy_hint"),
            "target_flaws": result.get("target_flaws"),
        },
    )
    result["practice_prompt_id"] = saved["practice_prompt_id"]
    if payload.session_id:
        memory = get_session_memory(payload.session_id, current_user["id"])
        prompts = list(memory.get("practice_prompts") or [])
        prompts.append(
            {
                "practice_prompt_id": saved["practice_prompt_id"],
                "mode": result["mode"],
                "topic": result.get("topic") or payload.topic,
                "prompt": result.get("prompt"),
                "target_flaws": result.get("target_flaws"),
                "round": payload.round,
            }
        )
        memory["practice_prompts"] = prompts[-12:]
        memory["active_mode"] = result["mode"]
        update_session_memory(payload.session_id, current_user["id"], memory)
    return result


@router.post("/turn", response_model=DebateTurnResponseV2)
def debate_turn(
    payload: DebateTurnRequest,
    current_user: dict = Depends(get_debate_user),
):
    turn_start = time.perf_counter()
    session = get_session(payload.session_id, user_id=current_user["id"])

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not payload.user_argument.strip():
        raise HTTPException(status_code=400, detail="user_argument is empty")

    if normalize_status(session["status"]) == "completed":
        raise HTTPException(status_code=400, detail="Session is already completed")

    # Fetch recent turns for conversation history.
    # Limit to last 3 to keep the prompt size bounded while giving enough
    # context for the LLM to produce evolving, non-repetitive rebuttals.
    turn_history = get_session_turns(payload.session_id)[-3:]

    active_mode = normalize_practice_mode(
        payload.practice_mode or session.get("practice_mode") or session.get("mode", "free_debate")
    )
    analysis_topic = (
        str(payload.practice_topic or "").strip()
        if active_mode in SINGLE_SKILL_MODES
        else ""
    ) or session["topic"]
    user_memory = get_user_memory(current_user["id"])
    mode_state = (user_memory.get("mode_state") or {}).get(active_mode, {})

    session_stance = normalize_stance(session.get("stance"))
    result = ai_service.generate_debate_analysis(
        topic=analysis_topic,
        stance=session_stance,
        difficulty=session["difficulty"],
        user_argument=payload.user_argument,
        age_group=session.get("age_group"),
        debate_level=session.get("debate_level"),
        coach_model=session.get("coach_model"),
        language=session.get("language"),
        input_mode=session.get("input_mode"),
        turn_history=turn_history,
            mode=session.get("mode", "free_debate"),
            practice_mode=active_mode,
            practice_prompt=payload.practice_prompt,
            practice_fallacy_hint=payload.practice_fallacy_hint,
            practice_target_flaws=payload.practice_target_flaws,
            practice_round=payload.practice_round,
            memory_context={
            "user_memory": user_memory,
            "mode_state": mode_state,
        },
    )
    result["cer"] = normalize_cer_to_100(result.get("cer"))
    ai_done_ms = int((time.perf_counter() - turn_start) * 1000)
    turn_status = "active" if result["ok"] else result.get("status", "error")

    saved = save_debate_turn(
        session=session,
        user_argument=payload.user_argument,
        ai_rebuttal=result["rebuttal"],
        cer=result["cer"],
        feedback=result["feedback"],
        mode_scores=result.get("mode_scores"),
        content_flags=result.get("content_flags", []),
        practice_mode=active_mode,
        practice_prompt=payload.practice_prompt,
        practice_round=payload.practice_round,
        practice_prompt_id=payload.practice_prompt_id,
        status=turn_status,
        count_for_completion=result["ok"],
        complete_session=active_mode not in SINGLE_SKILL_MODES,
    )
    response_status = saved["session"]["status"] if result["ok"] else turn_status
    if result["ok"]:
        update_user_memory_after_turn(
            user_id=current_user["id"],
            mode=active_mode,
            topic=analysis_topic,
            topic_category=session.get("topic_category"),
            user_argument=payload.user_argument,
            ai_result=result,
        )
        session_memory = get_session_memory(payload.session_id, current_user["id"])
        session_memory.update(
            {
                "active_mode": active_mode,
                "last_turn_id": saved["turn_id"],
                "last_turn_number": saved["turn_number"],
                "last_practice_prompt_id": payload.practice_prompt_id,
            }
        )
        update_session_memory(payload.session_id, current_user["id"], session_memory)
    total_turn_ms = int((time.perf_counter() - turn_start) * 1000)
    timings = result.get("timings", {})
    logger.info(
        "debate_turn_timing session_id=%s status=%s provider=%s build_prompt_ms=%s llm_ms=%s parse_output_ms=%s ai_total_ms=%s turn_total_ms=%s",
        payload.session_id,
        normalize_status(response_status),
        timings.get("provider") or result.get("provider"),
        timings.get("build_prompt_ms"),
        timings.get("llm_ms"),
        timings.get("parse_output_ms"),
        timings.get("total_ai_ms", ai_done_ms),
        total_turn_ms,
    )

    return DebateTurnResponseV2(
        session_id=payload.session_id,
        user_argument=payload.user_argument,
        ai_rebuttal=result["rebuttal"],
        practice_mode=active_mode,
        is_valid=result.get("is_valid", result["ok"]),
        cer_breakdown=result.get("cer_breakdown"),
        turn_number=int(saved["turn_number"]),
        max_turns=int(saved["session"].get("max_turns") or session["max_turns"]),
        status=normalize_status(response_status),
        cer=result["cer"],
        mode_scores=result.get("mode_scores") if active_mode == "quick_rebuttal" else None,
        feedback=result["feedback"],
    )


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
def get_session_info(
    session_id: str,
    current_user: dict = Depends(get_debate_user),
):
    session = get_session(session_id, user_id=current_user["id"])

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _session_response(session)


@router.post("/session/{session_id}/end", response_model=SessionInfoResponse)
def end_session_route(
    session_id: str,
    current_user: dict = Depends(get_debate_user),
):
    session = end_session(session_id, user_id=current_user["id"])

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _session_response(session)


@router.get("/session/{session_id}/summary", response_model=SessionSummaryResponse)
def get_session_summary_route(
    session_id: str,
    current_user: dict = Depends(get_debate_user),
):
    summary = get_session_summary(session_id, user_id=current_user["id"])

    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    summary["stance"] = normalize_stance(summary.get("stance"))
    return summary


@router.get("/progress/overview", response_model=ProgressOverviewResponse)
def get_progress_overview_route(current_user: dict = Depends(get_debate_user)):
    return get_progress_overview(user_id=current_user["id"])


@router.get("/user-memory")
def get_user_memory_route(current_user: dict = Depends(get_current_user)):
    return {"memory": get_user_memory(current_user["id"])}


@router.delete("/user-memory")
def reset_user_memory_route(current_user: dict = Depends(get_current_user)):
    return {"memory": reset_user_memory(current_user["id"])}
