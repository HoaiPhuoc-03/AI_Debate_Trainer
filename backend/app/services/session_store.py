"""
session_store.py — Firebase Firestore backend
=============================================
Replaces the SQLite implementation.  All public function signatures and
return shapes are preserved so the rest of the app requires no changes.

Firestore collections
---------------------
  users            – one document per user (doc id = user_id)
  auth_sessions    – one document per session (doc id = session_id)
  debate_sessions  – one document per debate (doc id = session_id)
  debate_turns     – one document per turn  (doc id = turn_id)
  cer_scores       – one document per score (doc id = score_id)
  feedback_items   – one document per item  (doc id = feedback_id)
  content_flags    – one document per flag  (doc id = flag_id)

Required Firestore composite indexes
-------------------------------------
  debate_turns     : session_id ASC, turn_number ASC
  feedback_items   : turn_id    ASC, created_at   ASC
  debate_sessions  : user_id    ASC, created_at   DESC  (for get_progress_overview)

Install
-------
  pip install firebase-admin

Configuration (add to settings)
--------------------------------
  FIREBASE_CREDENTIALS_PATH  – path to service-account JSON (optional when
                               running on Google Cloud with a default identity)
  FIREBASE_PROJECT_ID        – only needed when credentials don't embed the
                               project id (e.g. Application Default Credentials)
"""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
import json
import os

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter

from app.core.config import settings
from app.services.cer_scorer import normalize_cer_to_100
from app.services.memory_utils import (
    default_user_memory,
    merge_user_memory,
    normalize_memory_mode,
    update_memory_after_turn,
)
from app.services.store_factory import get_store


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEMO_USER_ID = "demo-user"
DEMO_USER_EMAIL = "guest@ai-debate-trainer.local"


# ---------------------------------------------------------------------------
# Firebase initialisation (lazy, safe for repeated calls)
# ---------------------------------------------------------------------------

def _db() -> firestore.Client:
    if not firebase_admin._apps:
        raw_json = settings.FIREBASE_CREDENTIALS_JSON
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        project_id = settings.FIREBASE_PROJECT_ID
        options = {"projectId": project_id} if project_id else {}

        if raw_json:
            cred = credentials.Certificate(json.loads(raw_json))
            firebase_admin.initialize_app(cred, options)
        elif cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, options)
        else:
            raise RuntimeError(
                "Firebase credentials not configured. "
                "Set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH in your .env file."
            )

    return firestore.client()

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """UTC datetime object representing the current time."""
    return datetime.now(timezone.utc)


def _parse_datetime(val) -> datetime | None:
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    # If string:
    try:
        val_str = str(val).strip()
        if " " in val_str:
            return datetime.strptime(val_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(val_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _parse_date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    # If string:
    try:
        val_str = str(val).strip()
        dt = _parse_datetime(val_str)
        if dt:
            return dt.date()
        return date.fromisoformat(val_str[:10])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pure-Python helpers (unchanged from the SQLite version)
# ---------------------------------------------------------------------------

def _unique_first(items: list[str], limit: int = 5) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
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


def _skill_label(scores: dict[str, float], pick_highest: bool) -> str:
    if not scores:
        return ""
    picker = max if pick_highest else min
    key = picker(scores, key=scores.get)
    return key.replace("_score", "")


def _streak_days(completed_days: list) -> int:
    parsed_days = {d for d in (_parse_date(day) for day in completed_days) if d}
    if not parsed_days:
        return 0
    cursor = max(parsed_days)
    streak = 0
    while cursor in parsed_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak



def _normalize_score_value(value: float) -> float:
    """Mirror the SQLite CASE: values in (0, 1] are treated as fractions → ×100."""
    if 0 < value <= 1:
        return value * 100.0
    return value


def _normalize_difficulty(difficulty: str) -> str:
    low = (difficulty or "").lower()
    if low in ("basic", "easy", "beginner"):
        return "Cơ bản"
    if low in ("intermediate", "medium"):
        return "Trung bình"
    if low in ("advanced", "hard", "expert"):
        return "Nâng cao"
    return difficulty or "Trung bình"


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def _ensure_demo_user() -> None:
    db = _db()
    ref = db.collection("users").document(DEMO_USER_ID)
    if not ref.get().exists:
        ref.set({
            "id": DEMO_USER_ID,
            "email": DEMO_USER_EMAIL,
            "password_hash": "demo-not-for-login",
            "display_name": "Guest",
            "age_group": "adult",
            "debate_level": "intermediate",
            "language": "vi",
            "created_at": _now(),
        })


def _firebase_init_db() -> None:
    """
    Initialise Firestore and seed the demo user.

    Firestore is schemaless, so there is no DDL or migration to run.
    This function is intentionally cheap to call multiple times.
    """
    try:
        _db()
        _ensure_demo_user()
    except Exception as e:
        import sys
        print(f"ERROR during init_db (e.g. Firestore Quota Exceeded): {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _firebase_create_user(
    email: str,
    password_hash: str,
    display_name: str,
    age_group: str,
    debate_level: str,
    language: str,
) -> dict:
    init_db()
    user_id = str(uuid4())
    data = {
        "id": user_id,
        "email": email,
        "password_hash": password_hash,
        "display_name": display_name,
        "age_group": age_group,
        "debate_level": debate_level,
        "language": language,
        "created_at": _now(),
    }
    _db().collection("users").document(user_id).set(data)
    return data


def _firebase_get_user_by_email(email: str) -> dict | None:
    init_db()
    docs = (
        _db()
        .collection("users")
        .where(filter=FieldFilter("email", "==", email))
        .limit(1)
        .get()
    )
    return docs[0].to_dict() if docs else None


def _firebase_get_user_by_id(user_id: str) -> dict | None:
    init_db()
    doc = _db().collection("users").document(user_id).get()
    return doc.to_dict() if doc.exists else None


def _firebase_get_demo_user() -> dict | None:
    init_db()
    return _firebase_get_user_by_id(DEMO_USER_ID)


# ---------------------------------------------------------------------------
# Auth sessions
# ---------------------------------------------------------------------------

def _enrich_auth_session(session_data: dict) -> dict:
    """
    Merge user profile fields into an auth-session dict.
    Replicates the JOIN on users done in the SQLite version.
    """
    user = _firebase_get_user_by_id(session_data["user_id"]) or {}
    return {
        **session_data,
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "age_group": user.get("age_group"),
        "debate_level": user.get("debate_level"),
        "language": user.get("language"),
    }


def _firebase_create_auth_session(
    user_id: str,
    token: str,
    expires_at: datetime | str | None = None,
) -> dict:
    init_db()
    session_id = str(uuid4())
    data = {
        "id": session_id,
        "user_id": user_id,
        "token": token,
        "created_at": _now(),
        "expires_at": _parse_datetime(expires_at),
        "is_active": 1,
    }
    _db().collection("auth_sessions").document(session_id).set(data)
    return _enrich_auth_session(data)


def _firebase_get_auth_session_by_token(token: str) -> dict | None:
    init_db()
    docs = (
        _db()
        .collection("auth_sessions")
        .where(filter=FieldFilter("token", "==", token))
        .limit(1)
        .get()
    )
    if not docs:
        return None
    return _enrich_auth_session(docs[0].to_dict())


def _firebase_deactivate_auth_session(token: str) -> dict | None:
    init_db()
    db = _db()
    docs = (
        db.collection("auth_sessions")
        .where(filter=FieldFilter("token", "==", token))
        .limit(1)
        .get()
    )
    if not docs:
        return None
    doc_ref = docs[0].reference
    doc_ref.update({"is_active": 0})
    return doc_ref.get().to_dict()


# ---------------------------------------------------------------------------
# Debate sessions
# ---------------------------------------------------------------------------

def _compute_session_avg_score(db: firestore.Client, session_id: str) -> float | None:
    """
    Compute the average CER total across all turns in a session.
    Mirrors the correlated sub-select used in the SQLite UPDATE statements.
    """
    turn_docs = (
        db.collection("debate_turns")
        .where(filter=FieldFilter("session_id", "==", session_id))
        .get()
    )
    turn_ids = [d.to_dict()["turn_id"] for d in turn_docs]
    if not turn_ids:
        return None

    totals: list[float] = []
    for tid in turn_ids:
        score_docs = (
            db.collection("cer_scores")
            .where(filter=FieldFilter("turn_id", "==", tid))
            .limit(1)
            .get()
        )
        if score_docs:
            totals.append(float(score_docs[0].to_dict().get("total", 0.0)))

    return round(sum(totals) / len(totals), 6) if totals else None


def _firebase_create_session(
    user_id: str,
    topic: str,
    stance: str,
    difficulty: str,
    input_mode: str,
    topic_id: str | None = None,
    topic_category: str | None = None,
    topic_tags: list[str] | None = None,
    custom_topic: str | None = None,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    mode: str = "free_debate",
    response_time: str | None = None,
    max_turns: int | None = None,
    display_name: str | None = None,
) -> dict:
    init_db()
    session_id = str(uuid4())
    resolved_max_turns = int(max_turns or settings.DEFAULT_MAX_TURNS)
    now = _now()
    data = {
        "session_id": session_id,
        "user_id": user_id,
        "topic": topic,
        "topic_id": topic_id,
        "topic_category": topic_category,
        "topic_tags": topic_tags,
        "custom_topic": custom_topic,
        "stance": stance,
        "difficulty": _normalize_difficulty(difficulty),
        "input_mode": input_mode or "text",
        "age_group": age_group or "adult",
        "debate_level": debate_level or "intermediate",
        "coach_model": coach_model or "socratic_v3",
        "language": language or "vi",
        "mode": mode or "free_debate",
        "response_time": response_time,
        "display_name": display_name,
        "status": "active",
        "turn_count": 0,
        "max_turns": resolved_max_turns,
        "average_score": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    _db().collection("debate_sessions").document(session_id).set(data)
    return data


def _firebase_get_session(session_id: str, user_id: str | None = None) -> dict | None:
    init_db()
    doc = _db().collection("debate_sessions").document(session_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if user_id is not None and data.get("user_id") != user_id:
        return None
    return data


def _firebase_end_session(session_id: str, user_id: str | None = None) -> dict | None:
    init_db()
    db = _db()
    doc_ref = db.collection("debate_sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if user_id is not None and data.get("user_id") != user_id:
        return None

    now = _now()
    avg_score = _compute_session_avg_score(db, session_id)
    doc_ref.update({
        "status": "completed",
        "average_score": avg_score,
        "updated_at": now,
        "completed_at": _parse_datetime(data.get("completed_at")) or now,
    })
    return doc_ref.get().to_dict()


# ---------------------------------------------------------------------------
# Debate turns
# ---------------------------------------------------------------------------

def _firebase_save_debate_turn(
    session: dict,
    user_argument: str,
    ai_rebuttal: str,
    cer: dict,
    feedback: dict,
    mode_scores: dict | None = None,
    content_flags: list | None = None,
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_round: int | None = None,
    practice_prompt_id: str | None = None,
    status: str = "active",
    count_for_completion: bool = True,
    complete_session: bool = True,
) -> dict:
    _ = practice_prompt_id
    _firebase_init_db()
    db = _db()
    turn_id = str(uuid4())
    session_id = session["session_id"]
    turn_number = int(session.get("turn_count", 0)) + 1
    cer = normalize_cer_to_100(cer)
    flags = content_flags or []
    now = _now()
    turn_metadata = {
        "practice_prompt": practice_prompt,
        "practice_round": practice_round,
        "status": status,
    }
    if practice_mode == "quick_rebuttal" and mode_scores:
        turn_metadata["mode_scores"] = mode_scores
        turn_metadata["score_schema"] = "quick_rebuttal_v1"

    # ── atomic batch write for all sub-documents ───────────────────────────
    batch = db.batch()

    # debate_turns
    turn_ref = db.collection("debate_turns").document(turn_id)
    batch.set(turn_ref, {
        "turn_id": turn_id,
        "session_id": session_id,
        "turn_number": turn_number,
        "user_argument": user_argument,
        "ai_rebuttal": ai_rebuttal,
        "practice_mode": practice_mode,
        "practice_prompt": practice_prompt,
        "practice_round": practice_round,
        "status": status,
        "metadata": turn_metadata,
        "created_at": now,
    })

    # cer_scores
    score_id = str(uuid4())
    cer_ref = db.collection("cer_scores").document(score_id)
    batch.set(cer_ref, {
        "score_id": score_id,
        "turn_id": turn_id,
        "claim": float(cer.get("claim", 0.0)),
        "evidence": float(cer.get("evidence", 0.0)),
        "reasoning": float(cer.get("reasoning", 0.0)),
        "total": float(cer.get("total", 0.0)),
        "created_at": now,
    })

    # feedback_items
    for category in ("strengths", "weaknesses", "suggestions"):
        for message in feedback.get(category, []):
            feedback_id = str(uuid4())
            fb_ref = db.collection("feedback_items").document(feedback_id)
            batch.set(fb_ref, {
                "feedback_id": feedback_id,
                "turn_id": turn_id,
                "category": category,
                "message": str(message),
                "created_at": now,
            })

    # content_flags
    for flag in flags:
        flag_id = str(uuid4())
        flag_ref = db.collection("content_flags").document(flag_id)
        batch.set(flag_ref, {
            "flag_id": flag_id,
            "turn_id": turn_id,
            "flag_type": flag.get("type", "ai_error"),
            "severity": flag.get("severity", "low"),
            "message": flag.get("message", ""),
            "created_at": now,
        })

    batch.commit()

    # ── update parent debate_session ───────────────────────────────────────
    next_turn_count = (
        turn_number if count_for_completion else int(session.get("turn_count", 0))
    )
    next_status = (
        "completed"
        if complete_session and count_for_completion and next_turn_count >= int(session["max_turns"])
        else "active"
    )
    avg_score = _compute_session_avg_score(db, session_id)

    session_ref = db.collection("debate_sessions").document(session_id)
    session_updates: dict = {
        "status": next_status,
        "turn_count": next_turn_count,
        "average_score": avg_score,
        "updated_at": now,
    }
    if next_status == "completed":
        current = session_ref.get().to_dict() or {}
        session_updates["completed_at"] = _parse_datetime(current.get("completed_at")) or now

    session_ref.update(session_updates)
    updated_session = session_ref.get().to_dict()

    return {
        "turn_id": turn_id,
        "turn_number": turn_number,
        "session": updated_session,
    }


def _firebase_get_session_turns(session_id: str) -> list[dict]:
    init_db()
    db = _db()

    # Requires composite index: session_id ASC, turn_number ASC
    turn_docs = (
        db.collection("debate_turns")
        .where(filter=FieldFilter("session_id", "==", session_id))
        .order_by("turn_number")
        .get()
    )
    turns = [d.to_dict() for d in turn_docs]
    if not turns:
        return []

    turn_ids = [t["turn_id"] for t in turns]

    # Fetch cer_scores keyed by turn_id
    cer_by_turn: dict[str, dict] = {}
    for tid in turn_ids:
        docs = (
            db.collection("cer_scores")
            .where(filter=FieldFilter("turn_id", "==", tid))
            .limit(1)
            .get()
        )
        if docs:
            cer_by_turn[tid] = docs[0].to_dict()

    # Fetch feedback_items grouped by turn_id
    # Requires composite index: turn_id ASC, created_at ASC
    feedback_by_turn: dict[str, dict] = {
        tid: {"strengths": [], "weaknesses": [], "suggestions": []}
        for tid in turn_ids
    }
    for tid in turn_ids:
        fb_docs = (
            db.collection("feedback_items")
            .where(filter=FieldFilter("turn_id", "==", tid))
            .order_by("created_at")
            .get()
        )
        for fb_doc in fb_docs:
            fb = fb_doc.to_dict()
            cat = fb.get("category")
            if cat in feedback_by_turn[tid]:
                feedback_by_turn[tid][cat].append(fb["message"])

    # Attach cer and feedback to each turn
    for turn in turns:
        tid = turn["turn_id"]
        raw = cer_by_turn.get(tid, {})
        turn["cer"] = normalize_cer_to_100({
            "claim":     float(raw.get("claim",     0.0)),
            "evidence":  float(raw.get("evidence",  0.0)),
            "reasoning": float(raw.get("reasoning", 0.0)),
            "total":     float(raw.get("total",     0.0)),
        })
        metadata = dict(turn.get("metadata") or {})
        turn["mode_scores"] = metadata.get("mode_scores")
        turn["score_schema"] = metadata.get("score_schema")
        turn["feedback"] = feedback_by_turn[tid]

    return turns


# ---------------------------------------------------------------------------
# Summaries and progress
# ---------------------------------------------------------------------------

def _firebase_get_session_summary(session_id: str, user_id: str | None = None) -> dict | None:
    session = _firebase_get_session(session_id, user_id=user_id)
    if not session:
        return None

    turns = _firebase_get_session_turns(session_id)
    scored_turns = [t for t in turns if t["status"] not in ("error", "invalid")]
    cer_scores = [t["cer"] for t in scored_turns]
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    for turn in turns:
        strengths.extend(turn["feedback"]["strengths"])
        weaknesses.extend(turn["feedback"]["weaknesses"])
        suggestions.extend(turn["feedback"]["suggestions"])

    return {
        "session_id":         session["session_id"],
        "topic":              session["topic"],
        "stance":             session["stance"],
        "difficulty":         session["difficulty"],
        "turn_count":         int(session["turn_count"]),
        "max_turns":          int(session["max_turns"]),
        "status":             session["status"],
        "avg_claim_score":    _average([s["claim"]     for s in cer_scores]),
        "avg_evidence_score": _average([s["evidence"]  for s in cer_scores]),
        "avg_reasoning_score":_average([s["reasoning"] for s in cer_scores]),
        "overall_score":      _average([s["total"]     for s in cer_scores]),
        "strength_summary":   _unique_first(strengths),
        "weakness_summary":   _unique_first(weaknesses),
        "next_steps":         _unique_first(suggestions),
    }


def _firebase_get_progress_overview(user_id: str | None = None) -> dict:
    init_db()
    db = _db()

    # ── fetch all relevant debate sessions ─────────────────────────────────
    sessions_ref = db.collection("debate_sessions")
    if user_id is not None:
        sessions_ref = sessions_ref.where(filter=FieldFilter("user_id", "==", user_id))
    sessions = [d.to_dict() for d in sessions_ref.get()]

    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.get("status") == "completed")

    def _created_at_sort_key(s: dict) -> datetime:
        dt = _parse_datetime(s.get("created_at"))
        return dt or datetime.min.replace(tzinfo=timezone.utc)

    # Recent sessions (up to 5, newest first, non-empty)
    recent_sessions = sorted(
        [s for s in sessions if s.get("topic")],
        key=_created_at_sort_key,
        reverse=True,
    )

    now = _now()
    week_cutoff = now - timedelta(days=7)
    month_cutoff = now - timedelta(days=30)

    # Unique completed calendar days for streak calculation
    completed_days = list({
        s["completed_at"]
        for s in sessions
        if s.get("completed_at")
    })

    # ── aggregate CER scores across all valid turns ────────────────────────
    session_ids = {s["session_id"] for s in sessions}
    session_modes = {s["session_id"]: s.get("mode", "free_debate") for s in sessions}
    session_meta = {s["session_id"]: s for s in sessions}
    session_scores = {}
    claim_vals:     list[float] = []
    evidence_vals:  list[float] = []
    reasoning_vals: list[float] = []
    total_vals:     list[float] = []

    for sid in session_ids:
        turn_docs = (
            db.collection("debate_turns")
            .where(filter=FieldFilter("session_id", "==", sid))
            .get()
        )
        valid_turn_ids = [
            d.to_dict()["turn_id"]
            for d in turn_docs
            if d.to_dict().get("status") not in ("error", "invalid")
        ]
        sess_total_vals = []
        mode = session_modes.get(sid, "free_debate")
        for tid in valid_turn_ids:
            score_docs = (
                db.collection("cer_scores")
                .where(filter=FieldFilter("turn_id", "==", tid))
                .limit(1)
                .get()
            )
            if score_docs:
                s = score_docs[0].to_dict()
                c = _normalize_score_value(float(s.get("claim",     0.0)))
                e = _normalize_score_value(float(s.get("evidence",  0.0)))
                r = _normalize_score_value(float(s.get("reasoning", 0.0)))
                t = _normalize_score_value(float(s.get("total",     0.0)))
                claim_vals.append(c)
                evidence_vals.append(e)
                reasoning_vals.append(r)
                total_vals.append(t)
                if mode == "claim_writing":
                    sess_total_vals.append(c)
                elif mode == "find_evidence":
                    sess_total_vals.append(e)
                elif mode == "quick_rebuttal":
                    sess_total_vals.append(r)
                else:
                    sess_total_vals.append(t)
        
        session_scores[sid] = _average(sess_total_vals) if sess_total_vals else 0.0

    recent_topics = [
        {
            "topic": s["topic"],
            "score": session_scores.get(s["session_id"], 0.0),
            "category": s.get("topic_category") or "Chưa phân loại",
            "difficulty": s.get("difficulty") or "Trung bình",
            "mode": s.get("mode") or "free_debate",
            "completed_at": s.get("completed_at") or s.get("created_at"),
        }
        for s in recent_sessions[:5]
    ]

    category_totals: dict[str, dict[str, float]] = {}
    weekly_scores: list[float] = []
    monthly_scores: list[float] = []
    for sid, score in session_scores.items():
        meta = session_meta.get(sid, {})
        category = meta.get("topic_category") or "Chưa phân loại"
        entry = category_totals.setdefault(category, {"count": 0, "sum": 0.0})
        entry["count"] += 1
        entry["sum"] += float(score)

        stamp = _parse_datetime(meta.get("completed_at") or meta.get("updated_at") or meta.get("created_at"))
        if stamp and stamp >= week_cutoff:
            weekly_scores.append(float(score))
        if stamp and stamp >= month_cutoff:
            monthly_scores.append(float(score))

    topic_category_breakdown = [
        {
            "category": category,
            "count": int(values["count"]),
            "average_score": round(values["sum"] / values["count"], 2) if values["count"] else 0.0,
        }
        for category, values in sorted(category_totals.items(), key=lambda item: (-int(item[1]["count"]), item[0]))
    ]

    best_topic = None
    worst_topic = None
    if recent_topics:
        sorted_recent = sorted(recent_topics, key=lambda item: float(item.get("score", 0.0)), reverse=True)
        best_topic = sorted_recent[0]
        worst_topic = sorted(recent_topics, key=lambda item: float(item.get("score", 0.0)))[0]

    recent_trend_delta = 0.0
    if len(recent_topics) >= 2:
        recent_trend_delta = round(float(recent_topics[0].get("score", 0.0)) - float(recent_topics[1].get("score", 0.0)), 2)

    scores = {
        "claim_score":     _average(claim_vals),
        "evidence_score":  _average(evidence_vals),
        "reasoning_score": _average(reasoning_vals),
    }

    return {
        "total_sessions":      total_sessions,
        "completed_sessions":  completed_sessions,
        "avg_claim_score":     scores["claim_score"],
        "avg_evidence_score":  scores["evidence_score"],
        "avg_reasoning_score": scores["reasoning_score"],
        "overall_score":       _average(total_vals),
        "streak_days":         _streak_days(completed_days),
        "recent_topics":       recent_topics,
        "topic_category_breakdown": topic_category_breakdown,
        "weekly_avg_score":     _average(weekly_scores),
        "monthly_avg_score":    _average(monthly_scores),
        "recent_trend_delta":   recent_trend_delta,
        "best_topic":           best_topic,
        "worst_topic":          worst_topic,
        "skill_strength":      _skill_label(scores, pick_highest=True),
        "skill_weakness":      _skill_label(scores, pick_highest=False),
    }


# ---------------------------------------------------------------------------
# Firebase implementations added for the provider facade
# ---------------------------------------------------------------------------

USER_MEMORY_FIELD = "debate_memory"


def _firebase_update_session(
    session_id: str,
    updates: dict,
    user_id: str | None = None,
) -> dict | None:
    session = _firebase_get_session(session_id, user_id=user_id)
    if not session:
        return None
    payload = dict(updates)
    payload.pop("id", None)
    payload.pop("session_id", None)
    payload["updated_at"] = _now()
    ref = _db().collection("debate_sessions").document(session_id)
    ref.update(payload)
    return ref.get().to_dict()


def _firebase_save_practice_prompt(
    *,
    session_id: str | None,
    user_id: str,
    mode: str,
    topic: str | None,
    topic_id: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    prompt_type: str | None = None,
    prompt_text: str | None = None,
    instruction: str | None = None,
    round_number: int = 1,
    metadata: dict | None = None,
) -> dict:
    _firebase_init_db()
    prompt_id = str(uuid4())
    data = {
        "id": prompt_id,
        "practice_prompt_id": prompt_id,
        "session_id": session_id,
        "user_id": user_id,
        "mode": mode,
        "topic": topic,
        "topic_id": topic_id,
        "category": category,
        "difficulty": difficulty,
        "prompt_type": prompt_type,
        "prompt_text": prompt_text,
        "prompt": prompt_text,
        "instruction": instruction,
        "round_number": int(round_number or 1),
        "metadata": metadata or {},
        "created_at": _now(),
    }
    _db().collection("practice_prompts").document(prompt_id).set(data)
    return data


def _firebase_get_used_practice_prompts(
    session_id: str,
    mode: str | None = None,
) -> list[dict]:
    _firebase_init_db()
    query = _db().collection("practice_prompts").where(
        filter=FieldFilter("session_id", "==", session_id)
    )
    if mode:
        query = query.where(filter=FieldFilter("mode", "==", mode))
    rows = [doc.to_dict() for doc in query.get()]
    return sorted(rows, key=lambda row: _parse_datetime(row.get("created_at")) or _now())


def _firebase_get_recent_turns(session_id: str, limit: int = 3) -> list[dict]:
    turns = _firebase_get_session_turns(session_id)
    return turns[-max(1, int(limit)):]


def _default_user_memory(user_id: str) -> dict:
    return default_user_memory(user_id)


def _merge_user_memory(memory: dict | None, user_id: str) -> dict:
    return merge_user_memory(memory, user_id)


def _firebase_get_user_memory(user_id: str) -> dict:
    init_db()
    doc = _db().collection("users").document(user_id).get()
    raw = doc.to_dict() if doc.exists else {}
    return merge_user_memory((raw or {}).get(USER_MEMORY_FIELD), user_id)


def _firebase_update_user_memory_after_turn(
    *,
    user_id: str,
    mode: str | None,
    topic: str,
    topic_category: str | None,
    user_argument: str,
    ai_result: dict,
) -> dict:
    _ = topic, user_argument
    memory = update_memory_after_turn(
        _firebase_get_user_memory(user_id),
        user_id=user_id,
        mode=mode,
        topic_category=topic_category,
        ai_result=ai_result,
    )
    _db().collection("users").document(user_id).set(
        {USER_MEMORY_FIELD: memory},
        merge=True,
    )
    return memory


def _firebase_reset_user_memory(user_id: str) -> dict:
    init_db()
    memory = default_user_memory(user_id)
    _db().collection("users").document(user_id).set(
        {USER_MEMORY_FIELD: memory},
        merge=True,
    )
    return memory


def _firebase_get_session_memory(
    session_id: str,
    user_id: str | None = None,
) -> dict:
    init_db()
    doc = _db().collection("session_memories").document(session_id).get()
    if not doc.exists:
        return {}
    data = doc.to_dict() or {}
    if user_id is not None and data.get("user_id") != user_id:
        return {}
    return dict(data.get("memory") or {})


def _firebase_update_session_memory(
    session_id: str,
    user_id: str,
    memory: dict,
) -> dict:
    init_db()
    _db().collection("session_memories").document(session_id).set(
        {
            "session_id": session_id,
            "user_id": user_id,
            "memory": memory or {},
            "updated_at": _now(),
        },
        merge=True,
    )
    return dict(memory or {})


# ---------------------------------------------------------------------------
# Public storage facade. The selected provider owns users, auth metadata,
# debate data, progress, and memory.
# ---------------------------------------------------------------------------

def init_db():
    return get_store().init_db()


def create_user(*args, **kwargs):
    return get_store().create_user(*args, **kwargs)


def get_user_by_email(*args, **kwargs):
    return get_store().get_user_by_email(*args, **kwargs)


def get_user_by_id(*args, **kwargs):
    return get_store().get_user_by_id(*args, **kwargs)


def get_demo_user():
    return get_store().get_demo_user()


def create_auth_session(*args, **kwargs):
    return get_store().create_auth_session(*args, **kwargs)


def get_auth_session_by_token(*args, **kwargs):
    return get_store().get_auth_session_by_token(*args, **kwargs)


def deactivate_auth_session(*args, **kwargs):
    return get_store().deactivate_auth_session(*args, **kwargs)


def create_session(*args, **kwargs):
    return get_store().create_session(*args, **kwargs)


def get_session(*args, **kwargs):
    return get_store().get_session(*args, **kwargs)


def update_session(*args, **kwargs):
    return get_store().update_session(*args, **kwargs)


def end_session(*args, **kwargs):
    return get_store().end_session(*args, **kwargs)


def save_practice_prompt(*args, **kwargs):
    return get_store().save_practice_prompt(*args, **kwargs)


def get_used_practice_prompts(*args, **kwargs):
    return get_store().get_used_practice_prompts(*args, **kwargs)


def save_debate_turn(*args, **kwargs):
    return get_store().save_debate_turn(*args, **kwargs)


def get_recent_turns(*args, **kwargs):
    return get_store().get_recent_turns(*args, **kwargs)


def get_session_turns(*args, **kwargs):
    return get_store().get_session_turns(*args, **kwargs)


def get_session_summary(*args, **kwargs):
    return get_store().get_session_summary(*args, **kwargs)


def get_progress_overview(*args, **kwargs):
    return get_store().get_progress_overview(*args, **kwargs)


def get_session_memory(*args, **kwargs):
    return get_store().get_session_memory(*args, **kwargs)


def update_session_memory(*args, **kwargs):
    return get_store().update_session_memory(*args, **kwargs)


def get_user_memory(*args, **kwargs):
    return get_store().get_user_memory(*args, **kwargs)


def update_user_memory_after_turn(*args, **kwargs):
    return get_store().update_user_memory_after_turn(*args, **kwargs)


def reset_user_memory(*args, **kwargs):
    return get_store().reset_user_memory(*args, **kwargs)
