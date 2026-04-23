"""
AI Debate Trainer — Database v2
Schema khớp với Pydantic models trong debate.py:
  - debate_sessions  ← StartSessionRequest / StartSessionResponse / SessionInfoResponse
  - debate_turns     ← DebateTurnRequest / DebateTurnResponse
  - cer_scores       ← lưu nội bộ, không expose qua Pydantic response
  - feedback_items   ← lưu nội bộ
  - content_flags    ← lưu nội bộ
"""

import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "debate_trainer_v2.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    conn.executescript("""

    -- ──────────────────────────────────────────
    --  debate_sessions
    --  Ánh xạ trực tiếp từ StartSessionRequest /
    --  StartSessionResponse / SessionInfoResponse
    -- ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS debate_sessions (
        session_id   TEXT PRIMARY KEY,
        topic        TEXT NOT NULL,          -- lưu thẳng chuỗi, không FK
        stance       TEXT NOT NULL,          -- "Ủng hộ" | "Phản đối" | "Trung lập"
        difficulty   TEXT NOT NULL,          -- "Cơ bản" | "Trung bình" | "Nâng cao"
        input_mode   TEXT NOT NULL DEFAULT 'text',
        status       TEXT NOT NULL DEFAULT 'active',
        turn_count   INTEGER NOT NULL DEFAULT 0,
        max_turns    INTEGER NOT NULL DEFAULT 5,
        -- điểm tổng kết (tính khi end_session)
        avg_claim_score     REAL,
        avg_evidence_score  REAL,
        avg_reasoning_score REAL,
        overall_score       REAL,
        created_at   TEXT NOT NULL,
        ended_at     TEXT
    );

    -- ──────────────────────────────────────────
    --  debate_turns
    --  Ánh xạ từ DebateTurnRequest / DebateTurnResponse
    --  Dùng đúng tên field "ai_rebuttal"
    -- ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS debate_turns (
        id                  TEXT PRIMARY KEY,
        session_id          TEXT NOT NULL REFERENCES debate_sessions(session_id),
        turn_number         INTEGER NOT NULL,
        user_argument       TEXT NOT NULL,   -- từ DebateTurnRequest
        ai_rebuttal         TEXT,            -- từ DebateTurnResponse (đổi tên)
        ai_word_count       INTEGER,
        processing_time_ms  INTEGER,
        is_safe             INTEGER NOT NULL DEFAULT 1,
        created_at          TEXT NOT NULL
    );

    -- ──────────────────────────────────────────
    --  cer_scores  (lưu nội bộ — không trong Pydantic)
    -- ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS cer_scores (
        id              TEXT PRIMARY KEY,
        turn_id         TEXT NOT NULL UNIQUE REFERENCES debate_turns(id),
        claim_score     REAL NOT NULL CHECK(claim_score BETWEEN 0 AND 10),
        evidence_score  REAL NOT NULL CHECK(evidence_score BETWEEN 0 AND 10),
        reasoning_score REAL NOT NULL CHECK(reasoning_score BETWEEN 0 AND 10),
        total_score     REAL NOT NULL CHECK(total_score BETWEEN 0 AND 10),
        created_at      TEXT NOT NULL
    );

    -- ──────────────────────────────────────────
    --  feedback_items  (lưu nội bộ)
    -- ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS feedback_items (
        id           TEXT PRIMARY KEY,
        turn_id      TEXT NOT NULL UNIQUE REFERENCES debate_turns(id),
        strengths    TEXT NOT NULL DEFAULT '[]',   -- JSON array
        weaknesses   TEXT NOT NULL DEFAULT '[]',
        suggestions  TEXT NOT NULL DEFAULT '[]',
        raw_feedback TEXT,
        created_at   TEXT NOT NULL
    );

    -- ──────────────────────────────────────────
    --  content_flags  (lưu nội bộ)
    -- ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS content_flags (
        id            TEXT PRIMARY KEY,
        turn_id       TEXT NOT NULL UNIQUE REFERENCES debate_turns(id),
        is_flagged    INTEGER NOT NULL DEFAULT 0,
        flag_reason   TEXT,
        flagged_terms TEXT NOT NULL DEFAULT '[]',
        created_at    TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_turns_session ON debate_turns(session_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON debate_sessions(status);
    """)
    conn.commit()
    conn.close()
    print("✓ Schema v2 đã sẵn sàng.")
