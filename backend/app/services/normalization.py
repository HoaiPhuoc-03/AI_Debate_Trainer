import re
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


def optional_text_list(value) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = optional_text(item)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(text)
    return items or None


def validate_debate_topic(topic: str | None) -> dict:
    text = " ".join(_clean_text(topic).split())
    key = _key(text)
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    unique_words = {word.casefold() for word in words}

    if not text:
        return {
            "is_valid": False,
            "topic": text,
            "reason": "empty",
            "message": "Vui lòng nhập topic chính của phiên tranh biện.",
        }
    if len(text) < 12 or len(words) < 4:
        return {
            "is_valid": False,
            "topic": text,
            "reason": "too_short",
            "message": "Topic quá ngắn. Hãy nhập một chủ đề/mệnh đề tranh biện rõ hơn.",
        }
    if len(text) > 180:
        return {
            "is_valid": False,
            "topic": text,
            "reason": "too_long",
            "message": "Topic quá dài. Hãy rút gọn dưới 180 ký tự.",
        }
    if len(unique_words) <= 2 or re.search(r"([a-zA-ZÀ-ỹ])\1{3,}", text, flags=re.UNICODE):
        return {
            "is_valid": False,
            "topic": text,
            "reason": "typo_or_repetition",
            "message": "Topic có dấu hiệu gõ lỗi hoặc lặp từ. Vui lòng nhập lại rõ ràng.",
        }
    if re.search(r"\b(k|ko|khum|hok|j|z)\b", key):
        return {
            "is_valid": False,
            "topic": text,
            "reason": "shorthand",
            "message": "Vui lòng tránh viết tắt hoặc gõ lỗi trong topic.",
        }
    vowel_stripped = re.sub(r"[aeiouyăâêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", "", key)
    if re.search(r"[a-z]{7,}", vowel_stripped):
        return {
            "is_valid": False,
            "topic": text,
            "reason": "spelling",
            "message": "Topic có vẻ sai chính tả hoặc khó đọc. Vui lòng kiểm tra lại.",
        }

    unsafe_terms = [
        "do ngu",
        "cam mieng",
        "chet di",
        "tu tu",
        "giet",
        "khieu dam",
        "ma tuy",
        "khung bo",
    ]
    if any(term in key for term in unsafe_terms):
        return {
            "is_valid": False,
            "topic": text,
            "reason": "unsafe",
            "message": "Topic có nội dung vi phạm an toàn. Vui lòng nhập chủ đề khác.",
        }

    debate_cues = [
        "co nen",
        "nen",
        "should",
        "ban",
        "allow",
        "cam",
        "cho phep",
        "bat buoc",
        "thay the",
        "anh huong",
        "tot hon",
        "quyen",
        "chinh sach",
        "luat",
        "trach nhiem",
        "hoc sinh",
        "sinh vien",
        "ai",
    ]
    if "?" not in text and not any(cue in key for cue in debate_cues):
        return {
            "is_valid": False,
            "topic": text,
            "reason": "not_debatable",
            "message": "Topic cần là một vấn đề có thể tranh biện, ví dụ bắt đầu bằng 'Có nên...'.",
        }

    return {"is_valid": True, "topic": text, "reason": "", "message": ""}


def normalize_topic(topic: str | None, topic_category: str | None, custom_topic: str | None) -> str:
    selected_topic = optional_text(topic)
    if selected_topic:
        return selected_topic
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
            "en": "vi",
            "eng": "vi",
            "english": "vi",
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
    topic = normalize_topic(payload.topic, payload.topic_category, payload.custom_topic)
    topic_id = optional_text(getattr(payload, "topic_id", None))
    return {
        "topic": topic,
        "topic_id": topic_id,
        "topic_category": optional_text(getattr(payload, "topic_category", None)) if topic_id else None,
        "topic_tags": optional_text_list(getattr(payload, "topic_tags", None)) if topic_id else None,
        "custom_topic": None,
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
