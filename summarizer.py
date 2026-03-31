import os
import glob
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTES_DIR = os.getenv("NOTES_DIR", "./Notes")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_USER_ID")

def send_telegram_message(message: str):
    """Send a notification back to the user via Telegram."""
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

def main():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set in .env. Exiting.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(NOTES_DIR, today_str)

    if not os.path.exists(folder_path):
        logger.info(f"No folder found for today ({today_str}). Nothing to summarize.")
        return

    # Find all note files in chronological order
    search_pattern = os.path.join(folder_path, "*_note.md")
    note_files = sorted(glob.glob(search_pattern))

    if not note_files:
        logger.info(f"No note files found in today's folder ({today_str}). Nothing to summarize.")
        return

    logger.info(f"Found {len(note_files)} notes to summarize.")

    # Aggregate notes
    aggregated_text = f"Voice Notes for {today_str}:\n\n"
    for filepath in note_files:
        filename = os.path.basename(filepath)
        # Extract time part from HH_MM_SS_note.md
        time_part = filename.split("_note.md")[0].replace("_", ":")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            aggregated_text += f"### Note at {time_part}\n{content}\n\n"

    logger.info("Calling LLM API for consolidation...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_prompt = (
        "You are an intelligent assistant that consolidates daily voice notes into a clear, "
        "well-organized Markdown summary. Extract key action items, group related thoughts, "
        "and provide a coherent narrative of the day while preserving important details. "
        "Respond only with the Markdown content."
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
        
        # Save summary
        summary_filename = f"{today_str}_Summary.md"
        summary_filepath = os.path.join(folder_path, summary_filename)
        
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary_markdown)
            
        logger.info(f"Successfully generated and saved {summary_filename}")
        
        # Notify the user that the summary is ready
        send_telegram_message(f"✅ **Daily consolidation complete!**\nSummary saved to `{summary_filename}`.")

    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        send_telegram_message("❌ **Daily consolidation failed!**\nCheck the summarizer script logs.")

if __name__ == "__main__":
    main()
