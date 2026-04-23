"""
AI Debate Trainer — Repository v2
Mọi hàm đều nhận vào hoặc trả về đúng Pydantic model từ debate.py.

Mapping rõ ràng:
  start_session(req: StartSessionRequest)  → StartSessionResponse
  get_session_info(session_id)             → SessionInfoResponse
  process_turn(req: DebateTurnRequest, …)  → DebateTurnResponse
  end_session(session_id)                  → SessionInfoResponse
"""

import uuid, json
from datetime import datetime, timezone
from typing import Optional

from database import get_connection
from app.schemas.debate import (
    StartSessionRequest, StartSessionResponse,
    DebateTurnRequest, DebateTurnResponse,
    SessionInfoResponse,
)


# ─── helpers ────────────────────────────────────────────
def _uid() -> str:
    return str(uuid.uuid4())

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ════════════════════════════════════════════════════════
#  SESSION
# ════════════════════════════════════════════════════════

def start_session(req: StartSessionRequest,
                  max_turns: int = 5) -> StartSessionResponse:
    """
    Nhận StartSessionRequest, tạo bản ghi mới,
    trả về StartSessionResponse.
    """
    sid = _uid()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO debate_sessions
              (session_id, topic, stance, difficulty, input_mode,
               status, turn_count, max_turns, created_at)
            VALUES (?,?,?,?,?,'active',0,?,?)
        """, (sid, req.topic, req.stance, req.difficulty,
              req.input_mode, max_turns, _now()))

    return StartSessionResponse(
        session_id = sid,
        topic      = req.topic,
        stance     = req.stance,
        difficulty = req.difficulty,
        input_mode = req.input_mode,
        status     = "active",
    )


def get_session_info(session_id: str) -> Optional[SessionInfoResponse]:
    """Trả về SessionInfoResponse hoặc None nếu không tìm thấy."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM debate_sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()
    if not row:
        return None
    return SessionInfoResponse(
        session_id = row["session_id"],
        topic      = row["topic"],
        stance     = row["stance"],
        difficulty = row["difficulty"],
        input_mode = row["input_mode"],
        status     = row["status"],
    )


def end_session(session_id: str) -> SessionInfoResponse:
    """
    Đóng phiên, tính điểm trung bình CER,
    trả về SessionInfoResponse với status='completed'.
    """
    with get_connection() as conn:
        scores = conn.execute("""
            SELECT AVG(cs.claim_score)     AS avg_claim,
                   AVG(cs.evidence_score)  AS avg_evidence,
                   AVG(cs.reasoning_score) AS avg_reasoning,
                   AVG(cs.total_score)     AS overall
            FROM debate_turns dt
            JOIN cer_scores cs ON cs.turn_id = dt.id
            WHERE dt.session_id = ?
        """, (session_id,)).fetchone()

        conn.execute("""
            UPDATE debate_sessions
            SET status              = 'completed',
                avg_claim_score     = ?,
                avg_evidence_score  = ?,
                avg_reasoning_score = ?,
                overall_score       = ?,
                ended_at            = ?
            WHERE session_id = ?
        """, (scores["avg_claim"], scores["avg_evidence"],
              scores["avg_reasoning"], scores["overall"],
              _now(), session_id))

    return get_session_info(session_id)


# ════════════════════════════════════════════════════════
#  TURNS
# ════════════════════════════════════════════════════════

def process_turn(req: DebateTurnRequest,
                 ai_rebuttal: str,
                 processing_time_ms: int,
                 is_safe: bool = True) -> DebateTurnResponse:
    """
    Nhận DebateTurnRequest + kết quả từ AI core,
    lưu debate_turns, tăng turn_count,
    trả về DebateTurnResponse.
    """
    turn_id = _uid()
    word_count = len(ai_rebuttal.split())

    with get_connection() as conn:
        # Lấy turn_number hiện tại
        row = conn.execute(
            "SELECT turn_count FROM debate_sessions WHERE session_id = ?",
            (req.session_id,)
        ).fetchone()
        turn_number = (row["turn_count"] or 0) + 1

        # Kiểm tra còn lượt không
        max_row = conn.execute(
            "SELECT max_turns FROM debate_sessions WHERE session_id = ?",
            (req.session_id,)
        ).fetchone()
        status = "active"
        if turn_number >= max_row["max_turns"]:
            status = "completed"

        # Lưu turn
        conn.execute("""
            INSERT INTO debate_turns
              (id, session_id, turn_number, user_argument, ai_rebuttal,
               ai_word_count, processing_time_ms, is_safe, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (turn_id, req.session_id, turn_number,
              req.user_argument, ai_rebuttal,
              word_count, processing_time_ms, int(is_safe), _now()))

        # Cập nhật turn_count và status nếu hết lượt
        conn.execute("""
            UPDATE debate_sessions
            SET turn_count = ?,
                status     = CASE WHEN ? = 'completed' THEN 'completed' ELSE status END
            WHERE session_id = ?
        """, (turn_number, status, req.session_id))

    return DebateTurnResponse(
        session_id    = req.session_id,
        user_argument = req.user_argument,
        ai_rebuttal   = ai_rebuttal,
        status        = status,
    )


# ════════════════════════════════════════════════════════
#  CER SCORES  (lưu nội bộ)
# ════════════════════════════════════════════════════════

def save_cer_score(session_id: str,
                   claim: float, evidence: float, reasoning: float) -> str:
    """Lấy turn_id mới nhất của session rồi lưu điểm CER."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id FROM debate_turns
            WHERE session_id = ?
            ORDER BY turn_number DESC LIMIT 1
        """, (session_id,)).fetchone()
        turn_id = row["id"]

        score_id = _uid()
        total = round((claim + evidence + reasoning) / 3, 2)
        conn.execute("""
            INSERT INTO cer_scores
              (id, turn_id, claim_score, evidence_score, reasoning_score, total_score, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (score_id, turn_id, claim, evidence, reasoning, total, _now()))
    return turn_id   # trả về để save_feedback dùng


# ════════════════════════════════════════════════════════
#  FEEDBACK  (lưu nội bộ)
# ════════════════════════════════════════════════════════

def save_feedback(turn_id: str,
                  strengths: list[str],
                  weaknesses: list[str],
                  suggestions: list[str]) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO feedback_items
              (id, turn_id, strengths, weaknesses, suggestions, created_at)
            VALUES (?,?,?,?,?,?)
        """, (_uid(), turn_id,
              json.dumps(strengths, ensure_ascii=False),
              json.dumps(weaknesses, ensure_ascii=False),
              json.dumps(suggestions, ensure_ascii=False),
              _now()))


# ════════════════════════════════════════════════════════
#  CONTENT FLAGS  (lưu nội bộ)
# ════════════════════════════════════════════════════════

def save_content_flag(turn_id: str,
                      is_flagged: bool = False,
                      flag_reason: str = "",
                      flagged_terms: list[str] = None) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO content_flags
              (id, turn_id, is_flagged, flag_reason, flagged_terms, created_at)
            VALUES (?,?,?,?,?,?)
        """, (_uid(), turn_id, int(is_flagged), flag_reason,
              json.dumps(flagged_terms or [], ensure_ascii=False), _now()))


# ════════════════════════════════════════════════════════
#  PROGRESS  (dashboard)
# ════════════════════════════════════════════════════════

def get_progress_summary() -> dict:
    """Tổng hợp tất cả phiên completed trong DB."""
    with get_connection() as conn:
        totals = conn.execute("""
            SELECT COUNT(*)              AS total_sessions,
                   AVG(overall_score)    AS overall_avg,
                   AVG(avg_claim_score)  AS claim_avg,
                   AVG(avg_evidence_score)   AS evidence_avg,
                   AVG(avg_reasoning_score)  AS reasoning_avg
            FROM debate_sessions WHERE status = 'completed'
        """).fetchone()

        recent = conn.execute("""
            SELECT session_id, topic, overall_score, created_at,
                   turn_count, difficulty, status
            FROM debate_sessions
            WHERE status = 'completed'
            ORDER BY created_at DESC LIMIT 10
        """).fetchall()

    return {
        "total_sessions": totals["total_sessions"] or 0,
        "average_scores": {
            "overall":   round(totals["overall_avg"]   or 0, 2),
            "claim":     round(totals["claim_avg"]     or 0, 2),
            "evidence":  round(totals["evidence_avg"]  or 0, 2),
            "reasoning": round(totals["reasoning_avg"] or 0, 2),
        },
        "recent_sessions": [dict(r) for r in recent],
    }
