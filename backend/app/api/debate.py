import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.debate import (
    DebateTurnRequest,
    DebateTurnResponseV2,
    ProgressOverviewResponse,
    SessionInfoResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from app.services import ai_service
from app.services.auth_service import get_debate_user
from app.services.cer_scorer import normalize_cer_to_100
from app.services.normalization import normalize_session_payload, normalize_status, validate_debate_topic
from app.services.session_store import (
    create_session,
    end_session,
    get_progress_overview,
    get_session,
    get_session_summary,
    save_debate_turn,
)

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


def _session_response(session: dict) -> dict:
    return {
        "session_id": session["session_id"],
        "topic": session["topic"],
        "topic_category": session.get("topic_category"),
        "custom_topic": session.get("custom_topic"),
        "stance": session["stance"],
        "difficulty": session["difficulty"],
        "input_mode": session["input_mode"],
        "age_group": session.get("age_group") or "adult",
        "debate_level": session.get("debate_level") or "intermediate",
        "coach_model": session.get("coach_model") or "socratic_v3",
        "language": session.get("language") or "vi",
        "response_time": session.get("response_time"),
        "max_turns": int(session.get("max_turns") or 0),
        "turn_count": int(session.get("turn_count") or 0),
        "status": normalize_status(session.get("status")),
    }


@router.post("/session", response_model=StartSessionResponse)
def start_session(
    payload: StartSessionRequest,
    current_user: dict = Depends(get_debate_user),
):
    topic_validation = validate_debate_topic(payload.topic)
    if not topic_validation["is_valid"]:
        raise HTTPException(status_code=400, detail=topic_validation["message"])
    normalized = normalize_session_payload(payload)
    session = create_session(user_id=current_user["id"], **normalized)
    return _session_response(session)


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

    result = ai_service.generate_debate_analysis(
        topic=session["topic"],
        stance=session["stance"],
        difficulty=session["difficulty"],
        user_argument=payload.user_argument,
        age_group=session.get("age_group"),
        debate_level=session.get("debate_level"),
        coach_model=session.get("coach_model"),
        language=session.get("language"),
        input_mode=session.get("input_mode"),
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
        content_flags=result.get("content_flags", []),
        status=turn_status,
        count_for_completion=result["ok"],
    )
    response_status = saved["session"]["status"] if result["ok"] else turn_status
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
        is_valid=result.get("is_valid", result["ok"]),
        cer_breakdown=result.get("cer_breakdown"),
        turn_number=int(saved["turn_number"]),
        max_turns=int(saved["session"].get("max_turns") or session["max_turns"]),
        status=normalize_status(response_status),
        cer=result["cer"],
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

    return summary


@router.get("/progress/overview", response_model=ProgressOverviewResponse)
def get_progress_overview_route(current_user: dict = Depends(get_debate_user)):
    return get_progress_overview(user_id=current_user["id"])
