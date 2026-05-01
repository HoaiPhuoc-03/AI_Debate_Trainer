import sys

from app.core.config import settings
from app.services.ai_service import generate_rebuttal


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    result = generate_rebuttal(
        topic="Sinh viên có nên đi làm thêm năm nhất?",
        stance="support",
        difficulty="intermediate",
        user_argument="Tôi nghĩ sinh viên không nên đi làm thêm năm nhất vì ảnh hưởng việc học.",
        age_group="adult",
        debate_level="intermediate",
        input_mode="text",
        language="vi",
    )
    print("provider:", result.get("provider") or "groq")
    print("model:", result.get("model") or settings.GROQ_MODEL)
    print("ok:", result.get("ok"))
    print("text:")
    print(result.get("text", ""))
    if result.get("error"):
        print("error:", result["error"])


if __name__ == "__main__":
    main()
