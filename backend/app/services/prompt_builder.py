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
    return f"""Bạn là hệ thống chấm điểm và phản biện tranh luận chuyên nghiệp bằng {output_language}. KHÔNG dùng tiếng Anh.

NHIỆM VỤ — BẮT BUỘC thực hiện suy nghĩ phân tích nháp chi tiết trong block [SUY NGHĨ] trước khi chấm điểm và viết phản hồi chính thức.
Hãy sử dụng nhiều thời gian suy nghĩ để đưa ra lập luận chính xác, sắc bén nhất.

Quy định độ dài: Độ dài tổng của các phần chính thức (từ [ĐIỂM SỐ] trở đi) TUYỆT ĐỐI KHÔNG vượt quá 300 từ.

CỔNG BẰNG CHỨNG (Evidence Gate):
- Bằng chứng thực tế phải có nguồn cụ thể (tên tổ chức + năm, nghiên cứu, báo cáo...) hoặc số liệu/sự kiện thực tế rõ ràng.
- Nếu không có nguồn thực tế/số liệu, điểm Evidence BẮT BUỘC bằng 0.

QUY TẮC CHẤM ĐIỂM (Thang điểm 10):
- Claim (Luận điểm): 0-3 (Mơ hồ); 4-7 (Chưa rõ ràng); 8-10 (Rõ ràng, trực tiếp).
- Evidence (Bằng chứng): 0-3 (Không có/yếu); 4-7 (Chung chung); 8-10 (Số liệu, nguồn cụ thể).
- Reasoning (Lập luận): 0-3 (Thiếu logic); 4-7 (Chưa chặt chẽ); 8-10 (Logic, không ngụy biện).

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
[SUY NGHĨ]
(Phân tích chi tiết suy nghĩ về lập luận của người dùng: Lập trường, nguồn bằng chứng, chuỗi nhân quả, lỗi logic.)

[ĐIỂM SỐ]
- Claim: <điểm số>/10
- Evidence: <điểm số>/10
- Reasoning: <điểm số>/10

[PHÂN TÍCH CER]
(Tối đa 2 câu. Đánh giá trực tiếp và ngắn gọn vào tiêu chí chấm điểm, không nhận xét chung chung.)

[PHẢN BIỆN LẠI]
(Tối đa 3 câu. Bắt đầu bằng: "Tuy nhiên,", "Thực tế cho thấy,", hoặc "Ngược lại,". Chỉ tập trung phản bác 1 điểm yếu quan trọng nhất trong lập luận của người dùng, dùng phản ví dụ hoặc trường hợp ngoại lệ.)

[GỢI Ý CẢI THIỆN]
(Chính xác 1 câu duy nhất. Đưa ra giải pháp khắc phục cụ thể cho điểm yếu vừa bị phản biện.)

CONTRACT RULES:
- Respond only in tiếng Việt.
- Write "ai_rebuttal" only in tiếng Việt.
- Do not mix English into the rebuttal.
- If there is no named source, evidence_score = 0 and all evidence breakdown values = 0.
- Write a 4–6 sentence rebuttal.
- Open with the counter-position.
"""


def _json_schema(output_language: str) -> str:
    """Legacy helper for backward compatibility — no longer used in new prompts."""
    return ""


def _build_claim_writing_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên AI hỗ trợ người dùng luyện viết Luận điểm (Claim) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

CƠ CHẾ HOẠT ĐỘNG:
  1. KHỞI ĐẦU: Nếu người dùng gửi thông điệp bắt đầu (như "Bắt đầu", "Bắt đầu bài tập", v.v.) và chưa có lịch sử trước đó:
     - Hãy đưa ra một chủ đề tranh luận thú vị và yêu cầu người dùng viết một Luận điểm (Claim) thể hiện rõ ràng lập trường của họ đối với chủ đề đó.
     - Đặt tất cả điểm số (Claim, Evidence, Reasoning) bằng 0.
     - Viết yêu cầu/chủ đề trong phần [PHẢN BIỆN LẠI] (dài 4-6 câu).
  2. ĐÁNH GIÁ: Nếu người dùng gửi luận điểm (Claim) ở lượt tiếp theo:
     - Phân tích và chấm điểm luận điểm của họ (Claim: 0-10, Evidence: 0/10, Reasoning: 0/10).
     - Viết nhận xét chi tiết hướng dẫn (Coaching) trong [PHẢN BIỆN LẠI] (dài 4-6 câu). Chỉ ra ưu điểm lớn nhất và gợi ý cách sửa đổi để làm câu rõ ràng hơn. Giọng điệu thân thiện, tích cực.
     - CUỐI phần [PHẢN BIỆN LẠI], hãy đưa ra thêm một chủ đề tranh luận MỚI để người dùng tiếp tục luyện tập ở lượt kế tiếp.

NHIỆM VỤ — BẮT BUỘC thực hiện suy nghĩ phân tích nháp chi tiết trong block [SUY NGHĨ] trước khi phản hồi chính thức.
Quy định độ dài: Độ dài tổng các phần chính thức (từ [ĐIỂM SỐ] trở đi) TUYỆT ĐỐI KHÔNG vượt quá 300 từ.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
[SUY NGHĨ]
(Phân tích chi tiết suy nghĩ về câu viết của người dùng hoặc xây dựng chủ đề khởi đầu.)

[ĐIỂM SỐ]
- Claim: <điểm số>/10
- Evidence: 0/10
- Reasoning: 0/10

[PHÂN TÍCH CER]
(Tối đa 2 câu nhận xét về luận điểm.)

[PHẢN BIỆN LẠI]
(Nội dung phản hồi chính hoặc chủ đề luyện tập mới của huấn luyện viên AI.)

[GỢI Ý CẢI THIỆN]
(Chính xác 1 câu gợi ý cải thiện.)
"""


def _build_find_evidence_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên AI hỗ trợ người dùng luyện tìm Bằng chứng (Evidence) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

CƠ CHẾ HOẠT ĐỘNG:
  1. KHỞI ĐẦU: Nếu người dùng gửi thông điệp bắt đầu (như "Bắt đầu", "Bắt đầu bài tập", v.v.) và chưa có lịch sử trước đó:
     - Hãy đưa ra một Luận điểm (Claim) cụ thể liên quan đến chủ đề tranh luận và yêu cầu người dùng tìm bằng chứng thực tế hỗ trợ cho luận điểm đó.
     - Đặt tất cả điểm số bằng 0.
     - Viết yêu cầu/Luận điểm trong phần [PHẢN BIỆN LẠI] (dài 4-6 câu).
  2. ĐÁNH GIÁ: Nếu người dùng gửi bằng chứng ở lượt tiếp theo:
     - Phân tích xem bằng chứng có nguồn cụ thể (tổ chức, báo cáo, năm) hoặc số liệu/sự kiện rõ ràng không.
     - Chấm điểm thực tế cho Evidence (0-10). Claim và Reasoning có thể chấm 0 hoặc mức tối thiểu.
     - Viết nhận xét chi tiết về bằng chứng trong [PHẢN BIỆN LẠI] (dài 4-6 câu). Giải thích rõ vì sao bằng chứng thuyết phục hoặc cần bổ sung gì.
     - CUỐI phần [PHẢN BIỆN LẠI], hãy đưa ra thêm một Luận điểm (Claim) MỚI để người dùng tiếp tục luyện tập ở lượt kế tiếp.

NHIỆM VỤ — BẮT BUỘC thực hiện suy nghĩ phân tích nháp chi tiết trong block [SUY NGHĨ] trước khi phản hồi chính thức.
Quy định độ dài: Độ dài tổng các phần chính thức (từ [ĐIỂM SỐ] trở đi) TUYỆT ĐỐI KHÔNG vượt quá 300 từ.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
[SUY NGHĨ]
(Phân tích chi tiết suy nghĩ về bằng chứng của người dùng.)

[ĐIỂM SỐ]
- Claim: 0/10
- Evidence: <điểm số>/10
- Reasoning: 0/10

[PHÂN TÍCH CER]
(Tối đa 2 câu nhận xét về dẫn chứng.)

[PHẢN BIỆN LẠI]
(Nhận xét của huấn luyện viên AI và Luận điểm mới cho lượt tiếp theo.)

[GỢI Ý CẢI THIỆN]
(Chính xác 1 câu gợi ý cách tìm dẫn chứng tốt hơn.)
"""


def _build_quick_rebuttal_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên AI hỗ trợ người dùng luyện Phản biện nhanh (Quick Rebuttal) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

CƠ CHẾ HOẠT ĐỘNG:
  1. KHỞI ĐẦU: Nếu người dùng gửi thông điệp bắt đầu (như "Bắt đầu", "Bắt đầu bài tập", v.v.) và chưa có lịch sử trước đó:
     - Hãy đưa ra một lập luận yếu chứa lỗi logic rõ ràng (ngụy biện bù nhìn, nhân quả sai, khái quát hóa vội vã...) ở lập trường đối lập với stance của người dùng.
     - Yêu cầu người dùng phát hiện lỗi logic hoặc phản bác lại lập luận yếu đó.
     - Đặt tất cả điểm số bằng 0.
     - Viết lập luận yếu đó trong phần [PHẢN BIỆN LẠI] (dài 4-6 câu).
  2. ĐÁNH GIÁ: Nếu người dùng gửi phản biện ở lượt tiếp theo:
     - Phân tích xem người dùng có phát hiện đúng lỗi logic/lỗ hổng hay không.
     - Chấm điểm thực tế cho Reasoning (0-10). Claim và Evidence chấm ở mức 0 hoặc tối thiểu.
     - Viết nhận xét chi tiết trong [PHẢN BIỆN LẠI] (dài 4-6 câu). Giải thích lỗi logic đó là gì và vì sao phản biện của họ tốt hoặc cần cải thiện.
     - CUỐI phần [PHẢN BIỆN LẠI], hãy đưa ra thêm một lập luận yếu MỚI để người dùng tiếp tục phản biện ở lượt kế tiếp.

NHIỆM VỤ — BẮT BUỘC thực hiện suy nghĩ phân tích nháp chi tiết trong block [SUY NGHĨ] trước khi phản hồi chính thức.
Quy định độ dài: Độ dài tổng các phần chính thức (từ [ĐIỂM SỐ] trở đi) TUYỆT ĐỐI KHÔNG vượt quá 300 từ.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
[SUY NGHĨ]
(Phân tích chi tiết suy nghĩ về phản biện nhanh của người dùng.)

[ĐIỂM SỐ]
- Claim: 0/10
- Evidence: 0/10
- Reasoning: <điểm số>/10

[PHÂN TÍCH CER]
(Tối đa 2 câu nhận xét về lập luận phản bác.)

[PHẢN BIỆN LẠI]
(Nhận xét của huấn luyện viên AI và lập luận yếu mới cho lượt tiếp theo.)

[GỢI Ý CẢI THIỆN]
(Chính xác 1 câu gợi ý cải thiện.)
"""


def _build_full_argument_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên AI hỗ trợ người dùng xây dựng Lập luận hoàn chỉnh (C+E+R) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ:
- Đánh giá toàn diện một lập luận đầy đủ bao gồm ba thành phần: Luận điểm (Claim), Bằng chứng (Evidence), và Suy luận (Reasoning).
- BẮT BUỘC thực hiện suy nghĩ phân tích nháp chi tiết trong block [SUY NGHĨ] trước khi chấm điểm và viết phản hồi chính thức.

Quy định độ dài: Độ dài tổng các phần chính thức (từ [ĐIỂM SỐ] trở đi) TUYỆT ĐỐI KHÔNG vượt quá 300 từ.

THANG ĐIỂM (Chấm đầy đủ cả ba tiêu chí trên thang điểm 10):
- Claim: 0-10
- Evidence: 0-10
- Reasoning: 0-10

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
[SUY NGHĨ]
(Phân tích chi tiết suy nghĩ về lập luận hoàn chỉnh C+E+R của người dùng.)

[ĐIỂM SỐ]
- Claim: <điểm số>/10
- Evidence: <điểm số>/10
- Reasoning: <điểm số>/10

[PHÂN TÍCH CER]
(Tối đa 2 câu nhận xét toàn diện về cấu trúc lập luận.)

[PHẢN BIỆN LẠI]
(Tối đa 3 câu nhận xét chi tiết, chỉ ra điểm sáng nhất và lỗ hổng lớn nhất cần khắc phục.)

[GỢI Ý CẢI THIỆN]
(Chính xác 1 câu gợi ý cải thiện thiết thực nhất.)
"""


def _build_claim_writing_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str,
    debate_level: str,
    input_mode: str,
    language: str,
    turn_history: list[dict] | None,
) -> list[dict[str, str]]:
    output_language = _language_name(language)
    system_prompt = _build_claim_writing_system_prompt(output_language, age_group, debate_level)
    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""
    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"Chế độ   : Luyện viết Claim\n"
        f"{history_section}"
        f"\n=== LẬP LUẬN HOẶC TIN NHẮN NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ===\n"
        f"Hãy phân tích và trả về phản hồi chính xác theo cấu trúc sau. TUYỆT ĐỐI không sử dụng JSON:\n"
        f"[SUY NGHĨ]\n"
        f"(Nháp phân tích chi tiết)\n\n"
        f"[ĐIỂM SỐ]\n"
        f"- Claim: <điểm>/10\n"
        f"- Evidence: <điểm>/10\n"
        f"- Reasoning: <điểm>/10\n\n"
        f"[PHÂN TÍCH CER]\n"
        f"<tối đa 2 câu phân tích>\n\n"
        f"[PHẢN BIỆN LẠI]\n"
        f"<tối đa 3 câu phản hồi/hướng dẫn>\n\n"
        f"[GỢI Ý CẢI THIỆN]\n"
        f"<chính xác 1 câu gợi ý>\n"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _build_find_evidence_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str,
    debate_level: str,
    input_mode: str,
    language: str,
    turn_history: list[dict] | None,
) -> list[dict[str, str]]:
    output_language = _language_name(language)
    system_prompt = _build_find_evidence_system_prompt(output_language, age_group, debate_level)
    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""
    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"Chế độ   : Luyện tìm Evidence\n"
        f"{history_section}"
        f"\n=== BẰNG CHỨNG (EVIDENCE) HOẶC TIN NHẮN NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ===\n"
        f"Hãy phân tích và trả về phản hồi chính xác theo cấu trúc sau. TUYỆT ĐỐI không sử dụng JSON:\n"
        f"[SUY NGHĨ]\n"
        f"(Nháp phân tích chi tiết)\n\n"
        f"[ĐIỂM SỐ]\n"
        f"- Claim: <điểm>/10\n"
        f"- Evidence: <điểm>/10\n"
        f"- Reasoning: <điểm>/10\n\n"
        f"[PHÂN TÍCH CER]\n"
        f"<tối đa 2 câu phân tích>\n\n"
        f"[PHẢN BIỆN LẠI]\n"
        f"<tối đa 3 câu phản hồi/hướng dẫn>\n\n"
        f"[GỢI Ý CẢI THIỆN]\n"
        f"<chính xác 1 câu gợi ý>\n"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _build_quick_rebuttal_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str,
    debate_level: str,
    input_mode: str,
    language: str,
    turn_history: list[dict] | None,
) -> list[dict[str, str]]:
    output_language = _language_name(language)
    system_prompt = _build_quick_rebuttal_system_prompt(output_language, age_group, debate_level)
    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""
    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"Chế độ   : Phản biện nhanh\n"
        f"{history_section}"
        f"\n=== PHẢN BIỆN HOẶC TIN NHẮN NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ===\n"
        f"Hãy phân tích và trả về phản hồi chính xác theo cấu trúc sau. TUYỆT ĐỐI không sử dụng JSON:\n"
        f"[SUY NGHĨ]\n"
        f"(Nháp phân tích chi tiết)\n\n"
        f"[ĐIỂM SỐ]\n"
        f"- Claim: <điểm>/10\n"
        f"- Evidence: <điểm>/10\n"
        f"- Reasoning: <điểm>/10\n\n"
        f"[PHÂN TÍCH CER]\n"
        f"<tối đa 2 câu phân tích>\n\n"
        f"[PHẢN BIỆN LẠI]\n"
        f"<tối đa 3 câu phản hồi/hướng dẫn>\n\n"
        f"[GỢI Ý CẢI THIỆN]\n"
        f"<chính xác 1 câu gợi ý>\n"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _build_full_argument_messages(
    topic: str,
    stance: str,
    difficulty: str,
    user_argument: str,
    age_group: str,
    debate_level: str,
    input_mode: str,
    language: str,
    turn_history: list[dict] | None,
) -> list[dict[str, str]]:
    output_language = _language_name(language)
    system_prompt = _build_full_argument_system_prompt(output_language, age_group, debate_level)
    history_block = _format_turn_history(turn_history)
    history_section = f"\n{history_block}\n" if history_block else ""
    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"Chế độ   : Xây dựng lập luận hoàn chỉnh (C+E+R)\n"
        f"{history_section}"
        f"\n=== LẬP LUẬN HOÀN CHỈNH (C+E+R) NGƯỜI DÙNG NHẬP ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ===\n"
        f"Hãy phân tích và trả về phản hồi chính xác theo cấu trúc sau. TUYỆT ĐỐI không sử dụng JSON:\n"
        f"[SUY NGHĨ]\n"
        f"(Nháp phân tích chi tiết)\n\n"
        f"[ĐIỂM SỐ]\n"
        f"- Claim: <điểm>/10\n"
        f"- Evidence: <điểm>/10\n"
        f"- Reasoning: <điểm>/10\n\n"
        f"[PHÂN TÍCH CER]\n"
        f"<tối đa 2 câu phân tích>\n\n"
        f"[PHẢN BIỆN LẠI]\n"
        f"<tối đa 3 câu phản hồi/hướng dẫn>\n\n"
        f"[GỢI Ý CẢI THIỆN]\n"
        f"<chính xác 1 câu gợi ý>\n"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


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
) -> list[dict[str, str]]:
    """
    Returns a [system, user] message pair for the Groq API.
    """
    if mode == "claim_writing":
        return _build_claim_writing_messages(
            topic, stance, difficulty, user_argument, age_group, debate_level, input_mode, language, turn_history
        )
    elif mode == "find_evidence":
        return _build_find_evidence_messages(
            topic, stance, difficulty, user_argument, age_group, debate_level, input_mode, language, turn_history
        )
    elif mode == "quick_rebuttal":
        return _build_quick_rebuttal_messages(
            topic, stance, difficulty, user_argument, age_group, debate_level, input_mode, language, turn_history
        )
    elif mode == "full_argument":
        return _build_full_argument_messages(
            topic, stance, difficulty, user_argument, age_group, debate_level, input_mode, language, turn_history
        )

    # Default: free_debate
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
        f"\n=== YÊU CẦU ĐỊNH DẠNG ĐẦU RA BẮT BUỘC ===\n"
        f"Hãy phân tích và trả về phản hồi chính xác theo cấu trúc sau. TUYỆT ĐỐI không sử dụng JSON:\n"
        f"[SUY NGHĨ]\n"
        f"(Nháp phân tích chi tiết)\n\n"
        f"[ĐIỂM SỐ]\n"
        f"- Claim: <điểm>/10\n"
        f"- Evidence: <điểm>/10\n"
        f"- Reasoning: <điểm>/10\n\n"
        f"[PHÂN TÍCH CER]\n"
        f"<tối đa 2 câu phân tích>\n\n"
        f"[PHẢN BIỆN LẠI]\n"
        f"<tối đa 3 câu phản phản biện>\n\n"
        f"[GỢI Ý CẢI THIỆN]\n"
        f"<chính xác 1 câu gợi ý>\n\n"
        f"CONTRACT RULES:\n"
        f"- Write the rebuttal only in tiếng Việt.\n"
        f"- Avoid score clustering; use the full range.\n"
        f"- If there is no named evidence, Evidence = 0.\n"
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
    mode: str = "free_debate",
) -> list[dict[str, str]]:
    """Legacy entry point — routes to build_cer_messages."""
    return build_cer_messages(
        topic=topic, stance=stance, difficulty=difficulty,
        user_argument=user_argument, age_group=age_group,
        debate_level=debate_level, input_mode=input_mode or "text",
        language=language, turn_history=turn_history,
        mode=mode,
    )