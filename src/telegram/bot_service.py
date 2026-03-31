import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.core.config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, validate_bot_config
from src.audio.transcriber import AudioTranscriber
from src.storage.notes import save_note

logger = logging.getLogger(__name__)

# Lazy initialization via global variable setup inside runtime
transcriber = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    await update.message.reply_text(
        "Voice Notes Bot is running! 🎙️\n"
        "Send me any voice message, and I will transcribe it into Italian and save it to today's folder."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized access attempt from user ID {user.id}")
        return

    logger.info("Voice message received.")
    status_message = await update.message.reply_text("Audio received. Transcribing... ⏳")

    voice_file = await context.bot.get_file(update.message.voice.file_id)
    temp_audio_path = f"temp_voice_{update.message.message_id}.ogg"
    await voice_file.download_to_drive(temp_audio_path)

    try:
        full_text = transcriber.transcribe(temp_audio_path)
        if not full_text:
            await status_message.edit_text("❌ Could not transcribe any text from the audio.")
            return

        filename = save_note(full_text)
        await status_message.edit_text(
            f"✅ **Note saved as** `{filename}`:\n\n_{full_text}_", 
            parse_mode='Markdown'
        )
        logger.info(f"Successfully transcribed and saved {filename}")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        await status_message.edit_text("❌ An error occurred during transcription.")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

def run_bot():
    validate_bot_config()
    global transcriber 
    transcriber = AudioTranscriber()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
