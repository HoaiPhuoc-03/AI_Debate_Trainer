from __future__ import annotations

import hashlib
import re
import unicodedata

from app.data.quick_rebuttal_prompts import QUICK_REBUTTAL_PROMPTS
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
        "Luận điểm yếu: Học tiếng Anh hiện nay gần như không còn cần thiết vì các công cụ dịch thuật AI đã phát triển rất mạnh. Chỉ cần có điện thoại, học sinh có thể dịch văn bản, hội thoại và tài liệu nước ngoài trong vài giây. Điều này cho thấy việc dành nhiều năm để học từ vựng, ngữ pháp và phát âm tiếng Anh là khá lãng phí. Trong tương lai AI chắc chắn sẽ dịch chính xác mọi tình huống giao tiếp nên con người không cần tự học ngoại ngữ nữa. Vì vậy, nhà trường nên giảm mạnh thời lượng học tiếng Anh và thay bằng các tiết học sử dụng công nghệ dịch thuật.",
        "Luận điểm yếu: Không cần học đại học vì đã có nhiều người thành công mà không cần bằng cấp. Những câu chuyện như Bill Gates hay một vài doanh nhân nổi tiếng cho thấy kinh nghiệm thực tế quan trọng hơn giảng đường. Nếu một số người có thể bỏ học mà vẫn giàu có, sinh viên bình thường cũng có thể đi theo con đường tương tự. Thay vì tốn bốn năm học lý thuyết, người trẻ nên đi làm sớm để học từ thị trường. Vì vậy, đại học không còn là lựa chọn đáng ưu tiên.",
        "Luận điểm yếu: Nên cấm xe máy ở thành phố vì ngày nào cũng có tin về tai nạn giao thông. Khi xe máy biến mất, đường phố chắc chắn sẽ an toàn và văn minh hơn. Người dân có thể chuyển sang xe buýt hoặc các phương tiện khác mà không gặp trở ngại lớn. Nếu vẫn cho xe máy lưu thông, tình trạng ùn tắc và tai nạn sẽ không bao giờ được giải quyết. Vì vậy, cấm xe máy là cách nhanh nhất để cải thiện giao thông đô thị.",
        "Luận điểm yếu: Mạng xã hội không gây ảnh hưởng nghiêm trọng đến khả năng tập trung vì hầu hết học sinh vẫn dùng mỗi ngày. Nếu thật sự có hại, phụ huynh và giáo viên đã cấm hoàn toàn từ lâu. Nhiều bạn vẫn đạt điểm tốt dù thường xuyên xem video ngắn, nên không thể nói mạng xã hội làm giảm hiệu quả học tập. Vấn đề chính nằm ở cách quản lý thời gian của từng người chứ không phải nền tảng. Vì vậy, không cần đặt ra giới hạn đặc biệt đối với mạng xã hội.",
        "Luận điểm yếu: Có nên cấm túi nilon dùng một lần không còn là câu hỏi cần tranh luận nhiều vì ai cũng biết nhựa gây ô nhiễm. Chỉ cần cấm loại túi này, môi trường sẽ sạch hơn rõ rệt và người dân sẽ tự chuyển sang lựa chọn xanh. Những khó khăn của cửa hàng nhỏ hay người tiêu dùng chỉ là vấn đề thói quen ban đầu. Nếu chính sách tốt cho môi trường thì không nên trì hoãn vì vài bất tiện ngắn hạn. Vì vậy, lệnh cấm nên được áp dụng ngay trên diện rộng.",
    ],
    "full_argument": [
        "Xay dung mot lap luan C-E-R day du ve viec co nen day ky nang phan bien bat buoc o dai hoc.",
        "Xay dung mot lap luan C-E-R day du ve viec co nen gioi han thoi gian dung TikTok cua thanh thieu nien.",
        "Xay dung mot lap luan C-E-R day du ve viec chinh phu co nen dung AI trong dich vu cong.",
        "Xay dung mot lap luan C-E-R day du ve viec co nen cam tui nilon dung mot lan.",
    ],
}

FALLACY_TEMPLATES = [
    {
        "fallacy_hint": "khái quát hóa vội vàng",
        "target_flaws": ["khái quát hóa vội vàng", "dựa vào vài ví dụ", "thiếu dữ liệu đại diện"],
        "template": (
            "Luận điểm yếu: Gần đây tôi thấy rất nhiều ví dụ cho thấy {subject_statement} là hướng đi đúng. "
            "Bạn bè, người thân và vài câu chuyện trên mạng đều cho kết quả khá tích cực. "
            "Từ những trường hợp đó có thể suy ra rằng phần lớn người khác cũng sẽ nhận được lợi ích tương tự. "
            "Vì vậy, không cần mất quá nhiều thời gian kiểm chứng bằng nghiên cứu hay số liệu rộng hơn. "
            "Nhà trường và xã hội nên nhanh chóng ủng hộ {subject_statement} thay vì tiếp tục tranh luận."
        ),
    },
    {
        "fallacy_hint": "dựa vào số đông",
        "target_flaws": ["dựa vào số đông", "nhầm phổ biến với đúng", "thiếu tiêu chí đánh giá"],
        "template": (
            "Luận điểm yếu: Rất nhiều người hiện nay đã đồng ý rằng {subject_statement} là lựa chọn hợp lý. "
            "Khi một quan điểm được nhiều phụ huynh, học sinh và cộng đồng ủng hộ, nó thường phản ánh nhu cầu thật. "
            "Nếu phần đông đều nghĩ như vậy thì việc tiếp tục nghi ngờ chỉ làm quá trình thay đổi chậm lại. "
            "Những người phản đối có lẽ đang chưa bắt kịp xu hướng chung của xã hội. "
            "Vì thế, quyết định tốt nhất là đi theo lựa chọn mà đa số đang ủng hộ."
        ),
    },
    {
        "fallacy_hint": "thiếu bằng chứng",
        "target_flaws": ["thiếu bằng chứng", "khẳng định không có dữ liệu", "dựa vào cảm giác hợp lý"],
        "template": (
            "Luận điểm yếu: Có thể thấy khá rõ rằng {subject_statement} sẽ mang lại nhiều lợi ích thiết thực. "
            "Điều này nghe hợp lý vì nó phù hợp với cách xã hội đang thay đổi và nhu cầu của nhiều người. "
            "Dù chưa có số liệu cụ thể, ta vẫn có thể dự đoán kết quả tích cực dựa trên quan sát thông thường. "
            "Nếu cứ chờ nghiên cứu đầy đủ thì chúng ta sẽ bỏ lỡ thời điểm hành động tốt nhất. "
            "Vì vậy, nên chấp nhận quan điểm này trước rồi điều chỉnh sau nếu cần."
        ),
    },
    {
        "fallacy_hint": "nguyên nhân giả",
        "target_flaws": ["nguyên nhân giả", "đơn giản hóa quan hệ nhân quả", "bỏ qua yếu tố khác"],
        "template": (
            "Luận điểm yếu: Nếu thực hiện {subject_statement}, vấn đề hiện nay gần như sẽ được giải quyết từ gốc. "
            "Nguyên nhân chính của khó khăn nằm ở việc chúng ta chưa dám chọn hướng đi này một cách dứt khoát. "
            "Một khi thay đổi được áp dụng, hành vi của mọi người sẽ tự điều chỉnh theo hướng tích cực hơn. "
            "Các yếu tố khác như chi phí, điều kiện thực hiện hay khác biệt giữa từng nhóm không quá quan trọng. "
            "Vì vậy, chỉ cần thông qua lựa chọn này là kết quả tốt sẽ xuất hiện."
        ),
    },
    {
        "fallacy_hint": "tuyệt đối hóa",
        "target_flaws": ["tuyệt đối hóa", "bỏ qua ngoại lệ", "khẳng định quá mức"],
        "template": (
            "Luận điểm yếu: {subject_statement_cap} là lựa chọn đúng trong hầu hết mọi hoàn cảnh. "
            "Những lo ngại thường được nêu ra chỉ là các trường hợp nhỏ và không làm thay đổi bản chất vấn đề. "
            "Khi một giải pháp đã có lợi ích rõ ràng, ta không nên để vài ngoại lệ cản trở quyết định chung. "
            "Nếu cứ tính đến mọi tình huống đặc biệt, xã hội sẽ không bao giờ có chính sách đủ mạnh. "
            "Do đó, nên xem quan điểm này như hướng xử lý gần như chắc chắn đúng."
        ),
    },
    {
        "fallacy_hint": "đánh tráo vấn đề",
        "target_flaws": ["đánh tráo vấn đề", "né câu hỏi chính", "chuyển trọng tâm sang lợi ích phụ"],
        "template": (
            "Luận điểm yếu: Khi bàn về {subject_statement}, điều quan trọng nhất là thái độ cởi mở với đổi mới. "
            "Những người phản đối thường tập trung quá nhiều vào rủi ro mà quên rằng xã hội luôn cần thay đổi. "
            "Nếu một lựa chọn giúp chúng ta trông hiện đại và linh hoạt hơn, nó đã có giá trị rất lớn. "
            "Việc hỏi liệu nó có thật sự hiệu quả trong từng trường hợp chỉ làm cuộc tranh luận trở nên rườm rà. "
            "Vì vậy, nên ủng hộ quan điểm này để thể hiện tinh thần tiến bộ."
        ),
    },
    {
        "fallacy_hint": "người rơm",
        "target_flaws": ["người rơm", "bóp méo quan điểm phản đối", "tấn công phiên bản yếu hơn"],
        "template": (
            "Luận điểm yếu: Những người phản đối {subject_statement} thường chỉ muốn giữ nguyên cách làm cũ. "
            "Họ dường như cho rằng mọi thay đổi đều nguy hiểm và người học không thể thích nghi với điều mới. "
            "Cách nghĩ đó quá bảo thủ trong một xã hội đang phát triển nhanh. "
            "Nếu cứ nghe theo họ, chúng ta sẽ bỏ lỡ nhiều cơ hội cải thiện cuộc sống và giáo dục. "
            "Vì vậy, quan điểm phản đối không thật sự đáng cân nhắc."
        ),
    },
    {
        "fallacy_hint": "lưỡng phân giả",
        "target_flaws": ["lưỡng phân giả", "ép chỉ còn hai lựa chọn", "bỏ qua phương án trung gian"],
        "template": (
            "Luận điểm yếu: Về {subject_statement}, chúng ta chỉ có hai lựa chọn rõ ràng. "
            "Hoặc ủng hộ hoàn toàn để xã hội tiến lên, hoặc phản đối và chấp nhận tụt lại phía sau. "
            "Những phương án thỏa hiệp thường chỉ làm chính sách yếu đi và khiến mọi người khó thực hiện. "
            "Trong các vấn đề quan trọng, quyết định nửa vời thường còn tệ hơn không làm gì. "
            "Vì vậy, cần chọn hẳn một phía và ủng hộ quan điểm này một cách dứt khoát."
        ),
    },
    {
        "fallacy_hint": "trượt dốc",
        "target_flaws": ["trượt dốc", "phóng đại hệ quả", "thiếu liên kết nhân quả"],
        "template": (
            "Luận điểm yếu: Nếu không chấp nhận {subject_statement} ngay từ bây giờ, hậu quả sẽ ngày càng nghiêm trọng. "
            "Ban đầu có thể chỉ là vài bất tiện nhỏ, nhưng dần dần xã hội sẽ mất khả năng thích nghi với thay đổi. "
            "Khi đã chậm một bước, chúng ta sẽ tiếp tục chậm trong nhiều quyết định khác. "
            "Cuối cùng, cả hệ thống có thể trở nên lạc hậu so với nhu cầu thực tế. "
            "Vì vậy, lựa chọn này cần được áp dụng sớm để tránh chuỗi hậu quả xấu."
        ),
    },
    {
        "fallacy_hint": "chọn lọc bằng chứng",
        "target_flaws": ["chọn lọc bằng chứng", "bỏ qua phản ví dụ", "thiếu so sánh cân bằng"],
        "template": (
            "Luận điểm yếu: Có nhiều ví dụ cho thấy {subject_statement} đem lại kết quả tốt. "
            "Một số trường hợp được chia sẻ trên báo chí và mạng xã hội cho thấy người tham gia cảm thấy hài lòng hơn. "
            "Những trường hợp chưa thành công có thể chỉ là do cách triển khai chưa đúng hoặc do người dùng chưa quen. "
            "Vì các ví dụ tích cực đã đủ thuyết phục, ta không cần đặt nặng những dữ liệu trái chiều. "
            "Do đó, nên xem đây là hướng đi có lợi và mở rộng nhanh hơn."
        ),
    },
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


def _lower_first(text: str) -> str:
    clean = str(text or "").strip()
    return clean[:1].lower() + clean[1:] if clean else ""


def _strip_final_question_particle(text: str) -> str:
    return re.sub(r"\s+không$", "", str(text or "").strip(), flags=re.IGNORECASE).strip()


def topic_to_subject_statement(title: str) -> str:
    clean = " ".join(str(title or "").strip().split()).rstrip(" ?.!").strip()
    if not clean:
        return "chủ đề này"

    should_prefix = re.match(r"^có nên\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if should_prefix:
        action = _strip_final_question_particle(should_prefix.group(1))
        return f"việc {_lower_first(action) if action else 'thực hiện lựa chọn này'}"

    embedded_should = re.match(
        r"^(.+?)\s+có nên\s+(.+?)(?:\s+không)?$",
        clean,
        flags=re.IGNORECASE,
    )
    if embedded_should:
        actor = embedded_should.group(1).strip()
        action = _strip_final_question_particle(embedded_should.group(2))
        subject = f"{actor} {action}".strip()
        return f"việc {_lower_first(subject)}"

    effect_question = re.match(
        r"^(.+?)\s+có\s+(làm|gây|ảnh hưởng|giúp|tạo|mang lại|dẫn đến)\s+(.+)$",
        clean,
        flags=re.IGNORECASE,
    )
    if effect_question:
        subject = (
            f"{effect_question.group(1).strip()} "
            f"{effect_question.group(2).strip()} "
            f"{_strip_final_question_particle(effect_question.group(3))}"
        )
        return f"việc {_lower_first(subject)}"

    still_measure = re.match(
        r"^(.+?)\s+có còn là\s+(.+)$",
        clean,
        flags=re.IGNORECASE,
    )
    if still_measure:
        subject = f"{still_measure.group(1).strip()} là {_strip_final_question_particle(still_measure.group(2))}"
        return f"việc {_lower_first(subject)}"

    is_question = re.match(
        r"^(.+?)\s+có phải là\s+(.+)$",
        clean,
        flags=re.IGNORECASE,
    )
    if is_question:
        subject = f"{is_question.group(1).strip()} là {_strip_final_question_particle(is_question.group(2))}"
        return f"việc {_lower_first(subject)}"

    return _lower_first(clean)


def _topic_to_claim_subject(topic_title: str) -> str:
    return topic_to_subject_statement(topic_title)


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


SPECIFIC_CLAIMS_MAPPING = {
    "edu_ai_homework": "Học sinh sử dụng công cụ AI để làm bài tập sẽ giúp cá nhân hóa quá trình học tập và tự sửa lỗi sai hiệu quả hơn.",
    "edu_phone_ban": "Cấm điện thoại trong giờ học giúp học sinh tăng mức độ tập trung nghe giảng và giảm thiểu sự xao nhãng bởi mạng xã hội.",
    "edu_no_homework": "Việc xóa bỏ bài tập về nhà giúp học sinh giảm căng thẳng tinh thần và có thêm thời gian tham gia các hoạt động thể chất.",
    "edu_grades_measure": "Điểm số không còn là thước đo toàn diện vì nó bỏ qua các kỹ năng mềm quan trọng như tư duy sáng tạo và làm việc nhóm.",
    "edu_critical_thinking_university": "Bắt buộc học kỹ năng phản biện giúp sinh viên nâng cao năng lực phân tích thông tin đa chiều và tránh bẫy tin giả.",
    "tech_ai_teacher": "AI nên thay thế giáo viên ở các nhiệm vụ chấm điểm và soạn giáo án để thầy cô có nhiều thời gian tương tác, định hướng tâm lý cho học sinh.",
    "tech_social_focus": "Mạng xã hội làm giảm khả năng tập trung sâu của người dùng do thói quen tiếp nhận các nội dung ngắn, giật gân liên tục.",
    "tech_tiktok_time_limit": "Giới hạn thời gian sử dụng TikTok giúp thanh thiếu niên cải thiện chất lượng giấc ngủ và giảm nguy cơ mắc chứng lo âu.",
    "tech_personal_data_property": "Dữ liệu cá nhân nên được xem là tài sản riêng để người dùng có quyền yêu cầu các công ty công nghệ trả phí khi khai thác thông tin của họ.",
    "tech_robot_eldercare": "Robot nên được dùng để chăm sóc người cao tuổi nhằm hỗ trợ các công việc thể chất nặng nhọc và theo dõi chỉ số sức khỏe liên tục.",
    "soc_cyberbullying_penalty": "Phạt nặng hành vi bắt nạt trên mạng sẽ răn đe các đối tượng xấu và giảm tỷ lệ mắc bệnh trầm cảm ở nạn nhân.",
    "soc_young_independent": "Người trẻ sống tự lập sớm giúp rèn luyện khả năng quản lý tài chính cá nhân và nâng cao tính tự chịu trách nhiệm.",
    "soc_remote_work": "Làm việc từ xa đem lại hiệu quả cao hơn nhờ giảm thiểu áp lực thời gian di chuyển và cho phép nhân viên tự chủ không gian làm việc.",
    "soc_public_transport": "Khuyến khích giao thông công cộng giúp giảm ùn tắc giao thông vào giờ cao điểm và giảm thiểu đáng kể lượng khí thải carbon đô thị.",
    "soc_celeb_role_model": "Người nổi tiếng có trách nhiệm đạo đức phải làm gương vì hành vi của họ có sức ảnh hưởng trực tiếp đến lối sống của giới trẻ.",
    "eco_personal_finance_school": "Dạy quản lý tài chính cá nhân từ cấp 3 giúp học sinh hình thành thói quen tiết kiệm và tránh được các bẫy nợ nần khi bước vào đại học.",
    "eco_online_spending": "Mua sắm online làm người trẻ chi tiêu mất kiểm soát do sự tiện lợi của các ví điện tử và các chiến dịch khuyến mãi liên tục.",
    "eco_green_tax": "Đánh thuế cao sản phẩm gây hại môi trường sẽ thúc đẩy doanh nghiệp chuyển đổi sang công nghệ sản xuất xanh, bền vững hơn.",
    "eco_startup_university": "Ưu tiên hỗ trợ startup trong đại học giúp thương mại hóa các đề tài nghiên cứu khoa học của sinh viên và giảng viên.",
    "eco_minimum_wage_yearly": "Tăng lương tối thiểu hằng năm giúp bảo vệ sức mua của người lao động nghèo trước áp lực lạm phát và bão giá.",
    "eth_ai_writing_cheating": "Dùng AI viết bài luận là gian lận học thuật vì nó làm suy giảm khả năng tự tư duy và diễn đạt ngôn ngữ của chính người học.",
    "eth_ai_camera_school": "Sử dụng camera AI giám sát học sinh vi phạm nghiêm trọng quyền riêng tư học đường và gây ra áp lực tâm lý căng thẳng.",
    "eth_public_grades": "Công khai điểm số gây ra sự so sánh tiêu cực và làm tổn thương lòng tự trọng của những học sinh có học lực trung bình hoặc yếu.",
    "eth_ai_hiring": "AI không nên có quyền quyết định tuyển dụng vì các thuật toán có thể kế thừa và phóng đại các thiên kiến phân biệt đối xử từ dữ liệu cũ.",
    "eth_cancel_scandal": "Tha thứ cho người nổi tiếng sau scandal giúp khuyến khích họ sửa sai và đóng góp tích cực lại cho cộng đồng.",
    "pol_student_policy_voice": "Cho học sinh góp ý chính sách giúp các quy định học đường sát với thực tế học tập và nhu cầu phát triển của thế hệ trẻ.",
    "pol_digital_media_literacy": "Bắt buộc học kỹ năng truyền thông số giúp nâng cao bộ lọc thông tin của công dân trước vấn nạn tin giả và lừa đảo mạng.",
    "pol_fake_news_control": "Siết chặt quản lý tin giả trên mạng xã hội giúp bảo vệ trật tự an toàn xã hội và ngăn chặn các thông tin sai lệch gây hoang mang dư luận.",
    "pol_ai_public_service": "Dùng AI trong dịch vụ công giúp chính phủ giải quyết nhanh chóng các thủ tục hành chính lặp đi lặp lại và giảm thiểu phiền hà cho người dân.",
    "pol_digital_citizenship_school": "Mở rộng giáo dục công dân số giúp học sinh biết cách tự bảo vệ thông tin cá nhân và hành xử văn minh trên không gian mạng.",
    "env_plastic_bag_ban": "Cấm túi nilon dùng một lần buộc người dân thay đổi thói quen tiêu dùng sang sử dụng các loại túi tự hủy sinh học thân thiện hơn.",
    "env_school_recycling": "Bắt buộc phân loại rác ở trường học giúp xây dựng ý thức bảo vệ môi trường và giảm chi phí xử lý chất thải sinh hoạt.",
    "env_gas_car_limit": "Hạn chế xe xăng ở đô thị lớn giúp cải thiện đáng kể chỉ số chất lượng không khí (AQI) và giảm các bệnh về đường hô hấp cho người dân.",
    "env_consumer_climate": "Người tiêu dùng có trách nhiệm lớn với biến đổi khí hậu vì thói quen mua sắm quá mức của họ đang thúc đẩy các nhà máy sản xuất cạn kiệt tài nguyên.",
    "env_energy_price_saving": "Tăng giá điện là biện pháp kinh tế trực tiếp thúc đẩy người dân và doanh nghiệp tắt các thiết bị không sử dụng để tiết kiệm chi phí.",
    "health_sugary_drinks_school": "Giới hạn đồ uống có đường trong căng tin giúp kiểm soát tỷ lệ học sinh bị béo phì và mắc các bệnh răng miệng từ sớm.",
    "health_mental_health_subject": "Dạy sức khỏe tinh thần chính khóa giúp học sinh biết cách nhận diện căng thẳng, trầm cảm và tự tìm kiếm sự giúp đỡ khi cần thiết.",
    "health_fast_food_ads": "Cấm quảng cáo đồ ăn nhanh cho trẻ em giúp ngăn chặn thói quen ăn uống không lành mạnh do bị tác động bởi các hình ảnh hấp dẫn trên truyền hình.",
    "health_sleep_vs_extra_classes": "Ngủ đủ giấc giúp não bộ học sinh tái tạo năng lượng, nâng cao khả năng ghi nhớ và học tập hiệu quả hơn so với việc cố nhồi nhét học thêm.",
    "health_school_psych_check": "Kiểm tra sức khỏe tâm lý định kỳ giúp phát hiện sớm các dấu hiệu trầm cảm học đường và bạo lực học đường để can thiệp kịp thời.",
    "culture_online_negative_reviews": "Review tiêu cực trên mạng cần bị kiểm soát khi nó biến tướng thành các hành vi bôi nhọ, tống tiền hoặc triệt hạ doanh nghiệp một cách cố ý.",
    "culture_movies_youth_behavior": "Phim ảnh có ảnh hưởng mạnh vì giới trẻ có xu hướng bắt chước các hành động bạo lực hoặc lối sống của nhân vật chính trong phim.",
    "culture_fandom_pressure": "Văn hóa thần tượng gây áp lực tài chính và thời gian lớn cho học sinh do phong trào mua vật phẩm ủng hộ và cày lượt xem cho thần tượng.",
    "culture_traditional_values_school": "Dạy nhiều về văn hóa truyền thống giúp học sinh giữ gìn bản sắc dân tộc trong thời kỳ hội nhập toàn cầu hóa.",
    "culture_global_content": "Nội dung giải trí quốc tế lấn lướt làm giới trẻ thờ ơ với nghệ thuật dân gian và các ngày lễ truyền thống trong nước.",
    "media_influencer_ads": "Influencer phải chịu trách nhiệm pháp lý khi quảng cáo các sản phẩm kém chất lượng, gây thiệt hại sức khỏe hoặc tiền bạc cho người theo dõi.",
    "media_short_video_harm": "Hạn chế video ngắn có nội dung độc hại giúp bảo vệ trẻ em khỏi các trào lưu nguy hiểm và lệch lạc nhận thức.",
    "media_fake_news_label": "Gắn nhãn cảnh báo tin giả giúp người đọc cảnh giác hơn và hạn chế việc chia sẻ rộng rãi các thông tin thất thiệt chưa kiểm chứng.",
    "media_children_fast_news": "Dạy cách kiểm chứng thông tin giúp học sinh không bị dắt mũi bởi tin đồn nhảm và biết cách tìm kiếm các nguồn tin chính thống.",
    "media_comments_real_name": "Bắt buộc dùng tên thật khi bình luận sẽ giảm thiểu vấn nạn bạo lực ngôn từ và nâng cao văn hóa ứng xử trên mạng xã hội.",
}


def _claim_from_topic(topic_title: str, topic_id: str | None = None) -> str:
    if topic_id and topic_id in SPECIFIC_CLAIMS_MAPPING:
        return SPECIFIC_CLAIMS_MAPPING[topic_id]

    clean = " ".join(str(topic_title or "").strip().split()).rstrip(" ?.!").strip()
    if not clean:
        return "Nên triển khai giải pháp này để mang lại lợi ích thiết thực và phát triển bền vững cho cộng đồng."

    # Pattern 1: "Có nên [action] (không)?" -> "Nên [action]..."
    match = re.match(r"^có nên\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        return f"Nên {action} vì điều này mang lại nhiều lợi ích thiết thực và phát triển bền vững."

    # Pattern 2: "[actor] có nên [action] (không)?" -> "[actor] nên [action]..."
    match = re.match(r"^(.+?)\s+có nên\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        actor = match.group(1).strip()
        action = match.group(2).strip()
        return f"{actor} nên {action} để cải thiện hiệu quả tổng thể và tối ưu hóa các nguồn lực."

    # Pattern 3: "[subject] có phải là [definition] (không)?" -> "[subject] là [definition]..."
    match = re.match(r"^(.+?)\s+có phải là\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        subject = match.group(1).strip()
        definition = match.group(2).strip()
        return f"{subject} là {definition} do tác động trực tiếp đến nhận thức và hành vi."

    # Pattern 4: "[subject] có còn là [definition] (không)?" -> "[subject] vẫn là [definition]..."
    match = re.match(r"^(.+?)\s+có còn là\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        subject = match.group(1).strip()
        definition = match.group(2).strip()
        return f"{subject} vẫn là {definition} vì nó đóng vai trò cốt lõi định hình giá trị lâu dài."

    # Pattern 5: "[subject] có làm/gây [effect] (không)?" -> "[subject] làm/gây [effect]..."
    match = re.match(r"^(.+?)\s+có\s+(làm|gây|ảnh hưởng|giúp|tạo|mang lại|dẫn đến)\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        subject = match.group(1).strip()
        verb = match.group(2).strip()
        effect = match.group(3).strip()
        return f"{subject} {verb} {effect} dưới tác động của sự thay đổi thói quen xã hội."

    # Pattern 6: "[subject] có [adjective] hơn [subject2] (không)?" -> "[subject] [adjective] hơn [subject2]..."
    match = re.match(r"^(.+?)\s+có\s+(.+?)\s+hơn\s+(.+?)(?:\s+không)?$", clean, flags=re.IGNORECASE)
    if match:
        subj1 = match.group(1).strip()
        adj = match.group(2).strip()
        subj2 = match.group(3).strip()
        return f"{subj1} {adj} hơn {subj2} nhờ khả năng tiết kiệm chi phí và tăng tính chủ động."

    # Default fallback: Remove trailing "không" and clean up
    clean_no_khong = re.sub(r"\s+không$", "", clean, flags=re.IGNORECASE).strip()
    if clean_no_khong:
        return f"{clean_no_khong} nhằm hướng tới sự phát triển toàn diện và nâng cao chất lượng cuộc sống."

    return f"Nên ủng hộ quan điểm về '{clean}' để đạt được hiệu quả tối ưu."


def _topic_metadata(topic: dict) -> dict:
    return {
        "topic": topic.get("title", ""),
        "topic_id": topic.get("id", ""),
        "category": topic.get("category", ""),
        "difficulty": topic.get("difficulty", ""),
    }


def get_quick_rebuttal_prompt_from_bank(
    topic: dict,
    round_number: int = 1,
) -> dict | None:
    topic_title = (topic.get("title") or topic.get("topic") or topic.get("name") or "").strip()
    topic_id = topic.get("id") or topic.get("topic_id") or ""

    candidates = [
        item
        for item in QUICK_REBUTTAL_PROMPTS
        if item.get("topic_id") == topic_id or item.get("topic") == topic_title
    ]

    if not candidates:
        return None

    safe_round = max(int(round_number or 1), 1)
    selected = candidates[(safe_round - 1) % len(candidates)]

    return {
        "mode": "quick_rebuttal",
        "prompt_type": "weak_argument",
        "topic": selected.get("topic") or topic_title,
        "topic_id": selected.get("topic_id") or topic_id,
        "category": selected.get("category") or topic.get("category"),
        "difficulty": selected.get("difficulty") or topic.get("difficulty"),
        "weak_argument": selected["weak_argument"],
        "fallacy_hint": selected.get("fallacy_hint"),
        "target_flaws": selected.get("target_flaws", []),
        "expected_rebuttal_points": selected.get("expected_rebuttal_points", []),
        "instruction": "Hãy chỉ ra lỗ hổng, giả định sai hoặc phản ví dụ.",
        "source": "local_prompt_bank",
    }


def _build_quick_rebuttal_prompt_from_topic(
    topic: dict,
    round_number: int | None = None,
) -> dict:
    title = str(topic.get("title") or "").strip()
    subject_statement = topic_to_subject_statement(title)
    template_index = _stable_index(
        f"{topic.get('id') or title}:{round_number or 0}",
        len(FALLACY_TEMPLATES),
    )
    template_data = FALLACY_TEMPLATES[template_index]
    fallacy_hint = str(template_data["fallacy_hint"])
    target_flaws = list(template_data.get("target_flaws") or [fallacy_hint])
    weak_argument = _sanitize_weak_argument(
        template_data["template"].format(
            subject_statement=subject_statement,
            subject_statement_cap=_clean_sentence(subject_statement).rstrip("."),
        )
    )
    return {
        "mode": "quick_rebuttal",
        "prompt_type": "weak_argument",
        "prompt": weak_argument,
        "weak_argument": weak_argument,
        "fallacy_hint": fallacy_hint,
        "target_flaws": target_flaws,
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
    finalized.setdefault("target_flaws", None)
    finalized.setdefault("expected_rebuttal_points", None)

    if mode == "quick_rebuttal":
        weak_argument = _sanitize_weak_argument(
            finalized.get("weak_argument") or finalized.get("prompt")
        )
        finalized["prompt_type"] = "weak_argument"
        finalized["weak_argument"] = weak_argument
        finalized["prompt"] = weak_argument
        finalized["fallacy_hint"] = finalized.get("fallacy_hint") or "thiếu bằng chứng / giả định chưa chứng minh"
        target_flaws = finalized.get("target_flaws") or []
        if isinstance(target_flaws, str):
            target_flaws = [item.strip() for item in target_flaws.split(",") if item.strip()]
        finalized["target_flaws"] = list(target_flaws) or [finalized["fallacy_hint"]]
        expected_rebuttal_points = finalized.get("expected_rebuttal_points") or []
        if isinstance(expected_rebuttal_points, str):
            expected_rebuttal_points = [
                item.strip()
                for item in expected_rebuttal_points.split(",")
                if item.strip()
            ]
        finalized["expected_rebuttal_points"] = list(expected_rebuttal_points)
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
        claim = _claim_from_topic(title, topic_id=topic.get("id"))
        instruction = "Hãy đưa ra bằng chứng cụ thể để hỗ trợ hoặc phản bác claim này."
        prompt = claim
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
        prompt_from_bank = get_quick_rebuttal_prompt_from_bank(topic, round_number or 1)
        if prompt_from_bank:
            prompt_from_bank["prompt"] = prompt_from_bank["weak_argument"]
            return prompt_from_bank

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
