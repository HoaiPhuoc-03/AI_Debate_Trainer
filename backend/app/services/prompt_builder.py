# ---------------------------------------------------------------------------
# prompt_builder.py
#
# GEPA prompt design — key principles:
#
# 1. LANGUAGE LOCK: System prompt written IN Vietnamese to lock register.
#
# 2. NO NUMERIC ANCHORS IN EXAMPLES: Few-shot examples contain NO score
#    numbers. Any number in the prompt becomes an anchor — the model
#    interpolates between example scores regardless of the actual argument.
#    Instead, examples show only qualitative labels (THẤP/TRUNG BÌNH/CAO).
#
# 3. CHAIN-OF-THOUGHT BEFORE SCORING: The prompt requires the model to
#    explicitly quote/paraphrase the argument and identify its evidence
#    BEFORE filling in scores. This forces argument-specific evaluation
#    rather than canned responses.
#
# 4. EXPLICIT EVIDENCE DETECTION: Named examples of what counts as
#    evidence vs. not, because the model misclassifies this.
#
# 5. REBUTTAL MUST REFERENCE ARGUMENT: Explicit constraint that the
#    rebuttal must mention specific content from the argument.
#
# 6. STRING PLACEHOLDERS IN SCHEMA: No numeric defaults in the JSON
#    template — they act as anchors.
# ---------------------------------------------------------------------------


def _language_name(language: str) -> str:
    return "tiếng Việt" if language == "vi" else "English"


def _tone_rule(age_group: str) -> str:
    rules = {
        "teen": "Khích lệ, dễ hiểu, ví dụ gần gũi.",
        "adult": "Rõ ràng, có cấu trúc, trực tiếp.",
        "senior": "Mạch lạc, giải thích chậm rãi.",
    }
    return rules.get(age_group, rules["adult"])


def _level_rule(debate_level: str) -> str:
    rules = {
        "basic": "Phản biện đơn giản; gợi ý ngắn.",
        "intermediate": "Phản biện có cấu trúc; chỉ rõ điểm yếu chính; ít nhất 2 gợi ý.",
        "advanced": "Phản biện sâu; nêu giả định ẩn, ngoại lệ và lỗi logic.",
    }
    return rules.get(debate_level, rules["intermediate"])


def _input_mode_rule(input_mode: str | None) -> str:
    if input_mode == "voice":
        return "Transcript giọng nói — không trừ nặng vì thiếu dấu."
    return "Văn bản bình thường."


def _format_turn_history(turn_history: list[dict] | None, max_turns: int = 3) -> str:
    """Formats the last N turns into a Vietnamese history block."""
    if not turn_history:
        return ""
    recent = (turn_history or [])[-max_turns:]
    lines = ["=== LỊCH SỬ TRANH LUẬN (phản biện mới phải khác về góc độ) ==="]
    for i, turn in enumerate(recent, 1):
        user_arg = (turn.get("user_argument") or "").strip()
        ai_reb = (turn.get("ai_rebuttal") or "").strip()
        if user_arg:
            lines.append(f"Lượt {i} — Người dùng: {user_arg[:250]}")
        if ai_reb:
            lines.append(f"Lượt {i} — AI: {ai_reb[:200]}")
    lines.append("=== KẾT THÚC LỊCH SỬ ===")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompt — written IN Vietnamese, NO numeric scores
# ---------------------------------------------------------------------------
def _build_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là hệ thống chấm điểm và phản biện tranh luận bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ — phân tích nội bộ rồi trả về DUY NHẤT JSON (không có text nào trước JSON):
  Trước khi điền JSON, xác định nội bộ:
  a) Có nguồn/tổ chức/số liệu có tên cụ thể không?
  b) Lập luận chính là gì? Phạm vi có rõ không?
  c) Có lỗi logic hoặc giả định ẩn không?

Viết "ai_rebuttal" — 4–6 câu phản biện bằng {output_language}:
  - PHẢI mở đầu bằng: "Tuy nhiên,", "Thực tế cho thấy," hoặc "Ngược lại,"
  - PHẢI đề cập hoặc phản hồi nội dung CỤ THỂ trong lập luận (dẫn luận điểm, số liệu hoặc từ khoá của người dùng)
  - KHÔNG được viết phản biện chung chung áp dụng cho mọi lập luận
  - KHÔNG mở đầu bằng "Lập luận của bạn", "Bạn nên", "Hãy"
  - Giọng ({age_group}): {_tone_rule(age_group)}
  - Độ sâu ({debate_level}): {_level_rule(debate_level)}

CỔNG BẰNG CHỨNG — bắt buộc áp dụng trước khi chấm:
  CÓ bằng chứng thực (has_real_evidence=true, evidence_score > 0):
    → Tên tổ chức + năm: "WHO 2023", "McKinsey 2022", "báo cáo OECD", "nghiên cứu Harvard"
    → Số liệu cụ thể: "23%", "tăng 3 lần", "15 triệu người"
    → Sự kiện có ngày: "từ năm 2019", "tháng 3/2024"
  KHÔNG phải bằng chứng (has_real_evidence=false, evidence_score=0):
    → "Nhiều nghiên cứu cho thấy", "mọi người biết", "thực tế là", "rõ ràng"
    → Lý luận thuần túy không có nguồn

THANG ĐIỂM (chấm theo TỪNG TRƯỜNG HỢP CỤ THỂ):
  claim_score: Chất lượng luận điểm chính (0–100)
    - Có lập trường rõ + phạm vi cụ thể + kết nối với chủ đề: 50–80
    - Có lập trường nhưng mơ hồ, không phạm vi: 20–45
    - Không có lập trường rõ: 0–20
  evidence_score: Chất lượng bằng chứng (0–100, = 0 nếu không có bằng chứng thực)
    - Nhiều nguồn cụ thể + số liệu + sự kiện: 60–90
    - Một nguồn cụ thể: 30–60
    - Không có nguồn thực: 0
  reasoning_score: Chất lượng suy luận (0–100)
    - Chuỗi nhân quả rõ + không có lỗi logic: 50–80
    - Có liên kết logic nhưng có lỗ hổng: 25–50
    - Suy luận yếu hoặc circular: 0–25
  overall_score = round(claim×0.3 + evidence×0.3 + reasoning×0.4)

CHỐNG DỒN ĐIỂM:
  - KHÔNG dùng cùng điểm cho các lập luận khác nhau về chất lượng
  - KHÔNG dùng số tròn trăm hoặc trừ các giá trị cuối bằng 0 (10,20,30...)
  - Lập luận khác nhau PHẢI có điểm khác nhau"""


# ---------------------------------------------------------------------------
# JSON schema — string placeholders, NO numeric anchors
# ---------------------------------------------------------------------------
def _json_schema(output_language: str) -> str:
    return (
        '{{\n'
        '  "is_valid": true,\n'
        '  "evidence_quote": "<trích nguyên văn nguồn/số liệu từ lập luận, hoặc NONE>",\n'
        '  "checklist": {{"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false}},\n'
        f'  "ai_rebuttal": "<4–6 câu phản biện TRỰC TIẾP lập luận trên bằng {output_language}>",\n'
        '  "claim_score": <số nguyên>,\n'
        '  "evidence_score": <số nguyên, bắt buộc 0 nếu không có bằng chứng thực>,\n'
        '  "reasoning_score": <số nguyên>,\n'
        '  "overall_score": <round(claim×0.3 + evidence×0.3 + reasoning×0.4)>,\n'
        '  "claim_breakdown": {{"clarity": <0–40>, "relevance": <0–30>, "specificity": <0–30>}},\n'
        '  "evidence_breakdown": {{"presence": <0–40>, "evidence_specificity": <0–30>, "evidence_relevance": <0–30>}},\n'
        '  "reasoning_breakdown": {{"logical_connection": <0–40>, "causal_explanation": <0–40>, "fallacy_control": <0–20>}},\n'
        f'  "claim_explanation": "<lý do điểm claim bằng {output_language}>",\n'
        f'  "evidence_explanation": "<lý do điểm evidence bằng {output_language}>",\n'
        f'  "reasoning_explanation": "<lý do điểm reasoning bằng {output_language}>",\n'
        f'  "strengths": ["<điểm mạnh bằng {output_language}>"],\n'
        f'  "weaknesses": ["<điểm yếu bằng {output_language}>"],\n'
        f'  "suggestions": ["<gợi ý bằng {output_language}>"]\n'
        '}}'
    )


# ---------------------------------------------------------------------------
# Mode-specific system prompts — written IN Vietnamese, NO numeric scores
# ---------------------------------------------------------------------------

def _build_claim_writing_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện viết LUẬN ĐIỂM (Claim) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ:
  Bạn sẽ ĐÁNH GIÁ luận điểm (claim) mà người dùng viết.
  Trước khi điền JSON, xác định nội bộ:
  a) Luận điểm có lập trường rõ ràng không?
  b) Phạm vi có cụ thể, giới hạn hợp lý không?
  c) Có kết nối trực tiếp với chủ đề không?
  d) Có mạnh mẽ, có thể tranh biện được không?

TRỌNG TÂM CHẤM: CHỈ tập trung vào claim_score.
  - evidence_score và reasoning_score đặt = 0 (vì chế độ này KHÔNG yêu cầu bằng chứng hay lập luận).
  - overall_score = claim_score (vì chỉ chấm claim).

Viết "ai_rebuttal" — 3–5 câu ĐÁNH GIÁ luận điểm bằng {output_language}:
  - PHẢI chỉ ra điểm mạnh và điểm yếu CỤ THỂ của luận điểm
  - PHẢI gợi ý cách viết lại luận điểm tốt hơn
  - Giọng ({age_group}): {_tone_rule(age_group)}
  - Độ sâu ({debate_level}): {_level_rule(debate_level)}

THANG ĐIỂM claim_score (0–100):
  - Lập trường rõ + phạm vi cụ thể + kết nối chủ đề + tranh biện được: 60–90
  - Có lập trường nhưng mơ hồ, phạm vi quá rộng: 25–55
  - Không có lập trường rõ hoặc chỉ là nhận xét chung: 0–25

CHỐNG DỒN ĐIỂM:
  - KHÔNG dùng cùng điểm cho các luận điểm khác nhau về chất lượng
  - KHÔNG dùng số tròn trăm (10,20,30...)
  - Luận điểm khác nhau PHẢI có điểm khác nhau"""


def _build_find_evidence_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện tìm BẰNG CHỨNG (Evidence) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ:
  Bạn sẽ ĐÁNH GIÁ bằng chứng mà người dùng đưa ra để hỗ trợ một luận điểm.
  Trước khi điền JSON, xác định nội bộ:
  a) Có nguồn/tổ chức/số liệu có tên cụ thể không?
  b) Bằng chứng có liên quan trực tiếp đến luận điểm không?
  c) Bằng chứng có đủ cụ thể và đáng tin cậy không?
  d) Có nhiều hơn một nguồn không?

TRỌNG TÂM CHẤM: CHỈ tập trung vào evidence_score.
  - claim_score và reasoning_score đặt = 0 (vì chế độ này KHÔNG yêu cầu viết claim hay lập luận).
  - overall_score = evidence_score (vì chỉ chấm evidence).

CỔNG BẰNG CHỨNG — bắt buộc áp dụng:
  CÓ bằng chứng thực (evidence_score > 0):
    → Tên tổ chức + năm: "WHO 2023", "McKinsey 2022", "báo cáo OECD"
    → Số liệu cụ thể: "23%", "tăng 3 lần", "15 triệu người"
    → Sự kiện có ngày: "từ năm 2019", "tháng 3/2024"
  KHÔNG phải bằng chứng (evidence_score=0):
    → "Nhiều nghiên cứu cho thấy", "mọi người biết", "thực tế là"
    → Lý luận thuần túy không có nguồn

Viết "ai_rebuttal" — 3–5 câu ĐÁNH GIÁ bằng chứng bằng {output_language}:
  - PHẢI chỉ ra nguồn nào mạnh, nguồn nào yếu
  - PHẢI gợi ý cách tìm bằng chứng tốt hơn
  - Giọng ({age_group}): {_tone_rule(age_group)}
  - Độ sâu ({debate_level}): {_level_rule(debate_level)}

THANG ĐIỂM evidence_score (0–100):
  - Nhiều nguồn cụ thể + số liệu + sự kiện: 60–90
  - Một nguồn cụ thể: 30–60
  - Không có nguồn thực: 0

CHỐNG DỒN ĐIỂM:
  - KHÔNG dùng cùng điểm cho các bằng chứng khác nhau về chất lượng
  - KHÔNG dùng số tròn trăm (10,20,30...)"""


def _build_quick_rebuttal_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện PHẢN BIỆN NHANH (Quick Rebuttal) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ:
  Bạn sẽ ĐÁNH GIÁ khả năng phản biện và phát hiện lỗ hổng logic của người dùng.
  Trước khi điền JSON, xác định nội bộ:
  a) Người dùng có xác định đúng điểm yếu trong lập luận không?
  b) Phản biện có logic chặt chẽ không?
  c) Có lỗi logic nào trong phản biện của người dùng không?
  d) Chuỗi nhân quả có rõ ràng không?

TRỌNG TÂM CHẤM: CHỈ tập trung vào reasoning_score.
  - claim_score và evidence_score đặt = 0 (vì chế độ này KHÔNG yêu cầu viết claim hay tìm evidence).
  - overall_score = reasoning_score (vì chỉ chấm reasoning).

Viết "ai_rebuttal" — 3–5 câu ĐÁNH GIÁ phản biện bằng {output_language}:
  - PHẢI xác nhận những điểm người dùng phát hiện đúng
  - PHẢI chỉ ra lỗ hổng mà người dùng bỏ sót
  - PHẢI đưa ra phân tích đúng nếu người dùng sai
  - Giọng ({age_group}): {_tone_rule(age_group)}
  - Độ sâu ({debate_level}): {_level_rule(debate_level)}

THANG ĐIỂM reasoning_score (0–100):
  - Chuỗi nhân quả rõ + phát hiện đúng lỗ logic + không có lỗi logic mới: 60–90
  - Có liên kết logic nhưng bỏ sót lỗ hổng quan trọng: 25–55
  - Suy luận yếu, không phát hiện được lỗ hổng: 0–25

CHỐNG DỒN ĐIỂM:
  - KHÔNG dùng cùng điểm cho các phản biện khác nhau về chất lượng
  - KHÔNG dùng số tròn trăm (10,20,30...)"""


def _build_full_argument_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là hệ thống chấm điểm và phản biện lập luận HOÀN CHỈNH (C+E+R) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ — phân tích nội bộ rồi trả về DUY NHẤT JSON (không có text nào trước JSON):
  Trước khi điền JSON, xác định nội bộ:
  a) Có nguồn/tổ chức/số liệu có tên cụ thể không?
  b) Lập luận chính là gì? Phạm vi có rõ không?
  c) Có lỗi logic hoặc giả định ẩn không?
  d) Ba thành phần C+E+R có liên kết chặt chẽ không?

TRỌNG TÂM: Chấm ĐẦY ĐỦ cả 3 thành phần Claim + Evidence + Reasoning.
  overall_score = round(claim×0.3 + evidence×0.3 + reasoning×0.4)

Viết "ai_rebuttal" — 4–6 câu ĐÁNH GIÁ TOÀN DIỆN lập luận bằng {output_language}:
  - PHẢI đánh giá cả 3 thành phần: luận điểm, bằng chứng, lập luận
  - PHẢI chỉ ra thành phần yếu nhất và gợi ý cải thiện cụ thể
  - Giọng ({age_group}): {_tone_rule(age_group)}
  - Độ sâu ({debate_level}): {_level_rule(debate_level)}

CỔNG BẰNG CHỨNG — bắt buộc áp dụng trước khi chấm:
  CÓ bằng chứng thực (has_real_evidence=true, evidence_score > 0):
    → Tên tổ chức + năm, số liệu cụ thể, sự kiện có ngày
  KHÔNG phải bằng chứng (has_real_evidence=false, evidence_score=0):
    → "Nhiều nghiên cứu cho thấy", "mọi người biết", lý luận thuần túy

THANG ĐIỂM (chấm theo TỪNG TRƯỜNG HỢP CỤ THỂ):
  claim_score: Chất lượng luận điểm chính (0–100)
    - Có lập trường rõ + phạm vi cụ thể + kết nối với chủ đề: 50–80
    - Có lập trường nhưng mơ hồ, không phạm vi: 20–45
    - Không có lập trường rõ: 0–20
  evidence_score: Chất lượng bằng chứng (0–100, = 0 nếu không có bằng chứng thực)
    - Nhiều nguồn cụ thể + số liệu + sự kiện: 60–90
    - Một nguồn cụ thể: 30–60
    - Không có nguồn thực: 0
  reasoning_score: Chất lượng suy luận (0–100)
    - Chuỗi nhân quả rõ + không có lỗi logic: 50–80
    - Có liên kết logic nhưng có lỗ hổng: 25–50
    - Suy luận yếu hoặc circular: 0–25

CHỐNG DỒN ĐIỂM:
  - KHÔNG dùng cùng điểm cho các lập luận khác nhau về chất lượng
  - KHÔNG dùng số tròn trăm hoặc trừ các giá trị cuối bằng 0 (10,20,30...)
  - Lập luận khác nhau PHẢI có điểm khác nhau"""


import re
import unicodedata

# ---------------------------------------------------------------------------
# Mode dispatch helper
# ---------------------------------------------------------------------------
PRACTICE_MODE_ALIASES = {
    "free": "free_debate",
    "free_debate": "free_debate",
    "claim": "claim_writing",
    "luyen_viet_claim": "claim_writing",
    "claim_practice": "claim_writing",
    "claim_writing": "claim_writing",
    "evidence": "find_evidence",
    "luyen_tim_evidence": "find_evidence",
    "evidence_practice": "find_evidence",
    "find_evidence": "find_evidence",
    "rebuttal": "quick_rebuttal",
    "phan_bien_nhanh": "quick_rebuttal",
    "quick_rebuttal": "quick_rebuttal",
    "argument_builder": "full_argument",
    "full_argument": "full_argument",
}

PRACTICE_PROMPT_TYPES = {
    "claim_writing": "scenario_prompt",
    "find_evidence": "claim_prompt",
    "quick_rebuttal": "weak_argument",
}


def normalize_practice_mode(mode: str | None) -> str:
    ascii_key = unicodedata.normalize("NFD", str(mode or "free_debate").strip().lower())
    ascii_key = "".join(char for char in ascii_key if unicodedata.category(char) != "Mn")
    key = re.sub(r"\W+", "_", ascii_key).strip("_")
    return PRACTICE_MODE_ALIASES.get(key, "free_debate")


def practice_prompt_type_for_mode(mode: str | None) -> str:
    return PRACTICE_PROMPT_TYPES.get(normalize_practice_mode(mode), "topic_prompt")


def practice_instruction_for_mode(mode: str | None) -> str:
    normalized = normalize_practice_mode(mode)
    if normalized == "claim_writing":
        return "Hãy viết một claim rõ ràng, có thể tranh luận được."
    if normalized == "find_evidence":
        return "Hãy đưa ra bằng chứng cụ thể để hỗ trợ hoặc phản bác claim này."
    if normalized == "quick_rebuttal":
        return "Hãy chỉ ra lỗ hổng, giả định sai hoặc phản ví dụ."
    return "Hãy xây dựng câu trả lời tranh biện phù hợp."


def _practice_context(mode: str, practice_prompt: str | None, practice_round: int | None) -> str:
    if mode not in PRACTICE_PROMPT_TYPES or not practice_prompt:
        return ""
    labels = {
        "claim_writing": "Chủ đề/tình huống do Lumi đưa ra",
        "find_evidence": "Claim mẫu do Lumi đưa ra",
        "quick_rebuttal": "Luận điểm yếu do Lumi đưa ra",
    }
    return (
        f"=== ĐỀ BÀI LUYỆN TẬP ===\n"
        f"Mode: {mode}\n"
        f"Lượt: {practice_round or 1}\n"
        f"{labels[mode]}: {practice_prompt}\n"
        f"Nhiệm vụ của người dùng: {practice_instruction_for_mode(mode)}\n"
        f"Chấm câu trả lời của người dùng theo đúng đề bài này. Không tự coi đề bài là câu trả lời của người dùng.\n\n"
    )


def _system_prompt_for_mode(mode: str, output_language: str, age_group: str, debate_level: str) -> str:
    mode = normalize_practice_mode(mode)
    if mode == "claim_writing":
        return _build_claim_writing_system_prompt(output_language, age_group, debate_level)
    elif mode == "find_evidence":
        return _build_find_evidence_system_prompt(output_language, age_group, debate_level)
    elif mode == "quick_rebuttal":
        return _build_quick_rebuttal_system_prompt(output_language, age_group, debate_level)
    elif mode == "full_argument":
        return _build_full_argument_system_prompt(output_language, age_group, debate_level)
    # Default: free_debate
    return _build_system_prompt(output_language, age_group, debate_level)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_cer_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str = "text",
    coach_model: str = "socratic_v3",
    language: str = "vi",
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_round: int | None = None,
) -> list[dict[str, str]]:
    """
    Returns a [system, user] message pair for the Groq API.

    Key design choices:
    - System prompt in Vietnamese (language register lock)
    - NO numeric scores in few-shot examples (prevents anchoring)
    - Chain-of-thought (Bước 1/2/3) forces argument-specific analysis
    - Turn history injected so rebuttals evolve each turn
    - String placeholders in JSON schema (no numeric anchors)
    - Mode dispatches to mode-specific system prompts
    """
    output_language = _language_name(language)
    mode = normalize_practice_mode(practice_mode or mode)
    system_prompt = _system_prompt_for_mode(mode, output_language, age_group, debate_level)

    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""
    practice_section = _practice_context(mode, practice_prompt, practice_round)

    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"{history_section}"
        f"{practice_section}"
        f"\n=== LẬP LUẬN HIỆN TẠI CỦA NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ===\n"
        f"Phân tích lập luận trên và trả về DUY NHẤT JSON hợp lệ (không có text nào trước JSON, không markdown):\n"
        f"{_json_schema(output_language)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_cer_rubric_prompt(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str = "text",
    coach_model: str = "socratic_v3",
    language: str = "vi",
) -> str:
    """Single-message fallback — kept for backward compatibility."""
    output_language = _language_name(language)
    msgs = build_cer_messages(
        topic=topic, stance=stance, difficulty=difficulty,
        user_argument=user_argument, age_group=age_group,
        debate_level=debate_level, input_mode=input_mode,
        language=language,
    )
    return msgs[0]["content"] + "\n\n" + msgs[1]["content"]


def build_practice_prompt_messages(
    mode: str,
    topic: str,
    difficulty: str | None = None,
    round: int = 1,
    language: str = "vi",
    previous_prompts: list[str] | None = None,
    previous_topics: list[str] | None = None,
    avoid_repeating: bool = True,
) -> list[dict[str, str]]:
    """Builds a small prompt-generation request for single-skill practice rounds."""
    normalized = normalize_practice_mode(mode)
    prompt_type = practice_prompt_type_for_mode(normalized)
    output_language = _language_name(language)
    if normalized == "find_evidence":
        task = (
            "Tạo đúng 1 claim mẫu ngắn, rõ lập trường, có thể được hỗ trợ hoặc phản bác bằng bằng chứng. "
            "Không tự đưa bằng chứng."
        )
    elif normalized == "quick_rebuttal":
        task = (
            "Tạo đúng 1 luận điểm yếu hoặc lập luận có lỗ hổng logic rõ, ngắn gọn, liên quan chủ đề. "
            "Lập luận yếu phải đủ cụ thể để người học phản biện."
        )
    else:
        task = (
            "Tạo đúng 1 chủ đề phụ hoặc tình huống ngắn để người học viết claim. "
            "Không viết claim thay người học."
        )

    previous_prompt_block = "\n".join(
        f"- {item}" for item in (previous_prompts or [])[-8:] if str(item).strip()
    ) or "- Chưa có"
    previous_topic_block = "\n".join(
        f"- {item}" for item in (previous_topics or [])[-8:] if str(item).strip()
    ) or "- Chưa có"
    anti_repeat_rule = (
        "Generate a new prompt that is different from previous prompts. "
        "Avoid reusing the same topic, same scenario, same claim, or same weak argument. "
        "Return only valid JSON. The prompt must be in Vietnamese."
        if avoid_repeating
        else "Return only valid JSON. The prompt must be in Vietnamese."
    )

    system_prompt = (
        f"Bạn là Lumi, huấn luyện viên tạo đề bài luyện tranh biện bằng {output_language}. "
        "Chỉ trả về DUY NHẤT JSON hợp lệ, không markdown, không giải thích ngoài JSON."
    )
    user_prompt = (
        f"Mode: {normalized}\n"
        f"Prompt type: {prompt_type}\n"
        f"Chủ đề phiên: {topic}\n"
        f"Độ khó: {difficulty or 'Trung bình'}\n"
        f"Lượt: {round}\n"
        f"Yêu cầu chống lặp: {anti_repeat_rule}\n"
        f"Previous prompts:\n{previous_prompt_block}\n"
        f"Previous topics:\n{previous_topic_block}\n"
        f"Nhiệm vụ: {task}\n\n"
        "JSON bắt buộc:\n"
        "{\n"
        f'  "mode": "{normalized}",\n'
        f'  "prompt_type": "{prompt_type}",\n'
        '  "topic": "<topic/tình huống chính mới, khác các topic trước>",\n'
        '  "scenario": "<chỉ dùng cho claim_writing, tình huống mới>",\n'
        '  "claim": "<chỉ dùng cho evidence_practice, claim mới>",\n'
        '  "weak_argument": "<chỉ dùng cho quick_rebuttal, luận điểm yếu mới>",\n'
        '  "prompt": "<đề bài 1-2 câu, cụ thể, không trùng nguyên văn chủ đề nếu có thể>",\n'
        f'  "instruction": "{practice_instruction_for_mode(normalized)}"\n'
        "}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_debate_prompt(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str = "text",
    coach_model: str = "socratic_v3",
    language: str = "vi",
) -> str:
    """Legacy marker-format prompt — kept for backward compatibility."""
    output_language = _language_name(language)
    invalid_output = (
        "[REBUTTAL]\nNội dung chưa đủ rõ để phản biện. Vui lòng nhập một lập luận cụ thể hơn.\n\n"
        "[CER]\nClaim: 0\nEvidence: 0\nReasoning: 0\n\n"
        "[FEEDBACK]\nStrengths:\n- Chưa có điểm mạnh rõ ràng.\n"
        "Weaknesses:\n- Lập luận chưa đủ rõ hoặc thiếu nội dung.\n"
        "Suggestions:\n- Hãy nêu rõ quan điểm chính và thêm ít nhất một lý do hoặc ví dụ."
    )
    return (
        f"Bạn viết toàn bộ câu trả lời bằng {output_language}. Tuyệt đối không dùng tiếng Anh.\n\n"
        f"HAI VAI TRÒ:\n"
        f"[REBUTTAL] = Đối thủ tranh biện — phản bác TRỰC TIẾP lập luận cụ thể của người dùng.\n"
        f"[CER]+[FEEDBACK] = Người chấm điểm bằng {output_language}.\n\n"
        f"RÀNG BUỘC:\n"
        f"• PHẢI mở đầu [REBUTTAL] bằng: \"Tuy nhiên,\", \"Thực tế cho thấy,\" hoặc \"Ngược lại,\".\n"
        f"• Phản biện PHẢI đề cập nội dung CỤ THỂ của lập luận người dùng.\n"
        f"• Giọng: {_tone_rule(age_group)} | Độ sâu: {_level_rule(debate_level)}\n"
        f"• Dùng toàn thang 0–100; tránh số tròn; điểm phản ánh chất lượng thực.\n"
        f"• Evidence=0 nếu không có nguồn/số liệu thực tên cụ thể.\n\n"
        f"Nếu lập luận không hợp lệ/quá ngắn/spam:\n{invalid_output}\n\n"
        f"FORMAT BẮT BUỘC:\n[REBUTTAL]\n<4–6 câu phản bác bằng {output_language}>\n\n"
        f"[CER]\nClaim: <số nguyên>\nEvidence: <số nguyên>\nReasoning: <số nguyên>\n\n"
        f"[FEEDBACK]\nStrengths:\n- <tối đa 3 gạch>\nWeaknesses:\n- <tối đa 3 gạch>\nSuggestions:\n- <tối đa 3 gạch>\n\n"
        f"Chủ đề: {topic}\nLập trường người dùng: {stance}\nLập luận người dùng: {user_argument}"
    ).strip()


def build_groq_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str = "adult",
    debate_level: str = "intermediate",
    input_mode: str | None = None,
    language: str = "vi",
    turn_history: list[dict] | None = None,
    mode: str = "free_debate",
    practice_mode: str | None = None,
    practice_prompt: str | None = None,
    practice_round: int | None = None,
) -> list[dict[str, str]]:
    """Legacy entry point — routes to build_cer_messages."""
    return build_cer_messages(
        topic=topic, stance=stance, difficulty=difficulty,
        user_argument=user_argument, age_group=age_group,
        debate_level=debate_level, input_mode=input_mode or "text",
        language=language, turn_history=turn_history,
        mode=mode,
        practice_mode=practice_mode,
        practice_prompt=practice_prompt,
        practice_round=practice_round,
    )
