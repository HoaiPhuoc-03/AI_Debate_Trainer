from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import settings
from app.services.cer_scorer import normalize_cer_to_100
from app.services.memory_utils import (
    default_user_memory,
    merge_user_memory,
    update_memory_after_turn,
)
from app.services.storage_errors import StorageError
from app.services.supabase_client import get_supabase_client


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def _rows(response) -> list[dict]:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _unique_first(items: list[str], limit: int = 5) -> list[str]:
    result = []
    seen = set()
    for item in items:
        clean = str(item or "").strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
        if len(result) >= limit:
            break
    return result


def _parse_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


class SupabaseStore:
    provider = "supabase"

    # TODO(auth-rls): after the Auth migration is stable, add per-user RLS
    # policies using auth.uid()::text = user_id before allowing direct clients.
    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def _execute(self, query, operation: str):
        try:
            return query.execute()
        except Exception as exc:
            raise StorageError(f"Supabase {operation} failed: {exc}") from exc

    @staticmethod
    def _session_from_row(row: dict | None) -> dict | None:
        if not row:
            return None
        metadata = dict(row.get("metadata") or {})
        session = {
            **metadata,
            **row,
            "session_id": str(row.get("id") or row.get("session_id")),
            "mode": row.get("practice_mode") or metadata.get("mode") or "free_debate",
            "input_mode": metadata.get("input_mode") or "text",
            "max_turns": int(metadata.get("max_turns") or settings.DEFAULT_MAX_TURNS),
        }
        return session

    def create_user(
        self,
        email: str,
        password_hash: str = "",
        display_name: str = "",
        age_group: str = "adult",
        debate_level: str = "intermediate",
        language: str = "vi",
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        user_id = user_id or str(uuid4())
        payload = {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "profile_level": debate_level,
            "preferred_language": language,
            "metadata": {
                "password_hash": password_hash,
                "age_group": age_group,
                "auth_sessions": [],
                **(metadata or {}),
            },
            "updated_at": _now_iso(),
        }
        response = self._execute(
            self.client.table("profiles").upsert(payload, on_conflict="id"),
            "create user",
        )
        row = (_rows(response) or [payload])[0]
        return self._user_from_row(row)

    def get_user(self, user_id: str) -> dict | None:
        response = self._execute(
            self.client.table("profiles").select("*").eq("id", user_id).limit(1),
            "get user",
        )
        rows = _rows(response)
        return self._user_from_row(rows[0]) if rows else None

    @staticmethod
    def _user_from_row(row: dict | None) -> dict | None:
        if not row:
            return None
        metadata = dict(row.get("metadata") or {})
        return {
            "id": str(row["id"]),
            "email": row.get("email"),
            "display_name": row.get("display_name"),
            "age_group": metadata.get("age_group") or "adult",
            "debate_level": row.get("profile_level") or "intermediate",
            "language": row.get("preferred_language") or "vi",
            "password_hash": metadata.get("password_hash") or "",
            "metadata": metadata,
        }

    def get_user_by_id(self, user_id: str) -> dict | None:
        return self.get_user(user_id)

    def get_user_by_email(self, email: str) -> dict | None:
        response = self._execute(
            self.client.table("profiles")
            .select("*")
            .eq("email", str(email or "").strip().casefold())
            .limit(1),
            "get user by email",
        )
        rows = _rows(response)
        return self._user_from_row(rows[0]) if rows else None

    def upsert_profile(
        self,
        user_id: str,
        email: str | None,
        display_name: str | None,
        *,
        age_group: str | None = None,
        debate_level: str | None = None,
        language: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        existing = self.get_user(user_id)
        existing_metadata = deepcopy((existing or {}).get("metadata") or {})
        profile_metadata = {
            **existing_metadata,
            **(metadata or {}),
        }
        if age_group:
            profile_metadata["age_group"] = age_group

        payload = {
            "id": str(user_id),
            "email": email or (existing or {}).get("email"),
            "display_name": (
                display_name
                or (existing or {}).get("display_name")
                or email
                or str(user_id)
            ),
            "profile_level": (
                debate_level
                or (existing or {}).get("debate_level")
                or "intermediate"
            ),
            "preferred_language": (
                language
                or (existing or {}).get("language")
                or "vi"
            ),
            "metadata": profile_metadata,
            "updated_at": _now_iso(),
        }
        response = self._execute(
            self.client.table("profiles").upsert(payload, on_conflict="id"),
            "upsert profile",
        )
        row = (_rows(response) or [payload])[0]
        return self._user_from_row(row)

    def ensure_profile(
        self,
        user_id: str,
        email: str | None = None,
        display_name: str | None = None,
        **profile_fields,
    ) -> dict:
        existing = self.get_user(user_id)
        if existing and not any(
            value is not None
            for value in (email, display_name, *profile_fields.values())
        ):
            return existing
        return self.upsert_profile(
            user_id,
            email,
            display_name,
            **profile_fields,
        )

    def ensure_user(
        self,
        user_id: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> dict:
        existing = self.get_user(user_id)
        if existing:
            if user_id == "demo-user":
                metadata = deepcopy(existing.get("metadata") or {})
                if metadata.get("source") != "local_demo":
                    metadata["source"] = "local_demo"
                    existing = self._write_user_metadata(user_id, metadata)
            return existing
        return self.create_user(
            user_id=user_id,
            email=email or f"{user_id}@local.test",
            display_name=display_name or user_id,
            age_group="adult",
            debate_level="Trung cấp",
            language="vi",
            metadata={"source": "local_demo"},
        )

    def get_demo_user(self) -> dict:
        return self.ensure_user(
            "demo-user",
            email="demo@local.test",
            display_name="Demo User",
        )

    def init_db(self) -> None:
        self.get_demo_user()

    def _write_user_metadata(self, user_id: str, metadata: dict) -> dict:
        response = self._execute(
            self.client.table("profiles")
            .update({"metadata": metadata, "updated_at": _now_iso()})
            .eq("id", user_id),
            "update user metadata",
        )
        rows = _rows(response)
        if rows:
            return self._user_from_row(rows[0])
        user = self.get_user(user_id)
        if not user:
            raise StorageError(f"Supabase user '{user_id}' was not found.")
        return user

    def create_auth_session(
        self,
        user_id: str,
        token: str,
        expires_at=None,
    ) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise StorageError(f"Supabase user '{user_id}' was not found.")
        metadata = deepcopy(user.get("metadata") or {})
        sessions = [
            item
            for item in (metadata.get("auth_sessions") or [])
            if item.get("token") != token
        ]
        session = {
            "id": str(uuid4()),
            "user_id": user_id,
            "token": token,
            "created_at": _now_iso(),
            "expires_at": (
                expires_at.isoformat()
                if isinstance(expires_at, datetime)
                else expires_at
            ),
            "is_active": 1,
        }
        sessions.append(session)
        metadata["auth_sessions"] = sessions[-20:]
        self._write_user_metadata(user_id, metadata)
        return {
            **session,
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "age_group": user.get("age_group"),
            "debate_level": user.get("debate_level"),
            "language": user.get("language"),
        }

    def get_auth_session_by_token(self, token: str) -> dict | None:
        response = self._execute(
            self.client.table("profiles").select("*"),
            "get auth session",
        )
        for row in _rows(response):
            user = self._user_from_row(row)
            for session in (user.get("metadata") or {}).get("auth_sessions", []):
                if session.get("token") == token:
                    return {
                        **session,
                        "email": user.get("email"),
                        "display_name": user.get("display_name"),
                        "age_group": user.get("age_group"),
                        "debate_level": user.get("debate_level"),
                        "language": user.get("language"),
                    }
        return None

    def deactivate_auth_session(self, token: str) -> dict | None:
        response = self._execute(
            self.client.table("profiles").select("*"),
            "deactivate auth session",
        )
        for row in _rows(response):
            user = self._user_from_row(row)
            metadata = deepcopy(user.get("metadata") or {})
            sessions = metadata.get("auth_sessions") or []
            for session in sessions:
                if session.get("token") == token:
                    session["is_active"] = 0
                    metadata["auth_sessions"] = sessions
                    self._write_user_metadata(user["id"], metadata)
                    return dict(session)
        return None

    def create_session(
        self,
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
        ai_stance: str | None = None,
        status: str = "active",
        metadata: dict | None = None,
    ) -> dict:
        session_id = str(uuid4())
        now = _now_iso()
        session_metadata = {
            **(metadata or {}),
            "topic_tags": topic_tags,
            "custom_topic": custom_topic,
            "input_mode": input_mode or "text",
            "age_group": age_group or "adult",
            "debate_level": debate_level or "intermediate",
            "coach_model": coach_model or "socratic_v3",
            "language": language or "vi",
            "mode": mode or "free_debate",
            "response_time": response_time,
            "max_turns": int(max_turns or settings.DEFAULT_MAX_TURNS),
            "display_name": display_name,
        }
        payload = {
            "id": session_id,
            "user_id": user_id,
            "topic": topic,
            "topic_id": topic_id,
            "topic_category": topic_category,
            "stance": stance,
            "ai_stance": ai_stance,
            "difficulty": difficulty,
            "practice_mode": mode or "free_debate",
            "status": status,
            "turn_count": 0,
            "average_score": 0,
            "metadata": session_metadata,
            "created_at": now,
            "updated_at": now,
        }
        response = self._execute(
            self.client.table("debate_sessions").insert(payload),
            "create session",
        )
        return self._session_from_row((_rows(response) or [payload])[0])

    def get_session(self, session_id: str, user_id: str | None = None) -> dict | None:
        query = self.client.table("debate_sessions").select("*").eq("id", session_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        response = self._execute(query.limit(1), "get session")
        rows = _rows(response)
        return self._session_from_row(rows[0]) if rows else None

    def update_session(
        self,
        session_id: str,
        updates: dict,
        user_id: str | None = None,
    ) -> dict | None:
        payload = dict(updates)
        payload.pop("id", None)
        payload.pop("session_id", None)
        payload["updated_at"] = _now_iso()
        query = self.client.table("debate_sessions").update(payload).eq("id", session_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        response = self._execute(query, "update session")
        rows = _rows(response)
        return self._session_from_row(rows[0]) if rows else self.get_session(session_id, user_id)

    def end_session(self, session_id: str, user_id: str | None = None) -> dict | None:
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        scores_response = self._execute(
            self.client.table("cer_scores").select("total").eq("session_id", session_id),
            "calculate session score",
        )
        totals = [float(row.get("total") or 0.0) for row in _rows(scores_response)]
        now = _now_iso()
        return self.update_session(
            session_id,
            {
                "status": "completed",
                "average_score": _average(totals),
                "completed_at": session.get("completed_at") or now,
            },
            user_id,
        )

    def save_practice_prompt(
        self,
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
        prompt_id = str(uuid4())
        payload = {
            "id": prompt_id,
            "session_id": session_id,
            "user_id": user_id,
            "mode": mode,
            "topic": topic,
            "topic_id": topic_id,
            "category": category,
            "difficulty": difficulty,
            "prompt_type": prompt_type,
            "prompt_text": prompt_text,
            "instruction": instruction,
            "round_number": int(round_number or 1),
            "metadata": metadata or {},
        }
        response = self._execute(
            self.client.table("practice_prompts").insert(payload),
            "save practice prompt",
        )
        row = (_rows(response) or [payload])[0]
        return {**row, "practice_prompt_id": str(row.get("id") or prompt_id)}

    def get_used_practice_prompts(
        self,
        session_id: str,
        mode: str | None = None,
    ) -> list[dict]:
        query = (
            self.client.table("practice_prompts")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
        )
        if mode:
            query = query.eq("mode", mode)
        response = self._execute(query, "get used practice prompts")
        return [
            {
                **row,
                "practice_prompt_id": str(row.get("id")),
                "prompt": row.get("prompt_text"),
            }
            for row in _rows(response)
        ]

    def _next_turn_number(self, session_id: str) -> int:
        response = self._execute(
            self.client.table("debate_turns")
            .select("turn_number")
            .eq("session_id", session_id)
            .order("turn_number", desc=True)
            .limit(1),
            "get next turn number",
        )
        rows = _rows(response)
        return int(rows[0].get("turn_number") or 0) + 1 if rows else 1

    def save_turn(
        self,
        *,
        session_id: str,
        user_id: str,
        practice_prompt_id: str | None,
        turn_number: int,
        user_argument: str,
        ai_rebuttal: str,
        input_type: str,
        practice_mode: str | None,
        is_valid: bool,
        metadata: dict | None = None,
    ) -> str:
        turn_id = str(uuid4())
        payload = {
            "id": turn_id,
            "session_id": session_id,
            "user_id": user_id,
            "practice_prompt_id": practice_prompt_id,
            "turn_number": int(turn_number),
            "user_argument": user_argument,
            "ai_rebuttal": ai_rebuttal,
            "input_type": input_type or "text",
            "practice_mode": practice_mode,
            "is_valid": bool(is_valid),
            "metadata": metadata or {},
        }
        response = self._execute(
            self.client.table("debate_turns").insert(payload),
            "save turn",
        )
        rows = _rows(response)
        return str(rows[0].get("id") if rows else turn_id)

    def save_cer_score(
        self,
        *,
        turn_id: str,
        session_id: str,
        user_id: str,
        cer: dict,
    ) -> str:
        score_id = str(uuid4())
        normalized = normalize_cer_to_100(cer)
        payload = {
            "id": score_id,
            "turn_id": turn_id,
            "session_id": session_id,
            "user_id": user_id,
            "claim": float(normalized.get("claim", 0.0)),
            "evidence": float(normalized.get("evidence", 0.0)),
            "reasoning": float(normalized.get("reasoning", 0.0)),
            "overall": float(normalized.get("overall", normalized.get("total", 0.0))),
            "total": float(normalized.get("total", 0.0)),
        }
        self._execute(self.client.table("cer_scores").insert(payload), "save CER score")
        return score_id

    def save_feedback_items(
        self,
        *,
        turn_id: str,
        session_id: str,
        user_id: str,
        feedback: dict,
    ) -> list[dict]:
        type_map = {
            "strengths": "strength",
            "weaknesses": "weakness",
            "suggestions": "suggestion",
        }
        payload = [
            {
                "id": str(uuid4()),
                "turn_id": turn_id,
                "session_id": session_id,
                "user_id": user_id,
                "feedback_type": feedback_type,
                "content": str(content),
            }
            for key, feedback_type in type_map.items()
            for content in (feedback.get(key) or [])
        ]
        if payload:
            self._execute(
                self.client.table("feedback_items").insert(payload),
                "save feedback items",
            )
        return payload

    def save_content_flags(
        self,
        *,
        turn_id: str,
        session_id: str,
        user_id: str,
        flags: list,
    ) -> list[dict]:
        payload = [
            {
                "id": str(uuid4()),
                "turn_id": turn_id,
                "session_id": session_id,
                "user_id": user_id,
                "flag_type": flag.get("type", "ai_error"),
                "message": flag.get("message", ""),
                "metadata": {"severity": flag.get("severity", "low")},
            }
            for flag in (flags or [])
        ]
        if payload:
            self._execute(
                self.client.table("content_flags").insert(payload),
                "save content flags",
            )
        return payload

    def save_debate_turn(
        self,
        session: dict,
        user_argument: str,
        ai_rebuttal: str,
        cer: dict,
        feedback: dict,
        content_flags: list | None = None,
        practice_mode: str | None = None,
        practice_prompt: str | None = None,
        practice_round: int | None = None,
        practice_prompt_id: str | None = None,
        status: str = "active",
        count_for_completion: bool = True,
        complete_session: bool = True,
    ) -> dict:
        session_id = session["session_id"]
        user_id = session["user_id"]
        turn_number = self._next_turn_number(session_id)
        is_valid = status not in ("invalid", "error")
        turn_id = self.save_turn(
            session_id=session_id,
            user_id=user_id,
            practice_prompt_id=practice_prompt_id,
            turn_number=turn_number,
            user_argument=user_argument,
            ai_rebuttal=ai_rebuttal,
            input_type=session.get("input_mode", "text"),
            practice_mode=practice_mode,
            is_valid=is_valid,
            metadata={
                "practice_prompt": practice_prompt,
                "practice_round": practice_round,
                "status": status,
            },
        )
        self.save_cer_score(
            turn_id=turn_id,
            session_id=session_id,
            user_id=user_id,
            cer=cer,
        )
        self.save_feedback_items(
            turn_id=turn_id,
            session_id=session_id,
            user_id=user_id,
            feedback=feedback,
        )
        self.save_content_flags(
            turn_id=turn_id,
            session_id=session_id,
            user_id=user_id,
            flags=content_flags or [],
        )
        scores_response = self._execute(
            self.client.table("cer_scores").select("total").eq(
                "session_id",
                session_id,
            ),
            "calculate session average",
        )
        average_score = _average(
            [float(row.get("total") or 0.0) for row in _rows(scores_response)]
        )

        current_count = int(session.get("turn_count") or 0)
        next_count = current_count + 1 if count_for_completion else current_count
        max_turns = int(session.get("max_turns") or settings.DEFAULT_MAX_TURNS)
        next_status = (
            "completed"
            if complete_session and count_for_completion and next_count >= max_turns
            else "active"
        )
        updates = {
            "turn_count": next_count,
            "status": next_status,
            "average_score": average_score,
        }
        if next_status == "completed":
            updates["completed_at"] = _now_iso()
        updated_session = self.update_session(session_id, updates, user_id) or session
        return {
            "turn_id": turn_id,
            "turn_number": turn_number,
            "session": updated_session,
        }

    def _hydrate_turn(self, turn: dict) -> dict:
        turn_id = str(turn.get("id") or turn.get("turn_id"))
        score_response = self._execute(
            self.client.table("cer_scores").select("*").eq("turn_id", turn_id).limit(1),
            "get turn CER score",
        )
        feedback_response = self._execute(
            self.client.table("feedback_items")
            .select("*")
            .eq("turn_id", turn_id)
            .order("created_at"),
            "get turn feedback",
        )
        score_rows = _rows(score_response)
        raw_score = score_rows[0] if score_rows else {}
        cer = normalize_cer_to_100(
            {
                "claim": float(raw_score.get("claim") or 0.0),
                "evidence": float(raw_score.get("evidence") or 0.0),
                "reasoning": float(raw_score.get("reasoning") or 0.0),
                "overall": float(raw_score.get("overall") or raw_score.get("total") or 0.0),
                "total": float(raw_score.get("total") or 0.0),
            }
        )
        feedback = {"strengths": [], "weaknesses": [], "suggestions": []}
        category_map = {
            "strength": "strengths",
            "weakness": "weaknesses",
            "suggestion": "suggestions",
        }
        for item in _rows(feedback_response):
            category = category_map.get(item.get("feedback_type"))
            if category:
                feedback[category].append(item.get("content", ""))

        metadata = dict(turn.get("metadata") or {})
        return {
            **turn,
            **metadata,
            "turn_id": turn_id,
            "status": metadata.get("status") or ("active" if turn.get("is_valid", True) else "invalid"),
            "practice_prompt": metadata.get("practice_prompt"),
            "practice_round": metadata.get("practice_round"),
            "cer": cer,
            "feedback": feedback,
            "feedback_summary": "; ".join(
                [*feedback["weaknesses"], *feedback["suggestions"]]
            ),
        }

    def get_recent_turns(self, session_id: str, limit: int = 3) -> list[dict]:
        response = self._execute(
            self.client.table("debate_turns")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit),
            "get recent turns",
        )
        return [self._hydrate_turn(row) for row in reversed(_rows(response))]

    def get_session_turns(self, session_id: str) -> list[dict]:
        response = self._execute(
            self.client.table("debate_turns")
            .select("*")
            .eq("session_id", session_id)
            .order("turn_number"),
            "get session turns",
        )
        return [self._hydrate_turn(row) for row in _rows(response)]

    def get_session_summary(
        self,
        session_id: str,
        user_id: str | None = None,
    ) -> dict | None:
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        turns = self.get_session_turns(session_id)
        scored = [turn for turn in turns if turn.get("status") not in ("error", "invalid")]
        strengths = [item for turn in turns for item in turn["feedback"]["strengths"]]
        weaknesses = [item for turn in turns for item in turn["feedback"]["weaknesses"]]
        suggestions = [item for turn in turns for item in turn["feedback"]["suggestions"]]
        return {
            "session_id": session_id,
            "topic": session["topic"],
            "stance": session["stance"],
            "difficulty": session["difficulty"],
            "turn_count": int(session.get("turn_count") or 0),
            "max_turns": int(session.get("max_turns") or settings.DEFAULT_MAX_TURNS),
            "status": session["status"],
            "avg_claim_score": _average([turn["cer"]["claim"] for turn in scored]),
            "avg_evidence_score": _average([turn["cer"]["evidence"] for turn in scored]),
            "avg_reasoning_score": _average([turn["cer"]["reasoning"] for turn in scored]),
            "overall_score": _average([turn["cer"]["total"] for turn in scored]),
            "strength_summary": _unique_first(strengths),
            "weakness_summary": _unique_first(weaknesses),
            "next_steps": _unique_first(suggestions),
        }

    def get_progress_overview(self, user_id: str | None = None) -> dict:
        query = self.client.table("debate_sessions").select("*")
        if user_id is not None:
            query = query.eq("user_id", user_id)
        sessions_response = self._execute(query, "get progress sessions")
        sessions = [self._session_from_row(row) for row in _rows(sessions_response)]
        sessions = [session for session in sessions if session]
        all_turns = []
        for session in sessions:
            all_turns.extend(self.get_session_turns(session["session_id"]))
        valid_turns = [
            turn for turn in all_turns if turn.get("status") not in ("error", "invalid")
        ]
        scores = {
            "claim_score": _average([turn["cer"]["claim"] for turn in valid_turns]),
            "evidence_score": _average([turn["cer"]["evidence"] for turn in valid_turns]),
            "reasoning_score": _average([turn["cer"]["reasoning"] for turn in valid_turns]),
        }
        recent = sorted(
            sessions,
            key=lambda item: _parse_datetime(item.get("created_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:5]
        recent_topics = [
            {
                "topic": session["topic"],
                "score": float(session.get("average_score") or 0.0),
                "category": session.get("topic_category") or "Chua phan loai",
                "difficulty": session.get("difficulty") or "Trung binh",
                "mode": session.get("mode") or "free_debate",
                "completed_at": session.get("completed_at") or session.get("created_at"),
            }
            for session in recent
        ]
        categories = {}
        for session in sessions:
            category = session.get("topic_category") or "Chua phan loai"
            entry = categories.setdefault(category, {"count": 0, "scores": []})
            entry["count"] += 1
            entry["scores"].append(float(session.get("average_score") or 0.0))
        breakdown = [
            {
                "category": category,
                "count": values["count"],
                "average_score": _average(values["scores"]),
            }
            for category, values in categories.items()
        ]
        completed_days = {
            _parse_datetime(session.get("completed_at")).date()
            for session in sessions
            if _parse_datetime(session.get("completed_at"))
        }
        streak = 0
        if completed_days:
            cursor = max(completed_days)
            while cursor in completed_days:
                streak += 1
                cursor -= timedelta(days=1)
        now = datetime.now(timezone.utc)
        weekly_scores = []
        monthly_scores = []
        for session in sessions:
            stamp = _parse_datetime(
                session.get("completed_at")
                or session.get("updated_at")
                or session.get("created_at")
            )
            score = float(session.get("average_score") or 0.0)
            if stamp and stamp >= now - timedelta(days=7):
                weekly_scores.append(score)
            if stamp and stamp >= now - timedelta(days=30):
                monthly_scores.append(score)
        skill_strength = max(scores, key=scores.get).replace("_score", "") if scores else ""
        skill_weakness = min(scores, key=scores.get).replace("_score", "") if scores else ""
        return {
            "total_sessions": len(sessions),
            "completed_sessions": sum(1 for item in sessions if item.get("status") == "completed"),
            "avg_claim_score": scores["claim_score"],
            "avg_evidence_score": scores["evidence_score"],
            "avg_reasoning_score": scores["reasoning_score"],
            "overall_score": _average([turn["cer"]["total"] for turn in valid_turns]),
            "streak_days": streak,
            "recent_topics": recent_topics,
            "topic_category_breakdown": breakdown,
            "weekly_avg_score": _average(weekly_scores),
            "monthly_avg_score": _average(monthly_scores),
            "recent_trend_delta": (
                round(recent_topics[0]["score"] - recent_topics[1]["score"], 2)
                if len(recent_topics) > 1
                else 0.0
            ),
            "best_topic": max(recent_topics, key=lambda item: item["score"]) if recent_topics else None,
            "worst_topic": min(recent_topics, key=lambda item: item["score"]) if recent_topics else None,
            "skill_strength": skill_strength,
            "skill_weakness": skill_weakness,
        }

    def get_session_memory(self, session_id: str, user_id: str | None = None) -> dict:
        query = self.client.table("session_memories").select("*").eq("session_id", session_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        response = self._execute(query.limit(1), "get session memory")
        rows = _rows(response)
        return dict(rows[0].get("memory") or {}) if rows else {}

    def update_session_memory(
        self,
        session_id: str,
        user_id: str,
        memory: dict,
    ) -> dict:
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "memory": memory or {},
            "updated_at": _now_iso(),
        }
        response = self._execute(
            self.client.table("session_memories").upsert(
                payload,
                on_conflict="session_id",
            ),
            "update session memory",
        )
        rows = _rows(response)
        return dict(rows[0].get("memory") or memory or {}) if rows else dict(memory or {})

    def get_user_memory(self, user_id: str) -> dict:
        response = self._execute(
            self.client.table("user_memories")
            .select("*")
            .eq("user_id", user_id)
            .limit(1),
            "get user memory",
        )
        rows = _rows(response)
        return merge_user_memory(rows[0].get("memory") if rows else None, user_id)

    def update_user_memory_after_turn(
        self,
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
            self.get_user_memory(user_id),
            user_id=user_id,
            mode=mode,
            topic_category=topic_category,
            ai_result=ai_result,
        )
        payload = {
            "user_id": user_id,
            "version": int(memory.get("version") or 1),
            "memory": memory,
            "updated_at": _now_iso(),
        }
        self._execute(
            self.client.table("user_memories").upsert(
                payload,
                on_conflict="user_id",
            ),
            "update user memory",
        )
        return memory

    def reset_user_memory(self, user_id: str) -> dict:
        memory = default_user_memory(user_id)
        payload = {
            "user_id": user_id,
            "version": 1,
            "memory": memory,
            "updated_at": _now_iso(),
        }
        self._execute(
            self.client.table("user_memories").upsert(
                payload,
                on_conflict="user_id",
            ),
            "reset user memory",
        )
        return memory
