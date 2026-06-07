from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "firebase").strip().lower()
    AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", STORAGE_PROVIDER).strip().lower()
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "90"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ai_debate_trainer.db"))
    DEFAULT_MAX_TURNS = int(os.getenv("DEFAULT_MAX_TURNS", "5"))
    SPEECH_MAX_AUDIO_BYTES = int(os.getenv("SPEECH_MAX_AUDIO_BYTES", str(8 * 1024 * 1024)))
    SPEECH_TTS_MAX_CHARS = int(os.getenv("SPEECH_TTS_MAX_CHARS", "1200"))

    # Speech-to-Text provider selection. ElevenLabs is primary, Groq is fallback.
    VOICE_STT_PROVIDER = os.getenv("VOICE_STT_PROVIDER", "elevenlabs")
    VOICE_STT_FALLBACK = os.getenv("VOICE_STT_FALLBACK", "groq")

    GROQ_STT_BASE_URL = os.getenv(
        "GROQ_STT_BASE_URL",
        "https://api.groq.com/openai/v1/audio/transcriptions",
    )
    GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")
    GROQ_STT_TIMEOUT_SECONDS = float(os.getenv("GROQ_STT_TIMEOUT_SECONDS", "60"))

    # Edge TTS (Microsoft Edge Text-to-Speech, no API key required)
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "vi-VN-NamMinhNeural")
    EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+10%")

    # ElevenLabs Speech-to-Text provider. Required only when ElevenLabs STT is used.
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_STT_BASE_URL = os.getenv(
        "ELEVENLABS_STT_BASE_URL",
        "https://api.elevenlabs.io/v1/speech-to-text",
    )
    ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")
    ELEVENLABS_STT_TIMEOUT_SECONDS = float(os.getenv("ELEVENLABS_STT_TIMEOUT_SECONDS", "60"))

    # Firebase
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

settings = Settings()
