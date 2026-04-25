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
    for separator in ("_", "-", "/", "."):
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
    return _lookup(
        value,
        {
            "basic": "basic",
            "easy": "basic",
            "beginner": "basic",
            "co ban": "basic",
            "medium": "intermediate",
            "intermediate": "intermediate",
            "trung binh": "intermediate",
            "advanced": "advanced",
            "hard": "advanced",
            "expert": "advanced",
            "nang cao": "advanced",
        },
        "intermediate",
    )


def normalize_age_group(value) -> str:
    return _lookup(
        value,
        {
            "teen": "teen",
            "teenager": "teen",
            "13": "teen",
            "17": "teen",
            "adult": "adult",
            "18": "adult",
            "40": "adult",
            "senior": "senior",
            "41": "senior",
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
            "voice": "voice",
            "speech": "voice",
            "audio": "voice",
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
        },
        "active",
    )


def normalize_max_turns(value) -> int:
    try:
        turns = int(value)
    except (TypeError, ValueError):
        turns = int(settings.DEFAULT_MAX_TURNS)
    if turns < 1:
        return int(settings.DEFAULT_MAX_TURNS)
    return turns


def normalize_session_payload(payload) -> dict:
    return {
        "topic": normalize_topic(payload.topic, payload.topic_category, payload.custom_topic),
        "topic_category": optional_text(payload.topic_category),
        "custom_topic": optional_text(payload.custom_topic),
        "stance": normalize_stance(payload.stance),
        "difficulty": normalize_difficulty(payload.difficulty),
        "input_mode": normalize_input_mode(payload.input_mode),
        "age_group": normalize_age_group(payload.age_group),
        "debate_level": normalize_difficulty(payload.debate_level),
        "language": normalize_language(payload.language),
        "response_time": optional_text(payload.response_time),
        "max_turns": normalize_max_turns(payload.max_turns),
        "display_name": optional_text(payload.display_name),
    }
