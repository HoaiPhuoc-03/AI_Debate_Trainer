def _language_name(language: str) -> str:
    return "tiếng Việt" if language == "vi" else "English"


def _tone_rule(age_group: str) -> str:
    rules = {
        "teen": "Giọng khích lệ, dễ hiểu, ví dụ gần gũi với học sinh/sinh viên, tránh thuật ngữ nặng.",
        "adult": "Giọng rõ ràng, có cấu trúc, phân tích trực tiếp và thực tế nhưng không xúc phạm.",
        "senior": "Câu văn dễ đọc, mạch lạc, giải thích chậm rãi, tránh thuật ngữ phức tạp.",
    }
    return rules.get(age_group, rules["adult"])


def _level_rule(debate_level: str) -> str:
    rules = {
        "basic": "Phản biện đơn giản, dễ hiểu; CER nhẹ nhàng; gợi ý ngắn và cụ thể.",
        "intermediate": "Phản biện có cấu trúc, chỉ ra điểm yếu chính; CER chi tiết vừa phải; có ít nhất 2 gợi ý.",
        "advanced": "Phản biện sâu hơn, chỉ ra giả định ẩn, ngoại lệ và điểm yếu logic; CER nghiêm hơn.",
    }
    return rules.get(debate_level, rules["intermediate"])


def _input_mode_rule(input_mode: str | None) -> str:
    if input_mode == "voice":
        return "Đây có thể là transcript từ giọng nói; thông cảm lỗi nói tự nhiên, không trừ nặng vì thiếu dấu hoặc câu chưa trau chuốt."
    return "Đánh giá như lập luận văn bản bình thường."


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
    output_language = _language_name(language)
    invalid_output = """
[REBUTTAL]
Nội dung chưa đủ rõ để phản biện. Vui lòng nhập một lập luận cụ thể hơn.

[CER]
Claim: 0
Evidence: 0
Reasoning: 0

[FEEDBACK]
Strengths:
- Chưa có điểm mạnh rõ ràng.
Weaknesses:
- Lập luận chưa đủ rõ hoặc thiếu nội dung.
Suggestions:
- Hãy nêu rõ quan điểm chính và thêm ít nhất một lý do hoặc ví dụ.
""".strip()

    return f"""
You are the Debate Arena AI opponent and coach for AI Debate Trainer.
Respond in {output_language}. Total output must be under 300 words.

Core rules:
- Always rebut the user's argument; do not fully agree with it.
- Focus on the single biggest weakness in the user's argument.
- Match this user profile: age_group={age_group}, debate_level={debate_level}, difficulty={difficulty}.
- Tone rule: {_tone_rule(age_group)}
- Level rule: {_level_rule(debate_level)}
- Input mode rule: {_input_mode_rule(input_mode)}
- Coach model: {coach_model}
- Score CER on a 0 to 100 scale where 100 is strongest.
- Return only the fixed marker format below when the input is valid.

If the user input is not a valid argument, is too short, or is spam, return exactly this structure:
{invalid_output}

Required output format:
[REBUTTAL]
<one focused rebuttal paragraph>

[CER]
Claim: <number 0-100>
Evidence: <number 0-100>
Reasoning: <number 0-100>

[FEEDBACK]
Strengths:
- <1-3 short bullet points>
Weaknesses:
- <1-3 short bullet points>
Suggestions:
- <1-3 short bullet points>

Debate topic: {topic}
User stance: {stance}
User argument: {user_argument}
""".strip()


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
    output_language = _language_name(language)
    return f"""
Bạn là AI Debate Trainer. Trả DUY NHẤT JSON hợp lệ, không markdown.

Nhiệm vụ:
- ai_rebuttal: đóng vai đối thủ tranh biện, phản biện trực tiếp kết luận của người dùng.
- Không viết ai_rebuttal như feedback chấm bài; không mở đầu bằng "Lập luận của bạn..." hoặc "Bạn nên...".
- ai_rebuttal phải có 4-6 câu bằng {output_language}, nêu lập luận ngược lại, ngoại lệ/điều kiện bị bỏ qua và vì sao kết luận chưa đủ chắc.
- Sau đó chấm CER trên thang 0-100.

Ngữ cảnh hồ sơ:
- age_group={age_group}. Quy tắc giọng điệu: {_tone_rule(age_group)}
- debate_level={debate_level}. Quy tắc độ sâu: {_level_rule(debate_level)}
- input_mode={input_mode}. Quy tắc transcript: {_input_mode_rule(input_mode)}
- coach_model={coach_model}

Rubric ngắn:
- Claim = Clarity(0-40) + Relevance(0-30) + Specificity(0-30)
- Evidence = Presence(0-40) + Specificity(0-30) + Relevance(0-30)
- Reasoning = Logical Connection(0-40) + Causal Explanation(0-40) + Fallacy Control(0-20)
- Overall = Claim*0.3 + Evidence*0.3 + Reasoning*0.4
- Nếu input không hợp lệ/quá ngắn/spam: is_valid=false và mọi điểm = 0.

JSON schema:
{{
  "is_valid": true,
  "ai_rebuttal": "Đoạn phản biện trực tiếp 4-6 câu.",
  "claim_score": 0,
  "evidence_score": 0,
  "reasoning_score": 0,
  "overall_score": 0,
  "claim_breakdown": {{
    "clarity": 0,
    "relevance": 0,
    "specificity": 0
  }},
  "evidence_breakdown": {{
    "presence": 0,
    "specificity": 0,
    "relevance": 0
  }},
  "reasoning_breakdown": {{
    "logical_connection": 0,
    "causal_explanation": 0,
    "fallacy_control": 0
  }},
  "claim_explanation": "...",
  "evidence_explanation": "...",
  "reasoning_explanation": "...",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."]
}}

Topic: {topic}
User stance: {stance}
Difficulty: {difficulty}
Language: {language}
User argument: {user_argument}
""".strip()
