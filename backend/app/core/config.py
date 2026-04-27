from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:latest")
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ai_debate_trainer.db"))
    DEFAULT_MAX_TURNS = int(os.getenv("DEFAULT_MAX_TURNS", "5"))

settings = Settings()
