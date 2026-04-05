import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
auth_id_str = os.getenv("AUTHORIZED_USER_ID", "")
AUTHORIZED_USER_ID = int(auth_id_str) if auth_id_str.isdigit() else 0

NOTES_DIR = os.getenv("NOTES_DIR", "./Notes")
MEMORY_DIR = os.path.join(NOTES_DIR, "memory")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "brainstack")
APP_LANGUAGE = os.getenv("APP_LANGUAGE", "en")

def validate_bot_config():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not AUTHORIZED_USER_ID:
        raise ValueError("AUTHORIZED_USER_ID is not set in .env")

def validate_summarizer_config():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")
