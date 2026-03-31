import os
import glob
import logging
from datetime import datetime
import requests
from google import genai

from src.core.config import GEMINI_API_KEY, NOTES_DIR, TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, validate_summarizer_config
from src.llm.parser import split_and_save_briefing

logger = logging.getLogger(__name__)

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not AUTHORIZED_USER_ID:
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": AUTHORIZED_USER_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")

def run_summarizer():
    validate_summarizer_config()
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(NOTES_DIR, today_str)

    if not os.path.exists(folder_path):
        logger.info(f"No folder found for today ({today_str}). Nothing to summarize.")
        return

    search_pattern = os.path.join(folder_path, "*_note.md")
    note_files = sorted(glob.glob(search_pattern))

    if not note_files:
        logger.info(f"No note files found in today's folder ({today_str}). Nothing to summarize.")
        return

    logger.info(f"Found {len(note_files)} notes to summarize.")
    aggregated_text = f"Voice Notes for {today_str}:\n\n"
    for filepath in note_files:
        filename = os.path.basename(filepath)
        time_part = filename.split("_note.md")[0].replace("_", ":")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            aggregated_text += f"### Note at {time_part}\n{content}\n\n"

    logger.info("Calling LLM API for consolidation...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_prompt = (
        "You are an elite 'Second Brain' intelligent assistant analyzing a user's daily voice notes. "
        "You MUST output your response in EXACTLY four sections, starting with these exact headers:\n"
        "## 1. Lineage\n"
        "(Summarize the raw thoughts chronologically so context is never lost.)\n\n"
        "## 2. Actions\n"
        "(Extract concrete action items, to-do lists, and strategize the execution of any projects mentioned.)\n\n"
        "## 3. Creative Drafts\n"
        "(Take any creative, philosophical, or abstract thoughts and write fully-formed Twitter threads or blog post drafts.)\n\n"
        "## 4. Analyst Assessment\n"
        "(Act as a psychologist and Devil's Advocate. Connect patterns in their thinking, point out blind spots, and challenge their assumptions.)\n\n"
        "Do NOT output any other top-level headers. You MUST strictly follow this Markdown structure."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=aggregated_text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )
        
        summary_markdown = response.text.strip()
        
        saved_files = split_and_save_briefing(summary_markdown, folder_path, today_str)
        
        logger.info(f"Successfully generated and saved {len(saved_files)} files.")
        
        if len(saved_files) == 4:
            send_telegram_message(f"✅ **Daily Second Brain processing complete!**\nSeparated into Lineage, Actions, Drafts, and Analysis.")
        else:
            send_telegram_message(f"⚠️ **Daily processing complete!**\nFallback briefing triggered (hallucinated headers).")

    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        send_telegram_message("❌ **Daily consolidation failed!**\nCheck the summarizer script logs.")
