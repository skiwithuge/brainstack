import os
from datetime import datetime
from src.core.config import NOTES_DIR

def get_daily_folder() -> str:
    """Returns the path to today's folder, creating it if necessary."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(NOTES_DIR, today_str)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_raw_folder(daily_folder: str = None) -> str:
    """Returns the path to the raw/ subfolder inside today's daily folder."""
    if daily_folder is None:
        daily_folder = get_daily_folder()
    raw_folder = os.path.join(daily_folder, "raw")
    os.makedirs(raw_folder, exist_ok=True)
    return raw_folder

def save_note(full_text: str) -> str:
    """Saves the transcribed note to the raw/ subfolder with a timestamped name."""
    raw_folder = get_raw_folder()
    timestamp_str = datetime.now().strftime("%H_%M_%S")
    filename = f"{timestamp_str}_note.md"
    filepath = os.path.join(raw_folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)

    return filename
