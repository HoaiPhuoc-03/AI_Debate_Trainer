from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:latest")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

settings = Settings()