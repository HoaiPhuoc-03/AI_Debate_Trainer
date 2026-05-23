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
) -> list[dict[str, str]]:
    """
    Returns a [system, user] message pair for the Groq API.

    Key design choices:
    - System prompt in Vietnamese (language register lock)
    - NO numeric scores in few-shot examples (prevents anchoring)
    - Chain-of-thought (Bước 1/2/3) forces argument-specific analysis
    - Turn history injected so rebuttals evolve each turn
    - String placeholders in JSON schema (no numeric anchors)
    """
    output_language = _language_name(language)
    system_prompt = _build_system_prompt(output_language, age_group, debate_level)

    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""

    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"{history_section}"
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
) -> list[dict[str, str]]:
    """Legacy entry point — routes to build_cer_messages."""
    return build_cer_messages(
        topic=topic, stance=stance, difficulty=difficulty,
        user_argument=user_argument, age_group=age_group,
        debate_level=debate_level, input_mode=input_mode or "text",
        language=language, turn_history=turn_history,
    )