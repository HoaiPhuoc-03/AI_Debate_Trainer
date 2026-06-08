from __future__ import annotations

import hashlib
import re
import unicodedata

from app.data.topics import list_topics, recommended_topics


MODE_ALIASES = {
    "claim_practice": "claim_writing",
    "claim": "claim_writing",
    "evidence_practice": "find_evidence",
    "evidence": "find_evidence",
    "argument_builder": "full_argument",
    "cer": "full_argument",
    "full": "full_argument",
}

SUPPORTED_PROMPT_MODES = {
    "claim_writing",
    "find_evidence",
    "quick_rebuttal",
    "full_argument",
}

PROMPT_BANK = {
    "claim_writing": [
        "Viet mot claim ro rang, co pham vi tranh luan va co the bi phan bien ve viec hoc sinh dung AI de lam bai tap.",
        "Viet mot claim cu the ve viec co nen cam dien thoai trong gio hoc.",
        "Viet mot claim co gioi han pham vi ve viec day ky nang tai chinh ca nhan o cap 3.",
        "Viet mot claim tranh luan duoc ve viec mang xa hoi anh huong den kha nang tap trung.",
    ],
    "find_evidence": [
        "Tim bang chung cu the cho claim: Hoc truc tuyen co the kem hieu qua hon hoc truc tiep neu thieu tuong tac.",
        "Tim bang chung cu the cho claim: Mang xa hoi lam giam kha nang tap trung cua thanh thieu nien.",
        "Tim bang chung cu the cho claim: Giao thong cong cong giup giam un tac va o nhiem do thi.",
        "Tim bang chung cu the cho claim: Day ky nang phan bien giup sinh vien ra quyet dinh tot hon.",
    ],
    "quick_rebuttal": [
        "Không cần học đại học vì Bill Gates cũng bỏ học mà vẫn thành công.",
        "Nên cấm xe máy vì tai nạn giao thông đường bộ xảy ra mỗi ngày.",
        "Điện thoại hoàn toàn vô hại vì tôi đã dùng mười năm mà không bị bệnh.",
        "Học tiếng Anh là vô ích vì công cụ AI đã có thể dịch mọi thứ.",
        "Nên tiêu hết tiền thay vì tiết kiệm vì ngày mai có thể chúng ta không còn sống.",
    ],
    "full_argument": [
        "Xay dung mot lap luan C-E-R day du ve viec co nen day ky nang phan bien bat buoc o dai hoc.",
        "Xay dung mot lap luan C-E-R day du ve viec co nen gioi han thoi gian dung TikTok cua thanh thieu nien.",
        "Xay dung mot lap luan C-E-R day du ve viec chinh phu co nen dung AI trong dich vu cong.",
        "Xay dung mot lap luan C-E-R day du ve viec co nen cam tui nilon dung mot lan.",
    ],
}

FALLACY_TEMPLATES = [
    (
        "khái quát hóa vội vàng",
        "{subject} chắc chắn đúng vì tôi thấy nhiều người xung quanh cũng nghĩ như vậy.",
    ),
    (
        "thiếu bằng chứng",
        "Có thể khẳng định rằng {subject} vì điều này nghe có vẻ hợp lý và ai cũng có thể thấy lợi ích của nó.",
    ),
    (
        "nguyên nhân giả",
        "Chỉ cần chấp nhận rằng {subject} thì vấn đề chắc chắn sẽ được giải quyết và kết quả sẽ tự động tốt hơn.",
    ),
    (
        "tuyệt đối hóa",
        "Không thể phủ nhận rằng {subject}, vì mọi quan điểm khác đều không hợp lý.",
    ),
    (
        "dựa vào số đông",
        "{subject} chắc chắn đúng vì nhiều người hiện nay đều đồng ý và làm theo.",
    ),
]

QUICK_REBUTTAL_INSTRUCTION = "Hãy chỉ ra lỗ hổng, giả định sai hoặc phản ví dụ."


def canonical_mode(mode: str | None) -> str:
    key = str(mode or "free_debate").strip().casefold().replace("-", "_").replace(" ", "_")
    key = MODE_ALIASES.get(key, key)
    return key if key in PROMPT_BANK or key == "free_debate" else "free_debate"


def _normalize_mode(mode: str | None) -> str:
    mode_key = canonical_mode(mode)
    return mode_key if mode_key in SUPPORTED_PROMPT_MODES else "claim_writing"


def _key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or "").casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("đ", "d").replace("Ä‘", "d")
    return " ".join(re.findall(r"[\w]+", normalized, flags=re.UNICODE))


def _tokens(text: str) -> set[str]:
    return {token for token in _key(text).split() if len(token) > 2}


def _too_similar(candidate: str, used_prompt: str) -> bool:
    candidate_key = _key(candidate)
    used_key = _key(used_prompt)
    if not candidate_key or not used_key:
        return False
    if candidate_key == used_key:
        return True
    if candidate_key in used_key or used_key in candidate_key:
        return True
    candidate_tokens = _tokens(candidate_key)
    used_tokens = _tokens(used_key)
    if not candidate_tokens or not used_tokens:
        return False
    overlap = len(candidate_tokens & used_tokens) / max(1, len(candidate_tokens | used_tokens))
    return overlap >= 0.72


def _stable_index(seed: str, size: int) -> int:
    if size <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % size


def _clean_sentence(text: str) -> str:
    clean = " ".join(str(text or "").strip().split())
    clean = re.sub(r"\s+([,.;?!:])", r"\1", clean)
    clean = re.sub(r"([,.;?!:])(?=\S)", r"\1 ", clean)
    if not clean:
        return ""
    clean = clean[0].upper() + clean[1:]
    if clean[-1] not in ".?!":
        clean += "."
    return clean


def _topic_to_claim_subject(topic_title: str) -> str:
    clean = " ".join(str(topic_title or "").strip().split()).rstrip(" ?.!").strip()
    if not clean:
        return "chủ đề này"

    should_prefix = re.match(r"^có nên\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if should_prefix:
        subject = should_prefix.group(1).strip()
        return f"việc {subject[0].lower() + subject[1:] if subject else 'thực hiện lựa chọn này'}"

    embedded_should = re.match(
        r"^(.+?)\s+có nên\s+(?:được\s+)?(.+?)(?:\s+không)?$",
        clean,
        flags=re.IGNORECASE,
    )
    if embedded_should:
        actor = embedded_should.group(1).strip()
        action = embedded_should.group(2).strip()
        subject = f"{actor} {action}".strip()
        return f"việc {subject[0].lower() + subject[1:]}"

    still_measure = re.match(
        r"^(.+?)\s+có còn là\s+(.+)$",
        clean,
        flags=re.IGNORECASE,
    )
    if still_measure:
        subject = f"{still_measure.group(1).strip()} là {still_measure.group(2).strip()}"
        return subject[0].lower() + subject[1:]

    is_question = re.match(
        r"^(.+?)\s+có phải là\s+(.+)$",
        clean,
        flags=re.IGNORECASE,
    )
    if is_question:
        subject = f"{is_question.group(1).strip()} là {is_question.group(2).strip()}"
        return subject[0].lower() + subject[1:]

    return clean


def _sanitize_weak_argument(text: str) -> str:
    clean = str(text or "").strip()
    clean = re.sub(
        r"^(?:phản biện\s+)?(?:lập|luận)\s*(?:luận|điểm)?\s*yếu\s*:?\s*",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.split(r"\s+Hãy chỉ ra\b", clean, maxsplit=1, flags=re.IGNORECASE)[0]
    clean = re.sub(
        r"\?\s+(?=(?:chắc chắn|rõ ràng|đương nhiên|vì)\b)",
        " ",
        clean,
        flags=re.IGNORECASE,
    )
    return _clean_sentence(clean)


def _get_topic_candidates(
    difficulty: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict]:
    def add_unique(base: list[dict], extras: list[dict]) -> list[dict]:
        seen = {str(item.get("id") or item.get("title")) for item in base}
        result = list(base)
        for item in extras:
            key = str(item.get("id") or item.get("title"))
            if key not in seen:
                result.append(item)
                seen.add(key)
        return result[:limit]

    try:
        minimum = min(max(1, limit), 3)
        candidates = list_topics(category=category, difficulty=difficulty, limit=limit)
        if len(candidates) >= minimum:
            return candidates

        recommended = recommended_topics(
            difficulty=difficulty,
            category=category,
            limit=limit,
        )
        candidates = add_unique(candidates, recommended)
        if len(candidates) >= minimum or candidates:
            return candidates

        return add_unique(candidates, list_topics(limit=limit))
    except Exception:
        return []


def _extract_previous_topics(used_prompts: list[str], previous_topics: list[str] | None = None) -> set[str]:
    titles = {_key(item) for item in (previous_topics or []) if _key(item)}
    for prompt in used_prompts:
        match = re.search(r"Chủ đề:\s*(.+?)(?:\n|$)", str(prompt), flags=re.IGNORECASE)
        if match:
            titles.add(_key(match.group(1)))
    return titles


def _choose_topic(
    candidates: list[dict],
    *,
    mode: str,
    round_number: int | None,
    session_id: str | None,
    difficulty: str | None,
    category: str | None,
    used_prompts: list[str],
    previous_topics: list[str] | None,
) -> dict | None:
    if not candidates:
        return None
    previous_keys = _extract_previous_topics(used_prompts, previous_topics)
    fresh = [topic for topic in candidates if _key(topic.get("title")) not in previous_keys]
    pool = fresh or candidates
    seed = f"{session_id or ''}:{mode}:{round_number or 0}:{difficulty or ''}:{category or ''}"
    return pool[_stable_index(seed, len(pool))]


def _claim_from_topic(topic_title: str) -> str:
    clean = topic_title.strip().rstrip("?")
    lowered = clean.casefold()
    if lowered.startswith("có nên "):
        return f"Nên {clean[7:].strip()} vì lựa chọn này có thể tạo ra lợi ích thiết thực và có thể kiểm chứng."
    return f"Nên ủng hộ quan điểm về '{clean}' vì nó có thể mang lại lợi ích thiết thực cho người học hoặc xã hội."


def _topic_metadata(topic: dict) -> dict:
    return {
        "topic": topic.get("title", ""),
        "topic_id": topic.get("id", ""),
        "category": topic.get("category", ""),
        "difficulty": topic.get("difficulty", ""),
    }


def _build_quick_rebuttal_prompt_from_topic(
    topic: dict,
    round_number: int | None = None,
) -> dict:
    title = str(topic.get("title") or "").strip()
    subject = _topic_to_claim_subject(title)
    template_index = _stable_index(
        f"{topic.get('id') or title}:{round_number or 0}",
        len(FALLACY_TEMPLATES),
    )
    fallacy_hint, template = FALLACY_TEMPLATES[template_index]
    weak_argument = _sanitize_weak_argument(template.format(subject=subject))
    return {
        "mode": "quick_rebuttal",
        "prompt_type": "weak_argument",
        "prompt": weak_argument,
        "weak_argument": weak_argument,
        "fallacy_hint": fallacy_hint,
        "instruction": QUICK_REBUTTAL_INSTRUCTION,
        "source": "topic_bank",
        **_topic_metadata(topic),
    }


def _finalize_prompt_result(result: dict) -> dict:
    finalized = dict(result or {})
    mode = canonical_mode(finalized.get("mode"))
    if mode != "free_debate":
        mode = _normalize_mode(mode)
    finalized["status"] = "success"
    finalized["mode"] = mode
    finalized.setdefault("warning", None)
    finalized.setdefault("topic", None)
    finalized.setdefault("scenario", None)
    finalized.setdefault("claim", None)
    finalized.setdefault("weak_argument", None)

    if mode == "quick_rebuttal":
        weak_argument = _sanitize_weak_argument(
            finalized.get("weak_argument") or finalized.get("prompt")
        )
        finalized["prompt_type"] = "weak_argument"
        finalized["weak_argument"] = weak_argument
        finalized["prompt"] = weak_argument
        finalized["instruction"] = QUICK_REBUTTAL_INSTRUCTION
    else:
        default_instructions = {
            "claim_writing": "Hãy viết một claim rõ ràng, thể hiện lập trường ủng hộ hoặc phản đối và có thể tranh luận được.",
            "find_evidence": "Hãy đưa ra bằng chứng cụ thể để hỗ trợ hoặc phản bác claim này.",
            "full_argument": "Hãy xây dựng một lập luận đầy đủ gồm Claim, Evidence và Reasoning theo lập trường ủng hộ hoặc phản đối.",
        }
        finalized.setdefault("instruction", default_instructions.get(mode, "Hãy trả lời đề bài luyện tập."))

    return finalized


def _build_topic_prompt(mode: str, topic: dict, *, round_number: int | None = None) -> dict:
    title = str(topic.get("title") or "").strip()
    metadata = _topic_metadata(topic)
    if mode == "claim_writing":
        instruction = "Hãy viết một claim rõ ràng, thể hiện lập trường ủng hộ hoặc phản đối và có thể tranh luận được."
        prompt = f"Chủ đề: {title}\n\n{instruction}"
        return {
            "mode": mode,
            "prompt_type": "scenario_prompt",
            "prompt": prompt,
            "instruction": instruction,
            "source": "topic_bank",
            **metadata,
        }

    if mode == "find_evidence":
        claim = _claim_from_topic(title)
        instruction = "Hãy đưa ra bằng chứng cụ thể để hỗ trợ hoặc phản bác claim này."
        prompt = f"Chủ đề: {title}\nClaim: {claim}\n\n{instruction}"
        return {
            "mode": mode,
            "prompt_type": "claim_prompt",
            "prompt": prompt,
            "claim": claim,
            "instruction": instruction,
            "source": "topic_bank",
            **metadata,
        }

    if mode == "quick_rebuttal":
        return _build_quick_rebuttal_prompt_from_topic(topic, round_number)

    instruction = "Hãy xây dựng một lập luận đầy đủ gồm Claim, Evidence và Reasoning theo lập trường ủng hộ hoặc phản đối."
    prompt = f": {title}\n\n{instruction}"
    return {
        "mode": mode,
        "prompt_type": "argument_builder",
        "prompt": prompt,
        "instruction": instruction,
        "source": "topic_bank",
        **metadata,
    }


def _fallback_prompt(mode: str, used_prompts: list[str], round_number: int | None) -> dict:
    fallback_mode = mode if mode in PROMPT_BANK else "claim_writing"
    candidates = PROMPT_BANK.get(fallback_mode, PROMPT_BANK["claim_writing"])
    offset = int(round_number or 0) % max(1, len(candidates))
    rotated = candidates[offset:] + candidates[:offset]
    for candidate in rotated:
        if not any(_too_similar(candidate, used_prompt) for used_prompt in used_prompts):
            return {
                "mode": fallback_mode,
                "prompt": candidate,
                "source": "prompt_bank_fallback",
                "prompt_type": "fallback_prompt",
            }

    base = candidates[offset] if candidates else "Hay tao mot nhiem vu luyen tap tranh bien moi."
    return {
        "mode": fallback_mode,
        "prompt": f"{base} Chon goc nhin moi va khong lap lai cac prompt truoc trong phien.",
        "source": "fallback_variant",
        "prompt_type": "fallback_prompt",
    }


def build_practice_prompt(
    mode: str,
    *,
    topic: str = "",
    used_prompts: list[str] | None = None,
    round_number: int | None = None,
    session_id: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    previous_topics: list[str] | None = None,
    avoid_repeating: bool = True,
) -> dict:
    mode_key = canonical_mode(mode)
    used = [
        str(item)
        for item in (used_prompts or [])
        if avoid_repeating and str(item).strip()
    ]
    prior_topics = previous_topics if avoid_repeating else []
    if mode_key == "free_debate":
        return _finalize_prompt_result({
            "mode": mode_key,
            "prompt": "Hay tiep tuc tranh bien tu do voi lap luan moi co claim, evidence va reasoning ro rang.",
            "source": "free_debate_default",
            "prompt_type": "free_debate_default",
        })

    prompt_mode = _normalize_mode(mode_key)
    candidates = _get_topic_candidates(difficulty=difficulty, category=category, limit=50)
    selected_topic = _choose_topic(
        candidates,
        mode=prompt_mode,
        round_number=round_number,
        session_id=session_id,
        difficulty=difficulty,
        category=category,
        used_prompts=used,
        previous_topics=prior_topics,
    )

    if selected_topic:
        result = _build_topic_prompt(prompt_mode, selected_topic, round_number=round_number)
        if not any(_too_similar(result["prompt"], used_prompt) for used_prompt in used):
            return _finalize_prompt_result(result)

        fresh_topics = [
            candidate
            for candidate in candidates
            if candidate.get("id") != selected_topic.get("id")
        ]
        for candidate in fresh_topics:
            result = _build_topic_prompt(prompt_mode, candidate, round_number=round_number)
            if not any(_too_similar(result["prompt"], used_prompt) for used_prompt in used):
                return _finalize_prompt_result(result)

        if result:
            result["prompt"] = (
                f"{result['prompt']}\n\nHãy chọn một góc nhìn mới và tránh lặp lại prompt trước trong phiên."
            )
            result["source"] = "topic_bank_variant"
            return _finalize_prompt_result(result)

    if topic:
        manual_topic = {
            "id": "",
            "title": topic,
            "category": category or "",
            "difficulty": difficulty or "",
        }
        result = _build_topic_prompt(prompt_mode, manual_topic, round_number=round_number)
        if not any(_too_similar(result["prompt"], used_prompt) for used_prompt in used):
            result["source"] = "provided_topic"
            return _finalize_prompt_result(result)

    return _finalize_prompt_result(_fallback_prompt(prompt_mode, used, round_number))
