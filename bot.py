# bot.py
import logging
from src.telegram.bot_service import run_bot

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    run_bot()
