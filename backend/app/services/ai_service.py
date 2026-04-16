from google import genai
from app.core.config import settings


def build_prompt(topic: str, stance: str, difficulty: str, user_argument: str) -> str:
    return f"""
Bạn là đối thủ tranh biện trong hệ thống AI Debate Trainer.

Yêu cầu:
- Luôn trả lời bằng tiếng Việt.
- Phản biện ngắn gọn, rõ ràng, không lan man.
- Tối đa khoảng 120-180 từ.
- Tập trung phản biện trực tiếp vào lập luận của người dùng.
- Không dùng ngôn ngữ xúc phạm.

Chủ đề: {topic}
Lập trường người dùng: {stance}
Độ khó: {difficulty}

Lập luận của người dùng:
{user_argument}

Hãy viết đúng 1 đoạn phản biện đối lập.
""".strip()


def generate_rebuttal(topic: str, stance: str, difficulty: str, user_argument: str) -> dict:
    if settings.DEMO_MODE:
        return {
            "ok": True,
            "text": "Đây là phản biện mẫu trong demo mode. Hệ thống đang dùng dữ liệu dự phòng.",
            "error": ""
        }

    if not settings.GEMINI_API_KEY:
        return {
            "ok": False,
            "text": "Thiếu GEMINI_API_KEY trong file .env",
            "error": "missing_api_key"
        }

    try:
        prompt = build_prompt(topic, stance, difficulty, user_argument)

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        text = getattr(response, "text", None)
        if text:
            return {
                "ok": True,
                "text": text.strip(),
                "error": ""
            }

        return {
            "ok": False,
            "text": "Gemini không trả về nội dung hợp lệ.",
            "error": "empty_output"
        }

    except Exception as e:
        return {
            "ok": False,
            "text": f"Gemini lỗi: {str(e)}",
            "error": str(e)
        }