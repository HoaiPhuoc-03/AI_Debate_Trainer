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


import re
import unicodedata

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


_FACT_CHECK_INSTRUCTION = """KIỂM CHỨNG BẰNG CHỨNG (fact_check):
  - Hãy là một kiểm chứng viên hoài nghi, khắt khe.
  - Chỉ kiểm chứng nếu người học đưa ra số liệu, nguồn trích dẫn, hoặc nghiên cứu cụ thể. Nếu không có, trả về [] (mảng rỗng).
  - Đối chiếu thông tin người học đưa ra với "=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ KIỂM CHỨNG BẰNG CHỨNG NGƯỜI DÙNG ===".
  - Gắn nhãn verdict:
    * "verified": nguồn/số liệu có thật, trùng khớp thông tin tìm kiếm.
    * "inaccurate" hoặc "unverifiable": số liệu/nguồn bịa đặt, sai lệch, không có thật, hoặc không hợp lý (ví dụ: NASA nghiên cứu về viết lách phổ thông).
  - Cấu trúc mỗi mục:
    * "claim_text": trích nguyên văn số liệu hoặc nguồn được nêu.
    * "verdict": "verified" | "inaccurate" | "unverifiable" | "outdated".
    * "explanation": giải thích ngắn gọn bằng tiếng Việt lý do nghi ngờ/xác thực.
    * "source_url": trích xuất chính xác URL cụ thể từ kết quả tìm kiếm nếu trùng khớp/liên quan đến nguồn được trích dẫn (ví dụ: link bài báo cụ thể trên WHO/UNESCO), hoặc để null nếu không tìm thấy."""


def _build_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là hệ thống chấm điểm và phản biện tranh luận bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ - Phân tích lập luận và trả về JSON:
  - Viết "ai_rebuttal": Viết dạng đoạn văn liền mạch, tự nhiên bằng {output_language} (4-6 câu).
  - Phản biện phải đề cập trực tiếp ý người dùng và tích hợp đủ 3 phần: Luận điểm phản biện, Bằng chứng thực tế cụ thể (tên tổ chức, số liệu, năm cụ thể) và Lập luận kết nối.
  - BẰNG CHỨNG CỦA AI: Bằng chứng bạn đưa ra trong "ai_rebuttal" phải CỤ THỂ (ví dụ: số liệu phần trăm, tổ chức uy tín, năm công bố cụ thể). Tuyệt đối KHÔNG sử dụng các câu mơ hồ chung chung như "nhiều nghiên cứu cho thấy", "các chuyên gia nói", "nhiều báo cáo chỉ ra".
  - RÀNG BUỘC LINK: Tuyệt đối KHÔNG chèn bất kỳ liên kết URL hay link markdown nào vào trong văn bản "ai_rebuttal". Văn bản "ai_rebuttal" phải hoàn toàn là text thuần túy.
  - Giọng ({age_group}): {_tone_rule(age_group)} | Độ sâu ({debate_level}): {_level_rule(debate_level)}

NGUỒN THAM KHẢO AI (evidence_source_links):
  - Hãy chọn một bài viết/số liệu thực tế từ "=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ AI LẤY BẰNG CHỨNG PHẢN BIỆN ===" để đưa vào phần bằng chứng trong "ai_rebuttal".
  - BẮT BUỘC cung cấp liên kết nguồn cụ thể trích xuất trực tiếp từ kết quả tìm kiếm đó để đưa vào "evidence_source_links".
  - Định dạng: "Tên nguồn - URL cụ thể của bài viết/nghiên cứu" (ví dụ: "UNESCO - https://www.unesco.org/en/articles/more-specific-path"). Tuyệt đối KHÔNG dùng link trang chủ chung chung (như https://unesco.org) nếu trong kết quả tìm kiếm có link bài viết cụ thể.

{_FACT_CHECK_INSTRUCTION}

CỔNG BẰNG CHỨNG (evidence_score > 0 chỉ khi có bằng chứng thực tế):
  - Có bằng chứng: Tên tổ chức/năm cụ thể (WHO 2023, McKinsey 2022), số liệu (23%, tăng 3 lần), hoặc sự kiện rõ ngày.
  - Không bằng chứng (evidence_score = 0): KHÔNG dùng các câu mơ hồ như "nhiều nghiên cứu cho thấy", "mọi người đều biết", hay lý lẽ suông không nguồn.

THANG ĐIỂM & CHỐNG DỒN ĐIỂM:
  - claim_score (0–100): Lập trường rõ + phạm vi cụ thể: 50–80. Mơ hồ: 20–45. Không rõ: 0–20.
  - evidence_score (0–100): Nhiều nguồn + số liệu: 60–90. Một nguồn: 30–60. Không bằng chứng: 0.
  - reasoning_score (0–100): Nhân quả rõ + không lỗi logic: 50–80. Có lỗ hổng: 25–50. Yếu/circular: 0–25.
  - overall_score = round(claim×0.3 + evidence×0.3 + reasoning×0.4)
  - Lập luận khác nhau PHẢI có điểm khác nhau. KHÔNG dùng số tròn trăm (100) hoặc tận cùng là 0 (ví dụ: 10,20,30...)."""


# ---------------------------------------------------------------------------
# JSON schema - string placeholders, NO numeric anchors
# ---------------------------------------------------------------------------
def _json_schema(output_language: str, mode: str | None = None) -> str:
    if str(mode or "").strip().lower() == "quick_rebuttal":
        return (
            "{\n"
            '  "is_valid": true,\n'
            '  "evidence_quote": "NONE",\n'
            '  "checklist": {"identified_weak_argument": true/false, "named_flaw": true/false, "explained_why_weak": true/false, "has_counter_example": true/false, "stays_focused": true/false},\n'
            f'  "ai_rebuttal": "<3-5 cau nhan xet huan luyen ve kha nang bat loi lap luan bang {output_language}>",\n'
            '  "mode_scores": {\n'
            '    "flaw_detection": <0-100 nhan dien dung loi chinh>,\n'
            '    "counter_example": <0-100 co phan vi du, cau hoi phan bien, hoac huong bac bo>,\n'
            '    "explanation": <0-100 giai thich vi sao loi lam yeu lap luan>,\n'
            '    "focus": <0-100 bam sat weak argument>,\n'
            '    "overall": <round(flaw_detection*0.40 + explanation*0.25 + counter_example*0.20 + focus*0.15)>\n'
            '  },\n'
            '  "cer": {\n'
            '    "claim": <same as mode_scores.flaw_detection>,\n'
            '    "evidence": <same as mode_scores.counter_example>,\n'
            '    "reasoning": <same as mode_scores.explanation>,\n'
            '    "overall": <same as mode_scores.overall>,\n'
            '    "total": <same as mode_scores.overall>\n'
            '  },\n'
            '  "claim_score": <same as mode_scores.flaw_detection>,\n'
            '  "evidence_score": <same as mode_scores.counter_example>,\n'
            '  "reasoning_score": <same as mode_scores.explanation>,\n'
            '  "overall_score": <same as mode_scores.overall>,\n'
            '  "claim_breakdown": {"clarity": <nhan dien loi chinh 0-40>, "relevance": <bam dung weak argument 0-30>, "specificity": <goi ten/cat dung cum yeu 0-30>},\n'
            '  "evidence_breakdown": {"presence": <co phan vi du/cau hoi phan bien 0-40>, "evidence_specificity": <phan vi du cu the 0-30>, "evidence_relevance": <phan vi du dung trong tam 0-30>},\n'
            '  "reasoning_breakdown": {"logical_connection": <giai thich vi sao loi lam yeu lap luan 0-40>, "causal_explanation": <noi loi voi he qua logic 0-40>, "fallacy_control": <khong tao loi moi 0-20>},\n'
            f'  "strengths": ["<chi nhan xet diem manh ve bat loi/nguy bien bang {output_language}>"],\n'
            f'  "weaknesses": ["<chi nhan xet diem yeu ve bat loi/giai thich/phan vi du/focus bang {output_language}>"],\n'
            f'  "suggestions": ["<goi y ngan de goi ten loi, trich cum yeu, them phan vi du bang {output_language}>"]\n'
            "}"
        )
    return (
        "{\n"
        '  "is_valid": true,\n'
        '  "evidence_quote": "<trích nguyên văn nguồn/số liệu từ lập luận, hoặc NONE>",\n'
        '  "checklist": {{"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false}},\n'
        f'  "ai_rebuttal": "<4–6 câu phản biện TRỰC TIẾP lập luận trên bằng {output_language}, chứa bằng chứng cụ thể tự chọn (ví dụ: số liệu, tổ chức), KHÔNG dùng từ mơ hồ, KHÔNG chứa bất kỳ liên kết URL hay link markdown nào>",\n'
        '  "evidence_source_links": ["<Tên nguồn - URL cụ thể trích trực tiếp từ kết quả tìm kiếm hỗ trợ cho bằng chứng của AI trong ai_rebuttal, KHÔNG dùng trang chủ chung chung (ví dụ: WHO - https://www.who.int/news-room/fact-sheets/detail/depression)>"],\n'
        '  "fact_check": [<danh sách kiểm chứng bằng chứng người dùng, mỗi mục: {{"claim_text": "<trích>", "verdict": "verified|inaccurate|unverifiable|outdated", "explanation": "<giải thích>", "source_url": "<URL cụ thể từ kết quả tìm kiếm, hoặc null nếu không tìm thấy>"}}, hoặc [] nếu không có bằng chứng>],\n'
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


def _json_schema_free_debate(output_language: str) -> str:
    """JSON schema for free_debate mode - includes coherent paragraph rebuttal and source links."""
    return (
        '{{\n'
        '  "is_valid": true,\n'
        '  "evidence_quote": "<trích nguyên văn nguồn/số liệu từ lập luận, hoặc NONE>",\n'
        '  "checklist": {{"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false}},\n'
        f'  "ai_rebuttal": "<phản biện mạch lạc dạng đoạn văn tự nhiên bằng {output_language}, KHÔNG chứa nhãn như [Luận điểm], chứa bằng chứng cụ thể tự chọn, KHÔNG dùng từ mơ hồ, KHÔNG chứa bất kỳ liên kết URL hay link markdown nào>",\n'
        '  "evidence_source_links": ["<Tên nguồn - URL cụ thể trích trực tiếp từ kết quả tìm kiếm hỗ trợ cho bằng chứng của AI trong ai_rebuttal, KHÔNG dùng trang chủ chung chung (ví dụ: WHO - https://www.who.int/news-room/fact-sheets/detail/depression)>"],\n'
        '  "fact_check": [<danh sách kiểm chứng bằng chứng người dùng, mỗi mục: {{"claim_text": "<trích>", "verdict": "verified|inaccurate|unverifiable|outdated", "explanation": "<giải thích>", "source_url": "<URL cụ thể từ kết quả tìm kiếm, hoặc null nếu không tìm thấy>"}}, hoặc [] nếu không có bằng chứng>],\n'
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


def _json_schema_find_evidence(output_language: str) -> str:
    """JSON schema for find_evidence mode - evidence-only critique with fact_check and source suggestions."""
    return (
        '{{\n'
        '  "is_valid": true,\n'
        '  "evidence_quote": "<trích nguyên văn nguồn/số liệu từ lập luận, hoặc NONE>",\n'
        '  "checklist": {{"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false}},\n'
        f'  "ai_rebuttal": "<đánh giá CHỈ về bằng chứng: phù hợp với claim, độ mạnh/độ tin cậy của bằng chứng, và đề xuất nguồn tốt hơn bằng {output_language}, hoàn toàn KHÔNG chứa liên kết URL hay link markdown>",\n'
        '  "evidence_source_links": ["<Tên nguồn - URL cụ thể trích trực tiếp từ kết quả tìm kiếm giới thiệu nguồn tốt hơn hỗ trợ người dùng, KHÔNG dùng trang chủ chung chung (ví dụ: WHO - https://www.who.int/news-room/fact-sheets/detail/depression)>"],\n'
        '  "fact_check": [<danh sách kiểm chứng bằng chứng người dùng, mỗi mục: {{"claim_text": "<trích>", "verdict": "verified|inaccurate|unverifiable|outdated", "explanation": "<giải thích>", "source_url": "<URL cụ thể từ kết quả tìm kiếm, hoặc null nếu không tìm thấy>"}}, hoặc [] nếu không có bằng chứng>],\n'
        '  "better_source_suggestions": ["<Tên nguồn/cơ sở dữ liệu - mô tả ngắn>"],\n'
        '  "claim_score": 0,\n'
        '  "evidence_score": <số nguyên, bắt buộc 0 nếu không có bằng chứng thực>,\n'
        '  "reasoning_score": 0,\n'
        '  "overall_score": <evidence_score>,\n'
        '  "claim_breakdown": {{"clarity": 0, "relevance": 0, "specificity": 0}},\n'
        '  "evidence_breakdown": {{"presence": <0–40>, "evidence_specificity": <0–30>, "evidence_relevance": <0–30>}},\n'
        '  "reasoning_breakdown": {{"logical_connection": 0, "causal_explanation": 0, "fallacy_control": 0}},\n'
        f'  "claim_explanation": "",\n'
        f'  "evidence_explanation": "<lý do điểm evidence bằng {output_language}>",\n'
        f'  "reasoning_explanation": "",\n'
        f'  "strengths": ["<điểm mạnh bằng chứng bằng {output_language}>"],\n'
        f'  "weaknesses": ["<điểm yếu bằng chứng bằng {output_language}>"],\n'
        f'  "suggestions": ["<gợi ý cải thiện bằng chứng bằng {output_language}>"]\n'
        '}}'
    )


def _json_schema_claim_and_rebuttal(output_language: str) -> str:
    """JSON schema for claim_writing and quick_rebuttal modes - NO fact_check or evidence_source_links."""
    return (
        '{{\n'
        '  "is_valid": true,\n'
        '  "evidence_quote": "<trích nguyên văn nguồn/số liệu từ lập luận, hoặc NONE>",\n'
        '  "checklist": {{"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false}},\n'
        f'  "ai_rebuttal": "<nhận xét/đánh giá CHỈ về chất lượng và độ mạnh của luận điểm (đối với claim_writing) hoặc lập luận (đối với quick_rebuttal) bằng {output_language}, KHÔNG chứa bất kỳ liên kết URL hay link markdown nào>",\n'
        f'  "model_claim": "<một câu claim mẫu hoàn chỉnh tương ứng với lập trường bằng {output_language}, hoặc NONE>",\n'
        '  "claim_score": <số nguyên>,\n'
        '  "evidence_score": <số nguyên, bắt buộc 0 nếu không có bằng chứng thực>,\n'
        '  "reasoning_score": <số nguyên>,\n'
        '  "overall_score": <overall score>,\n'
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


def _json_schema_for_mode(mode: str, output_language: str) -> str:
    """Returns the appropriate JSON schema for the given practice mode."""
    if mode == "free_debate":
        return _json_schema_free_debate(output_language)
    elif mode == "find_evidence":
        return _json_schema_find_evidence(output_language)
    elif mode == "claim_writing":
        return _json_schema_claim_and_rebuttal(output_language)
    elif mode == "quick_rebuttal":
        return _json_schema(output_language, mode)
    return _json_schema(output_language)


# ---------------------------------------------------------------------------
# Mode-specific system prompts - written IN Vietnamese, NO numeric scores
# ---------------------------------------------------------------------------

def _build_claim_writing_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện viết LUẬN ĐIỂM (Claim) bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ - Phân tích luận điểm và trả về JSON:
  - Viết "ai_rebuttal" (chỉ nhận xét về LUẬN ĐIỂM, tuyệt đối không bình luận về bằng chứng hay lý luận khác):
    * Chỉ tập trung bình luận và đánh giá xem luận điểm (Claim) của người dùng mạnh/yếu như thế nào (1–3 câu).
  - RÀNG BUỘC LINK: Tuyệt đối KHÔNG chèn bất kỳ liên kết URL hay link markdown nào vào trong văn bản "ai_rebuttal". Văn bản "ai_rebuttal" phải hoàn toàn là text thuần túy.
  - Giọng ({age_group}): {_tone_rule(age_group)} | Độ sâu ({debate_level}): {_level_rule(debate_level)}

TRỌNG TÂM CHẤM: CHỈ tập trung vào claim_score.
  - evidence_score = 0 | reasoning_score = 0 | overall_score = claim_score.
  - Chấm theo clarity (40 điểm), relevance (30 điểm) và specificity (30 điểm).
  - BẮT BUỘC trả về một câu luận điểm mẫu hoàn chỉnh trong trường "model_claim".

THANG ĐIỂM & CHỐNG DỒN ĐIỂM:
  - claim_score (0–100): Rõ lập trường + phạm vi tốt + tranh biện được: 60–100. Mơ hồ: 25–59. Yếu/nhận xét chung: 0–25.
  - Lập luận khác nhau PHẢI có điểm khác nhau. KHÔNG dùng số tròn trăm (100) hoặc tận cùng là 0 (ví dụ: 10,20,30...)."""


def _build_find_evidence_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện tìm BẰNG CHỨNG (Evidence) bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ - Phân tích bằng chứng và trả về JSON:
  - Viết "ai_rebuttal" (đánh giá CHỈ về BẰNG CHỨNG, tuyệt đối không bình luận về luận điểm hay lỗi lý luận khác):
    1) Nhận xét mức độ phù hợp của bằng chứng đối với luận điểm (Claim) (1-2 câu).
    2) Nhận xét độ mạnh/độ tin cậy của bằng chứng đó (1-2 câu).
    3) Đưa ra gợi ý/khuyến nghị các nguồn tài liệu tốt hơn để tìm bằng chứng mạnh hơn (1-2 câu).
  - RÀNG BUỘC LINK: Tuyệt đối KHÔNG chèn bất kỳ liên kết URL hay link markdown nào vào trong văn bản "ai_rebuttal". Văn bản "ai_rebuttal" phải hoàn toàn là text thuần túy.
  - Giọng ({age_group}): {_tone_rule(age_group)} | Độ sâu ({debate_level}): {_level_rule(debate_level)}

TRỌNG TÂM CHẤM: CHỈ tập trung vào evidence_score.
  - claim_score = 0 | reasoning_score = 0 | overall_score = evidence_score.

NGUỒN GỢI Ý ĐỂ TÌM BẰNG CHỨNG MẠNH HƠN (evidence_source_links):
  - Dựa vào kết quả tìm kiếm trong "=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ AI LẤY BẰNG CHỨNG PHẢN BIỆN ===", hãy chọn ra 1-2 liên kết bài viết cụ thể và uy tín nhất để người dùng tham khảo tìm kiếm bằng chứng tốt hơn.
  - Đưa các liên kết này vào mảng "evidence_source_links".
  - Định dạng mỗi mục trong mảng: "Tên nguồn - URL cụ thể của bài viết/nghiên cứu" (ví dụ: "UNESCO - https://www.unesco.org/en/articles/more-specific-path"). Tuyệt đối không dùng link trang chủ chung chung (như https://unesco.org) nếu trong kết quả tìm kiếm có link bài viết cụ thể.

CỔNG BẰNG CHỨNG (evidence_score > 0 chỉ khi có bằng chứng thực tế):
  - Có bằng chứng: Tên tổ chức/năm cụ thể, số liệu cụ thể, hoặc sự kiện rõ ngày.
  - Không bằng chứng: 0.

{_FACT_CHECK_INSTRUCTION}

GỢI Ý NGUỒN TỐT HƠN (better_source_suggestions):
  - Gợi ý 2-3 nguồn dạng: "Tên nguồn/cơ sở dữ liệu - mô tả ngắn".

THANG ĐIỂM & CHỐNG DỒN ĐIỂM:
  - evidence_score (0–100): Nhiều nguồn + số liệu: 60–90. Một nguồn: 30–60. Không có nguồn thực: 0.
  - Lập luận khác nhau PHẢI có điểm khác nhau. KHÔNG dùng số tròn trăm (100) hoặc tận cùng là 0 (ví dụ: 10,20,30...)."""


def _build_quick_rebuttal_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện PHẢN BIỆN NHANH (Quick Rebuttal) bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ - Phân tích phản biện và trả về JSON:
  - Viết "ai_rebuttal" (chỉ nhận xét về LẬP LUẬN/SUY LUẬN, tuyệt đối không bình luận về luận điểm hay bằng chứng khác):
    * Chỉ tập trung bình luận và đánh giá xem lập luận/suy luận (Reasoning) của người dùng mạnh/yếu như thế nào (1–3 câu).
  - RÀNG BUỘC LINK: Tuyệt đối KHÔNG chèn bất kỳ liên kết URL hay link markdown nào vào trong văn bản "ai_rebuttal". Văn bản "ai_rebuttal" phải hoàn toàn là text thuần túy.
  - Giọng ({age_group}): {_tone_rule(age_group)} | Độ sâu ({debate_level}): {_level_rule(debate_level)}

TRỌNG TÂM CHẤM: CHỈ tập trung vào reasoning_score.
  - claim_score = 0 | evidence_score = 0 | overall_score = reasoning_score.

THANG ĐIỂM & CHỐNG DỒN ĐIỂM:
  - reasoning_score (0–100): Chuỗi nhân quả rõ + phát hiện đúng lỗ logic: 60–90. Bỏ sót lỗ hổng quan trọng: 25–55. Suy luận yếu/sai: 0–25.
  - Lập luận khác nhau PHẢI có điểm khác nhau. KHÔNG dùng số tròn trăm (100) hoặc tận cùng là 0 (ví dụ: 10,20,30...)."""


def _build_quick_rebuttal_system_prompt_v2(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""MODE: QUICK_REBUTTAL

Ban la huan luyen vien che do PHAN BIEN NHANH bang {output_language}. Khong dung tieng Anh trong noi dung feedback, tru cac ten khoa rubric bat buoc.

Ban chat flow:
  - The AI has provided a weak argument.
  - Lumi da dua cho nguoi dung mot weak argument / luan diem yeu.
  - The user's task is to identify the flaw, fallacy, unsupported assumption, or counterexample in the weak argument.
  - Nguoi dung khong viet mot bai tranh bien day du; the user is not writing a full argument and not writing a full CER argument.
  - Nhiem vu cua nguoi dung la chi ra lo hong, gia dinh sai, nguy bien, hoac phan vi du ngan.
  - Nhiem vu cua ban la cham xem nguoi dung co bat dung loi chinh khong va huan luyen ky nang phan bien nhanh.

Tuyet doi khong cham nhu free_debate hoac full CER:
  - Khong yeu cau viet Claim-Evidence-Reasoning day du.
  - Khong che chung chung rang user thieu dan chung cu the, khong co lap luan logic, can xay dung C-E-R.
  - Chi nhac "thieu bang chung" neu do la ten loi cua weak argument va nguoi dung chua nhan ra loi do.

Rubric rieng — DUNG mode_scores, KHONG dung CER truc tiep:
  1. flaw_detection (0-100): nhan dien dung loi chinh trong weak argument.
     - 90-100: bat dung loi chinh VA goi ten duoc nguy bien (vd: khai quat hoa voi vang, nguyen nhan gia, dua vao so dong).
     - 70-89: bat dung loi nhung chua goi ten ro.
     - 40-69: co thay van de nhung con mo ho.
     - 0-39: khong bat duoc loi chinh.
  2. counter_example (0-100): co phan vi du, cau hoi phan bien, hoac huong bac bo.
     - 90-100: phan vi du cu the, truc tiep bac bo luan diem.
     - 70-89: co cau hoi phan bien hoac huong bac bo tot.
     - 40-69: co y phan bac nhung chua cu the.
     - 0-39: khong co phan vi du/cau hoi phan bien.
  3. explanation (0-100): giai thich vi sao loi do lam weak argument kem thuyet phuc.
     - 90-100: giai thich ro rang, noi loi voi hau qua logic.
     - 70-89: co giai thich nhung chua sau.
     - 40-69: chi noi loi ma khong giai thich.
     - 0-39: khong giai thich.
  4. focus (0-100): bam sat weak argument, khong lan man.
     - 90-100: hoan toan bam sat luan diem yeu.
     - 70-89: phan lon dung trong tam.
     - 40-69: co lan man sang chu de khac.
     - 0-39: phan hoi leech hoan toan.

overall = round(flaw_detection * 0.40 + explanation * 0.25 + counter_example * 0.20 + focus * 0.15)

Return mode_scores with:
  - flaw_detection: 0-100
  - counter_example: 0-100
  - explanation: 0-100
  - focus: 0-100
  - overall: 0-100

For quick_rebuttal, the CER fields are reused only for backward compatibility:
  - claim_score = mode_scores.flaw_detection
  - evidence_score = mode_scores.counter_example
  - reasoning_score = mode_scores.explanation
  - overall_score = mode_scores.overall
  - claim = quality of flaw detection
  - evidence = quality of counterexample or targeted rebuttal
  - reasoning = quality of explanation
  - claim = flaw_detection / quality of flaw detection
  - evidence = counter_example / quality of counterexample or targeted rebuttal
  - reasoning = explanation / quality of explanation
Do not evaluate this as a full CER argument.

Viet "ai_rebuttal" gom 3-5 cau huan luyen:
  - No ro user da bat dung diem nao trong weak argument.
  - Neu sai hoac thieu, chi ra loi chinh bi bo sot.
  - Goi y cach sua: goi ten loi, trich cum yeu, them mot phan vi du/cau hoi phan bien.
  - Giong ({age_group}): {_tone_rule(age_group)}
  - Do sau ({debate_level}): {_level_rule(debate_level)}

Feedback chi tap trung vao quick rebuttal quality, khong dung free debate or full CER feedback."""


def _build_full_argument_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là hệ thống chấm điểm và phản biện lập luận HOÀN CHỈNH (C+E+R) bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ - Phân tích lập luận và trả về JSON:
  - Viết "ai_rebuttal": Đoạn văn 4–6 câu đánh giá toàn diện cả 3 phần (luận điểm, bằng chứng, lập luận), chỉ ra phần yếu nhất và đưa ra gợi ý, ví dụ cụ thể (tên tổ chức, số liệu cụ thể nếu có). Tuyệt đối KHÔNG sử dụng các nhận xét/gợi ý chung chung mơ hồ.
  - RÀNG BUỘC LINK: Tuyệt đối KHÔNG chèn bất kỳ liên kết URL hay link markdown nào vào trong văn bản "ai_rebuttal". Văn bản "ai_rebuttal" phải hoàn toàn là text thuần túy.
  - Giọng ({age_group}): {_tone_rule(age_group)} | Độ sâu ({debate_level}): {_level_rule(debate_level)}

NGUỒN THAM KHẢO AI (evidence_source_links):
  - Hãy chọn một bài viết/số liệu thực tế từ "=== KẾT QUẢ TÌM KIẾM INTERNET ĐỂ AI LẤY BẰNG CHỨNG PHẢN BIỆN ===" để đưa vào phần bằng chứng trong "ai_rebuttal".
  - BẮT BUỘC cung cấp liên kết nguồn cụ thể trích xuất trực tiếp từ kết quả tìm kiếm đó để đưa vào "evidence_source_links".
  - Định dạng: "Tên nguồn - URL cụ thể của bài viết/nghiên cứu" (ví dụ: "UNESCO - https://www.unesco.org/en/articles/more-specific-path"). Tuyệt đối KHÔNG dùng link trang chủ chung chung (như https://unesco.org) nếu trong kết quả tìm kiếm có link bài viết cụ thể.

{_FACT_CHECK_INSTRUCTION}

CỔNG BẰNG CHỨNG (evidence_score > 0 chỉ khi có bằng chứng thực tế):
  - Có bằng chứng thực tế: Tên tổ chức/năm cụ thể, số liệu cụ thể, hoặc sự kiện rõ ngày tháng.
  - Không có bằng chứng thực tế (evidence_score = 0): Chỉ dùng "nhiều nghiên cứu cho thấy", "mọi người đều biết", hoặc lý lẽ suông không nguồn.

THANG ĐIỂM & CHỐNG DỒN ĐIỂM:
  - claim_score (0–100): Lập trường rõ + phạm vi cụ thể: 50–80. Mơ hồ: 20–45. Không rõ: 0–20.
  - evidence_score (0–100): Nhiều nguồn + số liệu: 60–90. Một nguồn: 30–60. Không bằng chứng: 0.
  - reasoning_score (0–100): Nhân quả rõ + không lỗi logic: 50–80. Có lỗ hổng: 25–50. Yếu: 0–25.
  - overall_score = round(claim×0.3 + evidence×0.3 + reasoning×0.4)
  - Lập luận khác nhau PHẢI có điểm khác nhau. KHÔNG dùng số tròn trăm (100) hoặc tận cùng là 0 (ví dụ: 10,20,30...)."""
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
    "cer": "full_argument",
    "full_argument": "full_argument",
}

PRACTICE_PROMPT_TYPES = {
    "claim_writing": "scenario_prompt",
    "find_evidence": "claim_prompt",
    "quick_rebuttal": "weak_argument",
    "full_argument": "argument_builder",
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
    if normalized == "full_argument":
        return "Hãy xây dựng một lập luận đầy đủ gồm Claim, Evidence và Reasoning cho chủ đề này."
    return "Hãy xây dựng câu trả lời tranh biện phù hợp."


def _practice_context(
    mode: str,
    practice_prompt: str | None,
    practice_round: int | None,
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
) -> str:
    if mode not in PRACTICE_PROMPT_TYPES or not practice_prompt:
        return ""
    labels = {
        "claim_writing": "Chủ đề/tình huống do Lumi đưa ra",
        "find_evidence": "Claim mẫu do Lumi đưa ra",
        "quick_rebuttal": "Luận điểm yếu do Lumi đưa ra",
        "full_argument": "Chủ đề xây dựng lập luận do Lumi đưa ra",
    }
    hint = ""
    if mode == "quick_rebuttal":
        clean_hint = str(practice_fallacy_hint or "").strip()
        clean_flaws = [
            str(item).strip()
            for item in (practice_target_flaws or [])
            if str(item).strip()
        ]
        hint = (
            f"Fallacy hint: {clean_hint or 'không cung cấp'}\n"
            f"Target flaws: {', '.join(clean_flaws) or 'không cung cấp'}\n"
        )
    return (
        f"=== ĐỀ BÀI LUYỆN TẬP ===\n"
        f"Mode: {mode}\n"
        f"Lượt: {practice_round or 1}\n"
        f"{labels[mode]}: {practice_prompt}\n"
        f"{hint}"
        f"Nhiệm vụ của người dùng: {practice_instruction_for_mode(mode)}\n"
        f"Chấm câu trả lời của người dùng theo đúng đề bài này. Không tự coi đề bài là câu trả lời của người dùng.\n\n"
    )


def _memory_context(memory_context: dict | None) -> str:
    if not memory_context:
        return ""
    user_memory = memory_context.get("user_memory") or {}
    global_state = user_memory.get("global") or {}
    mode_state = memory_context.get("mode_state") or {}
    weaknesses = global_state.get("recurring_weaknesses") or []
    suggestions = global_state.get("recurring_suggestions") or []
    mode_weaknesses = mode_state.get("common_weaknesses") or []
    if not any((weaknesses, suggestions, mode_weaknesses)):
        return ""
    return (
        "=== USER MEMORY ===\n"
        f"Recurring weaknesses: {weaknesses}\n"
        f"Recurring suggestions: {suggestions}\n"
        f"Current mode weaknesses: {mode_weaknesses}\n"
        "Use this only to personalize coaching and avoid repetitive feedback. "
        "Do not change CER scores because of past performance.\n\n"
    )


def _system_prompt_for_mode(mode: str, output_language: str, age_group: str, debate_level: str) -> str:
    mode = normalize_practice_mode(mode)
    if mode == "claim_writing":
        return _build_claim_writing_system_prompt(output_language, age_group, debate_level)
    elif mode == "find_evidence":
        return _build_find_evidence_system_prompt(output_language, age_group, debate_level)
    elif mode == "quick_rebuttal":
        return _build_quick_rebuttal_system_prompt_v2(output_language, age_group, debate_level)
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
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
    practice_round: int | None = None,
    memory_context: dict | None = None,
    user_search_context: str = "",
    ai_search_context: str = "",
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
    practice_section = _practice_context(
        mode,
        practice_prompt,
        practice_round,
        practice_fallacy_hint,
        practice_target_flaws,
    )
    memory_section = _memory_context(memory_context)

    user_search_section = f"\n{user_search_context}\n" if user_search_context else ""
    ai_search_section = f"\n{ai_search_context}\n" if ai_search_context else ""

    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"{history_section}"
        f"{memory_section}"
        f"{practice_section}"
        f"{user_search_section}"
        f"{ai_search_section}"
        f"\n=== LẬP LUẬN HIỆN TẠI CỦA NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ===\n"
        f"Phân tích lập luận trên và trả về DUY NHẤT JSON hợp lệ (không có text nào trước JSON, không markdown):\n"
        f"{_json_schema_for_mode(mode, output_language)}"
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
    elif normalized == "claim_writing":
        task = (
            "Hãy tạo đúng 1 tình huống thực tế hoặc chủ đề phụ ngắn gọn (1-2 câu) dựa trên chủ đề phiên được giao. "
            "Tình huống phải cụ thể, có mâu thuẫn hoặc sự lựa chọn để người học dễ viết claim. "
            "Tuyệt đối không viết câu claim hộ người học. "
            "Tạo kèm 2-3 góc nhìn gợi ý ngắn gọn trong suggested_angles."
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
    response_tail = (
        f'  "instruction": "{practice_instruction_for_mode(normalized)}",\n'
        '  "suggested_angles": ["<góc nhìn gợi ý 1>", "<góc nhìn gợi ý 2>", "<góc nhìn gợi ý 3>"]\n'
        if normalized == "claim_writing"
        else f'  "instruction": "{practice_instruction_for_mode(normalized)}"\n'
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
        f"{response_tail}"
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
    practice_fallacy_hint: str | None = None,
    practice_target_flaws: list[str] | None = None,
    practice_round: int | None = None,
    memory_context: dict | None = None,
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
        practice_fallacy_hint=practice_fallacy_hint,
        practice_target_flaws=practice_target_flaws,
        practice_round=practice_round,
        memory_context=memory_context,
    )
