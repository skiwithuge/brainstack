import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from faster_whisper import WhisperModel

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Using int handles empty string properly, but let's safely parse it
auth_id_str = os.getenv("AUTHORIZED_USER_ID", "")
AUTHORIZED_USER_ID = int(auth_id_str) if auth_id_str.isdigit() else 0

NOTES_DIR = os.getenv("NOTES_DIR", "./Notes")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Initialize Whisper Model 
# Using cpu and int8 keeps the memory and compute requirements very low
logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
logger.info("Whisper model loaded successfully.")

def get_daily_folder() -> str:
    """Returns the path to today's folder, creating it if necessary."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(NOTES_DIR, today_str)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return # Ignore unauthorized users silently
        
    await update.message.reply_text(
        "Voice Notes Bot is running! 🎙️\n"
        "Send me any voice message, and I will transcribe it into Italian and save it to today's folder."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming voice messages."""
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized access attempt from user ID {user.id}")
        return

    logger.info("Voice message received.")
    status_message = await update.message.reply_text("Audio received. Transcribing... ⏳")

    # Get the voice file from Telegram servers
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    
    # Download locally temporarily
    temp_audio_path = f"temp_voice_{update.message.message_id}.ogg"
    await voice_file.download_to_drive(temp_audio_path)

    try:
        # Transcribe with faster-whisper
        # Language is forced to "it" based on user preferences.
        # Beam size 5 provides good accuracy.
        segments, info = whisper_model.transcribe(temp_audio_path, language="it", beam_size=5)
        
        transcript = []
        for segment in segments:
            transcript.append(segment.text)
        
        full_text = " ".join(transcript).strip()
        
        if not full_text:
            await status_message.edit_text("❌ Could not transcribe any text from the audio.")
            return

        # Prepare saving the markdown file
        daily_folder = get_daily_folder()
        timestamp_str = datetime.now().strftime("%H_%M_%S")
        filename = f"{timestamp_str}_note.md"
        filepath = os.path.join(daily_folder, filename)

        # Write transcription to the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_text)

        await status_message.edit_text(
            f"✅ **Note saved as** `{filename}`:\n\n_{full_text}_", 
            parse_mode='Markdown'
        )
        logger.info(f"Successfully transcribed and saved {filename}")

    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        await status_message.edit_text("❌ An error occurred during transcription.")
    finally:
        # Cleanup temp audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return
    if not AUTHORIZED_USER_ID:
        logger.error("AUTHORIZED_USER_ID is not set in .env")
        return

    # Ensure base notes directory exists
    os.makedirs(NOTES_DIR, exist_ok=True)

    # Build the application
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Run the bot
    logger.info("Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
