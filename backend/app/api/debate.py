from fastapi import APIRouter, HTTPException
from app.schemas.debate import (
    StartSessionRequest,
    StartSessionResponse,
    DebateTurnRequest,
    DebateTurnResponse,
    SessionInfoResponse,
)
from app.services.ai_service import generate_rebuttal
from app.services.session_store import create_session, get_session

router = APIRouter()


@router.post("/session", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest):
    session = create_session(
        topic=payload.topic,
        stance=payload.stance,
        difficulty=payload.difficulty,
        input_mode=payload.input_mode,
    )

    return StartSessionResponse(
        session_id=session["session_id"],
        topic=session["topic"],
        stance=session["stance"],
        difficulty=session["difficulty"],
        input_mode=session["input_mode"],
        status="ready",
    )


@router.post("/turn", response_model=DebateTurnResponse)
def debate_turn(payload: DebateTurnRequest):
    session = get_session(payload.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not payload.user_argument.strip():
        raise HTTPException(status_code=400, detail="user_argument is empty")

    result = generate_rebuttal(
        topic=session["topic"],
        stance=session["stance"],
        difficulty=session["difficulty"],
        user_argument=payload.user_argument,
    )

    return DebateTurnResponse(
        session_id=payload.session_id,
        user_argument=payload.user_argument,
        ai_rebuttal=result["text"],
        status="success" if result["ok"] else "error",
    )
@router.get("/session/{session_id}", response_model=SessionInfoResponse)
def get_session_info(session_id: str):
    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfoResponse(
        session_id=session["session_id"],
        topic=session["topic"],
        stance=session["stance"],
        difficulty=session["difficulty"],
        input_mode=session["input_mode"],
        status="found"
    )