import logging
import glob
import os
from datetime import datetime

from src.core.config import GEMINI_API_KEY, MEMORY_DIR, NOTES_DIR, TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, validate_summarizer_config
from src.core.locales import LOCALES
import src.core.config as _cfg
from src.llm.wiki_service import update_from_monthly
from src.llm import tag_service

logger = logging.getLogger(__name__)

from google import genai
import requests


def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not AUTHORIZED_USER_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": AUTHORIZED_USER_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


def run_monthly_summarizer(target_date: str = None) -> None:
    """
    Generates a monthly summary report from available weekly reports,
    then triggers a wiki update.
    """
    validate_summarizer_config()

    if target_date:
        ref_date = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        ref_date = datetime.now()

    month_str = ref_date.strftime("%Y-%m")
    year_str = ref_date.strftime("%Y")

    weekly_dir = os.path.join(MEMORY_DIR, "weekly")
    weekly_reports = sorted(glob.glob(os.path.join(weekly_dir, f"{year_str}-W*_report.md")))

    if not weekly_reports:
        logger.info(f"monthly_service: no weekly reports found for {year_str}. Nothing to do.")
        return

    logger.info(f"monthly_service: aggregating {len(weekly_reports)} weekly reports")

    aggregated = ""
    for report_path in weekly_reports:
        with open(report_path, "r", encoding="utf-8") as f:
            aggregated += f"\n\n---\n{f.read().strip()}"

    report_dir = os.path.join(MEMORY_DIR, "monthly")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{month_str}_report.md")

    system_prompt = LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])["memory_prompts"]["monthly"]

    # Collect tag frequency for this month's daily folders
    month_folders = []
    if os.path.exists(NOTES_DIR):
        for entry in os.listdir(NOTES_DIR):
            if entry.startswith(month_str) and os.path.isdir(os.path.join(NOTES_DIR, entry)):
                month_folders.append(os.path.join(NOTES_DIR, entry))
    tag_freq = tag_service.collect_tag_frequency(month_folders)
    if tag_freq:
        tag_summary = ", ".join(f"{tag}: {count}" for tag, count in tag_freq.items())
        aggregated += f"\n\n---\n## Tag Frequency This Month\n{tag_summary}"

    try:
        from src.llm.client import generate_response
        report_md = generate_response(system_prompt, f"Monthly notes ({month_str}):\n{aggregated}", temperature=0.3)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Monthly Report: {month_str}\n\n{report_md}")

        logger.info(f"monthly_service: report saved to {report_path}")
        update_from_monthly(report_path)
        send_telegram_message(f"📆 **Monthly Second Brain report ready!**\n{month_str} processed from {len(weekly_reports)} weekly reports.")

    except Exception as e:
        logger.error(f"monthly_service: LLM call failed: {e}")
        send_telegram_message("❌ **Monthly consolidation failed!** Check logs.")
