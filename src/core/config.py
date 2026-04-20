import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
auth_id_str = os.getenv("AUTHORIZED_USER_ID", "")
AUTHORIZED_USER_ID = int(auth_id_str) if auth_id_str.isdigit() else 0
TELEGRAM_FETCH_ENABLED = os.getenv("TELEGRAM_FETCH_ENABLED", "true").lower() in ("true", "1", "yes", "on")

NOTES_DIR = os.getenv("NOTES_DIR", "./Notes")
MEMORY_DIR = os.path.join(NOTES_DIR, "memory")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

# ── LLM Configuration ────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/api/generate")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

WEB_PASSWORD = os.getenv("WEB_PASSWORD", "brainstack")
APP_LANGUAGE = os.getenv("APP_LANGUAGE", "en")

def validate_bot_config():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not AUTHORIZED_USER_ID:
        raise ValueError("AUTHORIZED_USER_ID is not set in .env")

def validate_summarizer_config():
    if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env file, but LLM_PROVIDER is set to gemini.")
