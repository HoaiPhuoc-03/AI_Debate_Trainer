from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "90"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ai_debate_trainer.db"))
    DEFAULT_MAX_TURNS = int(os.getenv("DEFAULT_MAX_TURNS", "5"))

settings = Settings()
