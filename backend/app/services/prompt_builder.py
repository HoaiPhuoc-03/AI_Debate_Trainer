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
    return f"""Ban la he thong cham diem va phan bien tranh luan bang {output_language}. Khong dung tieng Anh trong noi dung feedback.

NHIEM VU - phan tich noi bo roi tra ve DUY NHAT JSON hop le:
  Nguoi dung chon mot lap truong: Ung ho hoac Phan doi. AI giu vai tro doi lap voi lap truong cua nguoi dung.
  Truoc khi dien JSON, xac dinh noi bo:
  a) Co nguon/to chuc/so lieu co ten cu the khong?
  b) Lap luan chinh la gi? Pham vi co ro khong?
  c) Co loi logic hoac gia dinh an khong?

Viet ai_rebuttal - 4-6 cau phan bien bang {output_language}:
  - Phai mo dau bang: "Tuy nhien,", "Thuc te cho thay," hoac "Nguoc lai,"
  - Phai phan hoi noi dung cu the trong lap luan cua nguoi dung.
  - Khong viet phan bien chung chung ap dung cho moi lap luan.
  - Giong ({age_group}): {_tone_rule(age_group)}
  - Do sau ({debate_level}): {_level_rule(debate_level)}

CONG BANG CHUNG - bat buoc ap dung truoc khi cham:
  Co bang chung thuc: ten to chuc + nam, so lieu cu the, su kien co ngay.
  Khong phai bang chung: "nhieu nghien cuu cho thay", "moi nguoi biet", ly luan thuan tuy khong co nguon.

THANG DIEM:
  claim_score: chat luong luan diem chinh (0-100)
  evidence_score: chat luong bang chung (0-100, = 0 neu khong co bang chung thuc)
  reasoning_score: chat luong suy luan (0-100)
  overall_score = round(claim*0.3 + evidence*0.3 + reasoning*0.4)

CHONG DON DIEM:
  - Khong dung cung diem cho cac lap luan khac nhau ve chat luong.
  - Khong dung toan so tron.
  - Diem phai phan anh tung cau tra loi cu the."""


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
        '  "evidence_quote": "<trich nguyen van nguon/so lieu tu lap luan, hoac NONE>",\n'
        '  "checklist": {"has_clear_position": true/false, "has_bounded_scope": true/false, "has_real_evidence": true/false, "has_causal_chain": true/false},\n'
        f'  "ai_rebuttal": "<4-6 cau phan bien truc tiep lap luan tren bang {output_language}>",\n'
        '  "claim_score": <so nguyen>,\n'
        '  "evidence_score": <so nguyen, bat buoc 0 neu khong co bang chung thuc>,\n'
        '  "reasoning_score": <so nguyen>,\n'
        '  "overall_score": <round(claim*0.3 + evidence*0.3 + reasoning*0.4)>,\n'
        '  "claim_breakdown": {"clarity": <0-40>, "relevance": <0-30>, "specificity": <0-30>},\n'
        '  "evidence_breakdown": {"presence": <0-40>, "evidence_specificity": <0-30>, "evidence_relevance": <0-30>},\n'
        '  "reasoning_breakdown": {"logical_connection": <0-40>, "causal_explanation": <0-40>, "fallacy_control": <0-20>},\n'
        f'  "claim_explanation": "<ly do diem claim bang {output_language}>",\n'
        f'  "evidence_explanation": "<ly do diem evidence bang {output_language}>",\n'
        f'  "reasoning_explanation": "<ly do diem reasoning bang {output_language}>",\n'
        f'  "strengths": ["<diem manh bang {output_language}>"],\n'
        f'  "weaknesses": ["<diem yeu bang {output_language}>"],\n'
        f'  "suggestions": ["<goi y bang {output_language}>"]\n'
        "}"
    )


# ---------------------------------------------------------------------------
# Mode-specific system prompts — written IN Vietnamese, NO numeric scores
# ---------------------------------------------------------------------------

def _build_claim_writing_system_prompt(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""Bạn là huấn luyện viên luyện viết LUẬN ĐIỂM (Claim) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ:
  Người dùng luôn chọn một trong hai lập trường: Ủng hộ hoặc Phản đối.
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
  Người dùng luôn chọn một trong hai lập trường: Ủng hộ hoặc Phản đối.
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
  Người dùng luôn chọn một trong hai lập trường: Ủng hộ hoặc Phản đối.
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


def _build_quick_rebuttal_system_prompt_v2(output_language: str, age_group: str, debate_level: str) -> str:
    return f"""MODE: QUICK_REBUTTAL

Ban la huan luyen vien che do PHAN BIEN NHANH bang {output_language}. Khong dung tieng Anh trong noi dung feedback, tru cac ten khoa rubric bat buoc.

Ban chat flow:
  - Lumi da dua cho nguoi dung mot weak argument / luan diem yeu.
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
    return f"""Bạn là hệ thống chấm điểm và phản biện lập luận HOÀN CHỈNH (C+E+R) bằng {output_language}. KHÔNG dùng tiếng Anh trong nội dung.

NHIỆM VỤ — phân tích nội bộ rồi trả về DUY NHẤT JSON (không có text nào trước JSON):
  Người dùng luôn chọn một trong hai lập trường: Ủng hộ hoặc Phản đối.
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


def _practice_context(mode: str, practice_prompt: str | None, practice_round: int | None) -> str:
    if mode not in PRACTICE_PROMPT_TYPES or not practice_prompt:
        return ""
    labels = {
        "claim_writing": "Chủ đề/tình huống do Lumi đưa ra",
        "find_evidence": "Claim mẫu do Lumi đưa ra",
        "quick_rebuttal": "Luận điểm yếu do Lumi đưa ra",
        "full_argument": "Chủ đề xây dựng lập luận do Lumi đưa ra",
    }
    return (
        f"=== ĐỀ BÀI LUYỆN TẬP ===\n"
        f"Mode: {mode}\n"
        f"Lượt: {practice_round or 1}\n"
        f"{labels[mode]}: {practice_prompt}\n"
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
    practice_round: int | None = None,
    memory_context: dict | None = None,
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
    memory_section = _memory_context(memory_context)

    user_prompt = (
        f"=== NGỮ CẢNH ===\n"
        f"Chủ đề   : {topic}\n"
        f"Lập trường: {stance}\n"
        f"Độ khó   : {difficulty}\n"
        f"Nhập liệu: {_input_mode_rule(input_mode)}\n"
        f"{history_section}"
        f"{memory_section}"
        f"{practice_section}"
        f"\n=== LẬP LUẬN HIỆN TẠI CỦA NGƯỜI DÙNG ===\n"
        f"{user_argument}\n"
        f"\n=== YÊU CẦU ===\n"
        f"Phân tích lập luận trên và trả về DUY NHẤT JSON hợp lệ (không có text nào trước JSON, không markdown):\n"
        f"{_json_schema(output_language, mode)}"
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
        practice_round=practice_round,
        memory_context=memory_context,
    )
