import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.services.cer_scorer import normalize_cer_to_100


SESSION_MIGRATIONS = {
    "user_id": "TEXT REFERENCES users(id)",
    "topic_category": "TEXT",
    "custom_topic": "TEXT",
    "age_group": "TEXT NOT NULL DEFAULT 'adult'",
    "debate_level": "TEXT NOT NULL DEFAULT 'intermediate'",
    "coach_model": "TEXT NOT NULL DEFAULT 'socratic_v3'",
    "language": "TEXT NOT NULL DEFAULT 'vi'",
    "response_time": "TEXT",
    "display_name": "TEXT",
}

DEMO_USER_ID = "demo-user"
DEMO_USER_EMAIL = "guest@ai-debate-trainer.local"


def _connect():
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def _connection():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _row_to_dict(row):
    return dict(row) if row else None


def _rows_to_dicts(rows):
    return [dict(row) for row in rows]


def _ensure_demo_user_row(connection):
    connection.execute(
        """
        INSERT OR IGNORE INTO users (
            id,
            email,
            password_hash,
            display_name,
            age_group,
            debate_level,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEMO_USER_ID,
            DEMO_USER_EMAIL,
            "demo-not-for-login",
            "Guest",
            "adult",
            "intermediate",
            "vi",
        ),
    )


def _migrate_debate_sessions(connection):
    existing_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(debate_sessions)").fetchall()
    }
    for column_name, definition in SESSION_MIGRATIONS.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE debate_sessions ADD COLUMN {column_name} {definition}"
            )

    connection.execute(
        """
        UPDATE debate_sessions
        SET status = CASE
            WHEN status IN ('ready', 'found', 'success') THEN 'active'
            WHEN status IN ('complete', 'done') THEN 'completed'
            WHEN status = 'error' THEN 'error'
            ELSE COALESCE(NULLIF(status, ''), 'active')
        END,
            input_mode = COALESCE(NULLIF(input_mode, ''), 'text'),
            age_group = COALESCE(NULLIF(age_group, ''), 'adult'),
            debate_level = COALESCE(NULLIF(debate_level, ''), 'intermediate'),
            coach_model = COALESCE(NULLIF(coach_model, ''), 'socratic_v3'),
            language = COALESCE(NULLIF(language, ''), 'vi'),
            difficulty = CASE
                WHEN lower(COALESCE(difficulty, '')) IN ('basic', 'easy', 'beginner') THEN 'Cơ bản'
                WHEN lower(COALESCE(difficulty, '')) IN ('intermediate', 'medium') THEN 'Trung bình'
                WHEN lower(COALESCE(difficulty, '')) IN ('advanced', 'hard', 'expert') THEN 'Nâng cao'
                ELSE COALESCE(NULLIF(difficulty, ''), 'Trung bình')
            END,
            max_turns = CASE WHEN max_turns < 1 THEN ? ELSE max_turns END
        """,
        (settings.DEFAULT_MAX_TURNS,),
    )
    connection.execute(
        """
        UPDATE debate_sessions
        SET user_id = ?
        WHERE user_id IS NULL OR user_id = ''
        """,
        (DEMO_USER_ID,),
    )


def init_db():
    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                age_group TEXT,
                debate_level TEXT,
                language TEXT NOT NULL DEFAULT 'vi',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS debate_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                topic_category TEXT,
                custom_topic TEXT,
                stance TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                input_mode TEXT NOT NULL,
                age_group TEXT NOT NULL DEFAULT 'adult',
                debate_level TEXT NOT NULL DEFAULT 'intermediate',
                coach_model TEXT NOT NULL DEFAULT 'socratic_v3',
                language TEXT NOT NULL DEFAULT 'vi',
                response_time TEXT,
                display_name TEXT,
                status TEXT NOT NULL,
                turn_count INTEGER NOT NULL DEFAULT 0,
                max_turns INTEGER NOT NULL DEFAULT 5,
                average_score REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS debate_turns (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                user_argument TEXT NOT NULL,
                ai_rebuttal TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES debate_sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS cer_scores (
                score_id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL,
                claim REAL NOT NULL,
                evidence REAL NOT NULL,
                reasoning REAL NOT NULL,
                total REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turn_id) REFERENCES debate_turns(turn_id)
            );

            CREATE TABLE IF NOT EXISTS feedback_items (
                feedback_id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turn_id) REFERENCES debate_turns(turn_id)
            );

            CREATE TABLE IF NOT EXISTS content_flags (
                flag_id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL,
                flag_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turn_id) REFERENCES debate_turns(turn_id)
            );
            """
        )
        _ensure_demo_user_row(connection)
        _migrate_debate_sessions(connection)


def create_user(
    email: str,
    password_hash: str,
    display_name: str,
    age_group: str,
    debate_level: str,
    language: str,
):
    init_db()
    user_id = str(uuid4())
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO users (
                id, email, password_hash, display_name, age_group, debate_level, language
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email,
                password_hash,
                display_name,
                age_group,
                debate_level,
                language,
            ),
        )
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_dict(row)


def get_user_by_email(email: str):
    init_db()
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    return _row_to_dict(row)


def get_user_by_id(user_id: str):
    init_db()
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_dict(row)


def get_demo_user():
    init_db()
    return get_user_by_id(DEMO_USER_ID)


def create_auth_session(user_id: str, token: str, expires_at: str | None = None):
    init_db()
    session_id = str(uuid4())
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO auth_sessions (
                id, user_id, token, expires_at, is_active
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (session_id, user_id, token, expires_at),
        )
        row = connection.execute(
            """
            SELECT
                auth_sessions.*,
                users.email,
                users.display_name,
                users.age_group,
                users.debate_level,
                users.language
            FROM auth_sessions
            JOIN users ON users.id = auth_sessions.user_id
            WHERE auth_sessions.id = ?
            """,
            (session_id,),
        ).fetchone()
    return _row_to_dict(row)


def get_auth_session_by_token(token: str):
    init_db()
    with _connection() as connection:
        row = connection.execute(
            """
            SELECT
                auth_sessions.*,
                users.email,
                users.display_name,
                users.age_group,
                users.debate_level,
                users.language
            FROM auth_sessions
            JOIN users ON users.id = auth_sessions.user_id
            WHERE auth_sessions.token = ?
            """,
            (token,),
        ).fetchone()
    return _row_to_dict(row)


def deactivate_auth_session(token: str):
    init_db()
    with _connection() as connection:
        connection.execute(
            """
            UPDATE auth_sessions
            SET is_active = 0
            WHERE token = ?
            """,
            (token,),
        )
        row = connection.execute(
            "SELECT * FROM auth_sessions WHERE token = ?",
            (token,),
        ).fetchone()
    return _row_to_dict(row)


def create_session(
    user_id: str,
    topic: str,
    stance: str,
    difficulty: str,
    input_mode: str,
    topic_category: str | None = None,
    custom_topic: str | None = None,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    response_time: str | None = None,
    max_turns: int | None = None,
    display_name: str | None = None,
):
    init_db()
    session_id = str(uuid4())
    resolved_max_turns = int(max_turns or settings.DEFAULT_MAX_TURNS)

    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO debate_sessions (
                session_id,
                user_id,
                topic,
                topic_category,
                custom_topic,
                stance,
                difficulty,
                input_mode,
                age_group,
                debate_level,
                coach_model,
                language,
                response_time,
                display_name,
                status,
                max_turns
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                topic,
                topic_category,
                custom_topic,
                stance,
                difficulty,
                input_mode,
                age_group,
                debate_level,
                coach_model,
                language,
                response_time,
                display_name,
                "active",
                resolved_max_turns,
            ),
        )

        row = connection.execute(
            "SELECT * FROM debate_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

    return _row_to_dict(row)


def get_session(session_id: str, user_id: str | None = None):
    init_db()
    with _connection() as connection:
        if user_id is None:
            row = connection.execute(
                "SELECT * FROM debate_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT * FROM debate_sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
    return _row_to_dict(row)


def end_session(session_id: str, user_id: str | None = None):
    init_db()
    with _connection() as connection:
        if user_id is None:
            row = connection.execute(
                "SELECT * FROM debate_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT * FROM debate_sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
        if not row:
            return None

        if user_id is None:
            connection.execute(
                """
                UPDATE debate_sessions
                SET status = 'completed',
                    average_score = (
                        SELECT AVG(total)
                        FROM cer_scores
                        JOIN debate_turns ON debate_turns.turn_id = cer_scores.turn_id
                        WHERE debate_turns.session_id = ?
                    ),
                    updated_at = CURRENT_TIMESTAMP,
                    completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                WHERE session_id = ?
                """,
                (session_id, session_id),
            )
        else:
            connection.execute(
                """
                UPDATE debate_sessions
                SET status = 'completed',
                    average_score = (
                        SELECT AVG(total)
                        FROM cer_scores
                        JOIN debate_turns ON debate_turns.turn_id = cer_scores.turn_id
                        WHERE debate_turns.session_id = ?
                    ),
                    updated_at = CURRENT_TIMESTAMP,
                    completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                WHERE session_id = ? AND user_id = ?
                """,
                (session_id, session_id, user_id),
            )
        updated = connection.execute(
            "SELECT * FROM debate_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

    return _row_to_dict(updated)


def save_debate_turn(
    session: dict,
    user_argument: str,
    ai_rebuttal: str,
    cer: dict,
    feedback: dict,
    content_flags: list | None = None,
    status: str = "active",
    count_for_completion: bool = True,
):
    init_db()
    turn_id = str(uuid4())
    session_id = session["session_id"]
    turn_number = int(session.get("turn_count", 0)) + 1
    cer = normalize_cer_to_100(cer)
    total_score = float(cer.get("total", 0.0))
    flags = content_flags or []

    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO debate_turns (
                turn_id, session_id, turn_number, user_argument, ai_rebuttal, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (turn_id, session_id, turn_number, user_argument, ai_rebuttal, status),
        )

        connection.execute(
            """
            INSERT INTO cer_scores (
                score_id, turn_id, claim, evidence, reasoning, total
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                turn_id,
                float(cer.get("claim", 0.0)),
                float(cer.get("evidence", 0.0)),
                float(cer.get("reasoning", 0.0)),
                total_score,
            ),
        )

        for category in ("strengths", "weaknesses", "suggestions"):
            for message in feedback.get(category, []):
                connection.execute(
                    """
                    INSERT INTO feedback_items (
                        feedback_id, turn_id, category, message
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(uuid4()), turn_id, category, str(message)),
                )

        for flag in flags:
            connection.execute(
                """
                INSERT INTO content_flags (
                    flag_id, turn_id, flag_type, severity, message
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    turn_id,
                    flag.get("type", "ai_error"),
                    flag.get("severity", "low"),
                    flag.get("message", ""),
                ),
            )

        next_turn_count = turn_number if count_for_completion else int(session.get("turn_count", 0))
        next_status = (
            "completed"
            if count_for_completion and next_turn_count >= int(session["max_turns"])
            else "active"
        )
        connection.execute(
            """
            UPDATE debate_sessions
            SET status = ?,
                turn_count = ?,
                average_score = (
                    SELECT AVG(total)
                    FROM cer_scores
                    JOIN debate_turns ON debate_turns.turn_id = cer_scores.turn_id
                    WHERE debate_turns.session_id = ?
                ),
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE
                    WHEN ? = 'completed' THEN COALESCE(completed_at, CURRENT_TIMESTAMP)
                    ELSE completed_at
                END
            WHERE session_id = ?
            """,
            (next_status, next_turn_count, session_id, next_status, session_id),
        )

        updated_session = connection.execute(
            "SELECT * FROM debate_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

    return {
        "turn_id": turn_id,
        "turn_number": turn_number,
        "session": _row_to_dict(updated_session),
    }


def get_session_turns(session_id: str):
    init_db()
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT
                debate_turns.turn_id,
                debate_turns.turn_number,
                debate_turns.user_argument,
                debate_turns.ai_rebuttal,
                debate_turns.status,
                debate_turns.created_at,
                COALESCE(cer_scores.claim, 0.0) AS claim,
                COALESCE(cer_scores.evidence, 0.0) AS evidence,
                COALESCE(cer_scores.reasoning, 0.0) AS reasoning,
                COALESCE(cer_scores.total, 0.0) AS total
            FROM debate_turns
            LEFT JOIN cer_scores ON cer_scores.turn_id = debate_turns.turn_id
            WHERE debate_turns.session_id = ?
            ORDER BY debate_turns.turn_number ASC, debate_turns.created_at ASC
            """,
            (session_id,),
        ).fetchall()
        turns = _rows_to_dicts(rows)

        feedback_rows = connection.execute(
            """
            SELECT
                feedback_items.turn_id,
                feedback_items.category,
                feedback_items.message
            FROM feedback_items
            JOIN debate_turns ON debate_turns.turn_id = feedback_items.turn_id
            WHERE debate_turns.session_id = ?
            ORDER BY feedback_items.created_at ASC
            """,
            (session_id,),
        ).fetchall()

    feedback_by_turn = {
        turn["turn_id"]: {"strengths": [], "weaknesses": [], "suggestions": []}
        for turn in turns
    }
    for row in feedback_rows:
        category = row["category"]
        if category in feedback_by_turn.get(row["turn_id"], {}):
            feedback_by_turn[row["turn_id"]][category].append(row["message"])

    for turn in turns:
        turn["cer"] = normalize_cer_to_100({
            "claim": float(turn.pop("claim")),
            "evidence": float(turn.pop("evidence")),
            "reasoning": float(turn.pop("reasoning")),
            "total": float(turn.pop("total")),
        })
        turn["feedback"] = feedback_by_turn[turn["turn_id"]]

    return turns


def _unique_first(items: list[str], limit: int = 5) -> list[str]:
    seen = set()
    unique = []
    for item in items:
        clean = str(item).strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            unique.append(clean)
        if len(unique) >= limit:
            break
    return unique


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def get_session_summary(session_id: str, user_id: str | None = None):
    session = get_session(session_id, user_id=user_id)
    if not session:
        return None

    turns = get_session_turns(session_id)
    scored_turns = [turn for turn in turns if turn["status"] not in ("error", "invalid")]
    cer_scores = [turn["cer"] for turn in scored_turns]
    strengths = []
    weaknesses = []
    suggestions = []
    for turn in turns:
        strengths.extend(turn["feedback"]["strengths"])
        weaknesses.extend(turn["feedback"]["weaknesses"])
        suggestions.extend(turn["feedback"]["suggestions"])

    return {
        "session_id": session["session_id"],
        "topic": session["topic"],
        "stance": session["stance"],
        "difficulty": session["difficulty"],
        "turn_count": int(session["turn_count"]),
        "max_turns": int(session["max_turns"]),
        "status": session["status"],
        "avg_claim_score": _average([score["claim"] for score in cer_scores]),
        "avg_evidence_score": _average([score["evidence"] for score in cer_scores]),
        "avg_reasoning_score": _average([score["reasoning"] for score in cer_scores]),
        "overall_score": _average([score["total"] for score in cer_scores]),
        "strength_summary": _unique_first(strengths),
        "weakness_summary": _unique_first(weaknesses),
        "next_steps": _unique_first(suggestions),
    }


def _skill_label(scores: dict[str, float], pick_highest: bool) -> str:
    if not scores:
        return ""
    picker = max if pick_highest else min
    key = picker(scores, key=scores.get)
    return key.replace("_score", "")


def _streak_days(completed_days: list[str]) -> int:
    parsed_days = {
        date.fromisoformat(day)
        for day in completed_days
        if day
    }
    if not parsed_days:
        return 0

    cursor = max(parsed_days)
    streak = 0
    while cursor in parsed_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_progress_overview(user_id: str | None = None):
    init_db()
    with _connection() as connection:
        user_filter = "" if user_id is None else "WHERE user_id = ?"
        params = () if user_id is None else (user_id,)
        counts = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_sessions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_sessions
            FROM debate_sessions
            {user_filter}
            """,
            params,
        ).fetchone()
        averages = connection.execute(
            f"""
            SELECT
                AVG(CASE WHEN cer_scores.claim > 0 AND cer_scores.claim <= 1 THEN cer_scores.claim * 100.0 ELSE cer_scores.claim END) AS avg_claim_score,
                AVG(CASE WHEN cer_scores.evidence > 0 AND cer_scores.evidence <= 1 THEN cer_scores.evidence * 100.0 ELSE cer_scores.evidence END) AS avg_evidence_score,
                AVG(CASE WHEN cer_scores.reasoning > 0 AND cer_scores.reasoning <= 1 THEN cer_scores.reasoning * 100.0 ELSE cer_scores.reasoning END) AS avg_reasoning_score,
                AVG(CASE WHEN cer_scores.total > 0 AND cer_scores.total <= 1 THEN cer_scores.total * 100.0 ELSE cer_scores.total END) AS overall_score
            FROM cer_scores
            JOIN debate_turns ON debate_turns.turn_id = cer_scores.turn_id
            JOIN debate_sessions ON debate_sessions.session_id = debate_turns.session_id
            WHERE debate_turns.status NOT IN ('error', 'invalid')
            {"AND debate_sessions.user_id = ?" if user_id is not None else ""}
            """,
            params,
        ).fetchone()
        topics = connection.execute(
            f"""
            SELECT topic
            FROM debate_sessions
            WHERE COALESCE(topic, '') != ''
            {"AND user_id = ?" if user_id is not None else ""}
            ORDER BY created_at DESC
            LIMIT 5
            """,
            params,
        ).fetchall()
        completed_days = connection.execute(
            f"""
            SELECT DISTINCT DATE(completed_at) AS completed_day
            FROM debate_sessions
            WHERE completed_at IS NOT NULL
            {"AND user_id = ?" if user_id is not None else ""}
            ORDER BY completed_day DESC
            """,
            params,
        ).fetchall()

    scores = {
        "claim_score": round(float(averages["avg_claim_score"] or 0.0), 2),
        "evidence_score": round(float(averages["avg_evidence_score"] or 0.0), 2),
        "reasoning_score": round(float(averages["avg_reasoning_score"] or 0.0), 2),
    }

    return {
        "total_sessions": int(counts["total_sessions"] or 0),
        "completed_sessions": int(counts["completed_sessions"] or 0),
        "avg_claim_score": scores["claim_score"],
        "avg_evidence_score": scores["evidence_score"],
        "avg_reasoning_score": scores["reasoning_score"],
        "overall_score": round(float(averages["overall_score"] or 0.0), 2),
        "streak_days": _streak_days([row["completed_day"] for row in completed_days]),
        "recent_topics": [row["topic"] for row in topics],
        "skill_strength": _skill_label(scores, pick_highest=True),
        "skill_weakness": _skill_label(scores, pick_highest=False),
    }
