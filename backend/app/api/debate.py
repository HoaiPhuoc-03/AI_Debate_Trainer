from fastapi import APIRouter, HTTPException
import time
from app.schemas.debate import (
    StartSessionRequest,
    StartSessionResponse,
    DebateTurnRequest,
    DebateTurnResponse,
    SessionInfoResponse,
)
from app.services.ai_service import generate_rebuttal
from app.services.session_store import create_session, get_session
from app.services.session_store.repository import (
    start_session as db_start_session,
    get_session_info as db_get_session_info,
    process_turn,
    save_cer_score,
    save_feedback,
    save_content_flag,
    end_session as db_end_session,
)

router = APIRouter()


@router.post("/session", response_model=StartSessionResponse)
def start_session_endpoint(payload: StartSessionRequest):
    """
    Tạo phiên mới sử dụng repository thực (SQLite).
    """
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
    """
    Xử lý một vòng tranh biện:
    1. Lấy session từ DB
    2. Gọi AI để tạo rebuttal
    3. Lưu turn vào DB (process_turn)
    4. Lưu CER scores (tạm mock)
    5. Lưu feedback (tạm mock)
    6. Lưu content flags
    7. Kiểm tra & end session nếu hết lượt
    """
    # Bước 1: Lấy session từ DB
    session_resp = db_get_session_info(payload.session_id)
    if not session_resp:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = {
        "session_id": session_resp.session_id,
        "topic": session_resp.topic,
        "stance": session_resp.stance,
        "difficulty": session_resp.difficulty,
        "input_mode": session_resp.input_mode,
        "status": session_resp.status,
    }

    # Kiểm tra user_argument
    if not payload.user_argument.strip():
        raise HTTPException(status_code=400, detail="user_argument is empty")

    # Bước 2: Gọi AI để tạo rebuttal (đo thời gian)
    start_time = time.time()
    result = generate_rebuttal(
        topic=session["topic"],
        stance=session["stance"],
        difficulty=session["difficulty"],
        user_argument=payload.user_argument,
    )
    processing_time_ms = int((time.time() - start_time) * 1000)

    # Kiểm tra AI có lỗi không
    if not result["ok"]:
        return DebateTurnResponse(
            session_id=payload.session_id,
            user_argument=payload.user_argument,
            ai_rebuttal=result["text"],
            status="error",
        )

    # Bước 3: Lưu turn vào DB
    turn_resp = process_turn(
        req=payload,
        ai_rebuttal=result["text"],
        processing_time_ms=processing_time_ms,
        is_safe=True,
    )

    # Bước 4: Lưu CER scores (tạm mock - giá trị cố định)
    # Trong thực tế, phải có logic từ AI để tính điểm
    try:
        save_cer_score(
            session_id=payload.session_id,
            claim=7.5,
            evidence=6.5,
            reasoning=7.0,
        )
    except Exception as e:
        print(f"Warning: Could not save CER score: {e}")

    # Bước 5: Lưu feedback (tạm mock)
    try:
        turn_id = None
        # Lấy turn_id từ DB (turn mới nhất)
        from app.services.session_store.database import get_connection
        with get_connection() as conn:
            row = conn.execute("""
                SELECT id FROM debate_turns
                WHERE session_id = ?
                ORDER BY turn_number DESC LIMIT 1
            """, (payload.session_id,)).fetchone()
            if row:
                turn_id = row["id"]
        
        if turn_id:
            save_feedback(
                turn_id=turn_id,
                strengths=["Lập luận rõ ràng"],
                weaknesses=["Cần thêm dẫn chứng"],
                suggestions=["Bổ sung số liệu cụ thể"],
            )
    except Exception as e:
        print(f"Warning: Could not save feedback: {e}")

    # Bước 6: Lưu content flags (tạm mock - no flags)
    try:
        turn_id = None
        from app.services.session_store.database import get_connection
        with get_connection() as conn:
            row = conn.execute("""
                SELECT id FROM debate_turns
                WHERE session_id = ?
                ORDER BY turn_number DESC LIMIT 1
            """, (payload.session_id,)).fetchone()
            if row:
                turn_id = row["id"]
        
        if turn_id:
            save_content_flag(
                turn_id=turn_id,
                is_flagged=False,
                flag_reason="",
                flagged_terms=[],
            )
    except Exception as e:
        print(f"Warning: Could not save content flag: {e}")

    # Bước 7: Kiểm tra & end session nếu hết lượt
    # turn_resp.status sẽ là 'completed' nếu đã đủ lượt
    final_status = turn_resp.status
    if final_status == "completed":
        db_end_session(payload.session_id)

    return DebateTurnResponse(
        session_id=payload.session_id,
        user_argument=payload.user_argument,
        ai_rebuttal=result["text"],
        status=final_status,
    )


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
def get_session_info_endpoint(session_id: str):
    """
    Lấy thông tin phiên từ DB.
    """
    session_resp = db_get_session_info(session_id)

    if not session_resp:
        raise HTTPException(status_code=404, detail="Session not found")

    return session_resp


@router.post("/session/{session_id}/end", response_model=SessionInfoResponse)
def end_session_endpoint(session_id: str):
    """
    Kết thúc phiên sớm và tính điểm trung bình.
    """
    session_resp = db_get_session_info(session_id)
    if not session_resp:
        raise HTTPException(status_code=404, detail="Session not found")
    
    final_resp = db_end_session(session_id)
    return final_resp