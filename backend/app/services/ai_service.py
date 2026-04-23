import httpx
from app.core.config import settings


def build_prompt(topic: str, stance: str, difficulty: str, user_argument: str) -> str:
    return f"""
Bạn là đối thủ tranh biện.

Trả lời bằng tiếng Việt.
Viết đúng 1 đoạn phản biện ngắn, rõ ràng, dưới 120 từ.
Không lan man, không xúc phạm.

Chủ đề: {topic}
Lập trường người dùng: {stance}
Độ khó: {difficulty}
Lập luận của người dùng: {user_argument}

Hãy phản biện trực tiếp.
""".strip()


def extract_text_from_ollama(data: dict) -> str:
    # /api/chat -> message.content
    message = data.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    # /api/generate -> response
    response_text = data.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()

    return ""


def generate_rebuttal(topic: str, stance: str, difficulty: str, user_argument: str) -> dict:
    prompt = build_prompt(topic, stance, difficulty, user_argument)

    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "think": False,
                "options": {
                    "num_predict": 120,
                    "temperature": 0.7
                }
            },
            timeout=180.0
        )

        response.raise_for_status()
        data = response.json()

        print("OLLAMA RAW RESPONSE:", data)

        text = extract_text_from_ollama(data)

        if not text:
            return {
                "ok": False,
                "text": "Ollama không trả về nội dung hợp lệ.",
                "error": str(data)
            }

        return {
            "ok": True,
            "text": text,
            "error": ""
        }

    except Exception as e:
        return {
            "ok": False,
            "text": f"Ollama local lỗi: {str(e)}",
            "error": str(e)
        }