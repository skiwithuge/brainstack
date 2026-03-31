import os
from datetime import datetime
from src.core.config import NOTES_DIR

def get_daily_folder() -> str:
    """Returns the path to today's folder, creating it if necessary."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(NOTES_DIR, today_str)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_note(full_text: str) -> str:
    """Saves the transcribed note to the daily folder with a timestamped name."""
    daily_folder = get_daily_folder()
    timestamp_str = datetime.now().strftime("%H_%M_%S")
    filename = f"{timestamp_str}_note.md"
    filepath = os.path.join(daily_folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    return filename
