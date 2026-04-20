import os
import logging
import glob
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from src.core.config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, TELEGRAM_FETCH_ENABLED, MEMORY_DIR, validate_bot_config
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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized text attempt from user ID {user.id}")
        return

    full_text = update.message.text
    if not full_text or not full_text.strip():
        return

    logger.info("Text message received.")
    try:
        filename = save_note(full_text.strip())
        await update.message.reply_text(
            f"✅ **Text note saved as** `{filename}`:\n\n_{full_text.strip()}_", 
            parse_mode='Markdown'
        )
        logger.info(f"Successfully saved text note to {filename}")
    except Exception as e:
        logger.error(f"Error saving text note: {e}")
        await update.message.reply_text("❌ An error occurred while saving the text note.")

async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id != AUTHORIZED_USER_ID:
        return
    
    if not TELEGRAM_FETCH_ENABLED:
        await update.message.reply_text("⚠️ Fetch functionality is currently disabled.")
        return

    keyboard = [
        [InlineKeyboardButton("🎯 Active Focus", callback_data="fetch_focus")],
        [InlineKeyboardButton("📅 Latest Daily", callback_data="fetch_latest_daily")],
        [InlineKeyboardButton("📊 Latest Weekly", callback_data="fetch_latest_weekly")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What would you like to retrieve?", reply_markup=reply_markup)

async def fetch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id != AUTHORIZED_USER_ID:
        await query.answer("Unauthorized", show_alert=True)
        return
    
    if not TELEGRAM_FETCH_ENABLED:
        await query.answer("Fetch is disabled", show_alert=True)
        return

    await query.answer()
    
    callback_type = query.data
    target_file = None
    
    if callback_type == "fetch_focus":
        target_file = os.path.join(MEMORY_DIR, "focus.md")
    elif callback_type == "fetch_latest_daily":
        import src.core.config
        notes_dir = src.core.config.NOTES_DIR
        daily_folders = [d for d in os.listdir(notes_dir) if os.path.isdir(os.path.join(notes_dir, d)) and d != "memory"]
        daily_folders.sort(reverse=True)
        for latest in daily_folders:
            temp_path = f"/tmp/{latest}_daily_summary.md"
            with open(temp_path, "w") as out:
                out.write(f"# Daily Summary for {latest}\n\n")
                found_any = False
                for suffix in ["_lineage.md", "_actions.md", "_drafts.md", "_analysis.md", "_Fallback_Briefing.md"]:
                    fpath = os.path.join(notes_dir, latest, f"{latest}{suffix}")
                    if os.path.exists(fpath):
                        with open(fpath, "r") as inf:
                            out.write(inf.read() + "\n\n")
                        found_any = True
                if found_any:
                    target_file = temp_path
                    break
    elif callback_type == "fetch_latest_weekly":
        weekly_files = sorted(glob.glob(os.path.join(MEMORY_DIR, "weekly", "*_report.md")))
        if weekly_files:
            target_file = weekly_files[-1]

    if not target_file or not os.path.exists(target_file):
        await query.message.reply_text("❌ Could not find the requested file. It may not have been generated yet.")
        return

    try:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open(target_file, "rb"),
            caption="Here is your requested document."
        )
    except Exception as e:
        logger.error(f"Error sending document: {e}")
        await query.message.reply_text("❌ Failed to send the document natively.")


async def post_init(application: Application) -> None:
    await application.bot.delete_my_commands()

def run_bot():
    validate_bot_config()
    global transcriber 
    transcriber = AudioTranscriber()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fetch", fetch_command))
    application.add_handler(CallbackQueryHandler(fetch_callback))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
