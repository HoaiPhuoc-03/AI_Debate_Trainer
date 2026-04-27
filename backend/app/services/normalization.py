import unicodedata

from app.core.config import settings


def _clean_text(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired.strip() or text


def _key(value) -> str:
    text = _repair_mojibake(_clean_text(value)).casefold()
    text = text.replace("\u0111", "d").replace("\u0110", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    for separator in ("_", "-", "–", "—", "/", "."):
        text = text.replace(separator, " ")
    return " ".join(text.split())


def _lookup(value, aliases: dict[str, str], default: str) -> str:
    key = _key(value)
    if not key:
        return default
    if key in aliases:
        return aliases[key]
    for alias, normalized in aliases.items():
        if alias in key:
            return normalized
    return default


def optional_text(value) -> str | None:
    text = _clean_text(value)
    return text or None


def normalize_topic(topic: str | None, topic_category: str | None, custom_topic: str | None) -> str:
    custom = optional_text(custom_topic)
    if custom:
        return custom
    selected_topic = optional_text(topic)
    if selected_topic:
        return selected_topic
    selected_category = optional_text(topic_category)
    if selected_category:
        return selected_category
    return "General Debate"


def normalize_stance(value) -> str:
    return _lookup(
        value,
        {
            "support": "support",
            "pro": "support",
            "for": "support",
            "agree": "support",
            "ung ho": "support",
            "oppose": "oppose",
            "against": "oppose",
            "anti": "oppose",
            "disagree": "oppose",
            "phan doi": "oppose",
            "neutral": "neutral",
            "balanced": "neutral",
            "trung lap": "neutral",
        },
        "neutral",
    )


def normalize_difficulty(value) -> str:
    level = _lookup(
        value,
        {
            "basic": "basic",
            "easy": "basic",
            "beginner": "basic",
            "co ban": "basic",
            "medium": "intermediate",
            "intermediate": "intermediate",
            "trung cap": "intermediate",
            "trung binh": "intermediate",
            "advanced": "advanced",
            "hard": "advanced",
            "expert": "advanced",
            "nang cao": "advanced",
        },
        "intermediate",
    )
    return difficulty_label_from_level(level)


def normalize_debate_level(value) -> str:
    return _lookup(
        value,
        {
            "basic": "basic",
            "easy": "basic",
            "beginner": "basic",
            "co ban": "basic",
            "medium": "intermediate",
            "intermediate": "intermediate",
            "trung cap": "intermediate",
            "trung binh": "intermediate",
            "advanced": "advanced",
            "hard": "advanced",
            "expert": "advanced",
            "nang cao": "advanced",
        },
        "intermediate",
    )


def difficulty_label_from_level(level: str) -> str:
    return {
        "basic": "Cơ bản",
        "intermediate": "Trung bình",
        "advanced": "Nâng cao",
    }.get(level, "Trung bình")


def normalize_age_group(value) -> str:
    return _lookup(
        value,
        {
            "teen": "teen",
            "teenager": "teen",
            "thanh thieu nien": "teen",
            "thieu nien": "teen",
            "13": "teen",
            "17": "teen",
            "13 17": "teen",
            "13 17 tuoi": "teen",
            "adult": "adult",
            "nguoi lon": "adult",
            "18": "adult",
            "40": "adult",
            "18 40": "adult",
            "18 40 tuoi": "adult",
            "senior": "senior",
            "nguoi cao tuoi": "senior",
            "cao tuoi": "senior",
            "41": "senior",
            "41 tuoi": "senior",
            "older": "senior",
        },
        "adult",
    )


def normalize_input_mode(value) -> str:
    return _lookup(
        value,
        {
            "text": "text",
            "type": "text",
            "typing": "text",
            "van ban": "text",
            "voice": "voice",
            "speech": "voice",
            "audio": "voice",
            "giong noi": "voice",
            "noi": "voice",
        },
        "text",
    )


def normalize_language(value) -> str:
    return _lookup(
        value,
        {
            "vi": "vi",
            "vn": "vi",
            "vietnamese": "vi",
            "tieng viet": "vi",
            "en": "en",
            "eng": "en",
            "english": "en",
        },
        "vi",
    )


def normalize_status(value) -> str:
    return _lookup(
        value,
        {
            "active": "active",
            "ready": "active",
            "found": "active",
            "success": "active",
            "completed": "completed",
            "complete": "completed",
            "done": "completed",
            "error": "error",
            "failed": "error",
            "invalid": "invalid",
        },
        "active",
    )


def normalize_coach_model(value) -> str:
    return _lookup(
        value,
        {
            "socratic v3": "socratic_v3",
            "socratic_v3": "socratic_v3",
            "socratic": "socratic_v3",
            "coach": "socratic_v3",
        },
        "socratic_v3",
    )


def normalize_max_turns(value) -> int:
    try:
        turns = int(value)
    except (TypeError, ValueError):
        turns = int(settings.DEFAULT_MAX_TURNS)
    if turns < 1:
        return int(settings.DEFAULT_MAX_TURNS)
    if turns > 10:
        return 10
    return turns


def normalize_session_payload(payload) -> dict:
    debate_level = normalize_debate_level(payload.debate_level)
    difficulty = normalize_difficulty(payload.difficulty) if payload.difficulty else difficulty_label_from_level(debate_level)
    return {
        "topic": normalize_topic(payload.topic, payload.topic_category, payload.custom_topic),
        "topic_category": optional_text(payload.topic_category),
        "custom_topic": optional_text(payload.custom_topic),
        "stance": normalize_stance(payload.stance),
        "difficulty": difficulty,
        "input_mode": normalize_input_mode(payload.input_mode),
        "age_group": normalize_age_group(payload.age_group),
        "debate_level": debate_level,
        "coach_model": normalize_coach_model(getattr(payload, "coach_model", None)),
        "language": normalize_language(payload.language),
        "response_time": optional_text(payload.response_time),
        "max_turns": normalize_max_turns(payload.max_turns),
        "display_name": optional_text(payload.display_name),
    }
