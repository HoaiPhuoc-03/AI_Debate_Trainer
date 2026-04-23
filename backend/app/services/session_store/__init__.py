"""
AI Debate Trainer — Session Store Wrapper
Cung cấp interface dict-based cho api/debate.py, 
bằng cách wrap repository functions (Pydantic-based).
"""

from typing import Optional
from app.schemas.debate import StartSessionRequest
from .repository import start_session, get_session_info


def create_session(
    topic: str,
    stance: str,
    difficulty: str,
    input_mode: str = "text",
) -> dict:
    """
    Wrap start_session() để trả về dict thay vì StartSessionResponse.
    API expects: dict với keys session_id, topic, stance, difficulty, input_mode, status
    """
    req = StartSessionRequest(
        topic=topic,
        stance=stance,
        difficulty=difficulty,
        input_mode=input_mode,
    )
    resp = start_session(req)
    return {
        "session_id": resp.session_id,
        "topic": resp.topic,
        "stance": resp.stance,
        "difficulty": resp.difficulty,
        "input_mode": resp.input_mode,
        "status": resp.status,
    }


def get_session(session_id: str) -> Optional[dict]:
    """
    Wrap get_session_info() để trả về dict thay vì SessionInfoResponse.
    API expects: dict với keys session_id, topic, stance, difficulty, input_mode, status
    """
    resp = get_session_info(session_id)
    if not resp:
        return None
    return {
        "session_id": resp.session_id,
        "topic": resp.topic,
        "stance": resp.stance,
        "difficulty": resp.difficulty,
        "input_mode": resp.input_mode,
        "status": resp.status,
    }


__all__ = ["create_session", "get_session"]