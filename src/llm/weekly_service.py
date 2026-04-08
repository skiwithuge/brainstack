import logging
import glob
import os
from datetime import datetime, timedelta

from src.core.config import GEMINI_API_KEY, NOTES_DIR, MEMORY_DIR, validate_summarizer_config
from src.core.locales import LOCALES
import src.core.config as _cfg
from src.llm.wiki_service import update_from_weekly
from src.llm import tag_service

logger = logging.getLogger(__name__)

from google import genai
import requests
from src.core.config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID


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


def run_weekly_summarizer(target_date: str = None) -> None:
    """
    Generates a weekly summary report from the last 7 days of daily artifacts,
    then triggers a wiki update and proactive stale-loop Telegram nudge.
    """
    validate_summarizer_config()

    if target_date:
        end_date = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()

    # Collect up to 7 days of daily artifact folders
    collected = []
    for offset in range(7):
        day = end_date - timedelta(days=offset)
        day_str = day.strftime("%Y-%m-%d")
        folder = os.path.join(NOTES_DIR, day_str)
        actions_file = os.path.join(folder, f"{day_str}_actions.md")
        lineage_file = os.path.join(folder, f"{day_str}_lineage.md")
        if os.path.exists(actions_file) and os.path.exists(lineage_file):
            collected.append((day_str, actions_file, lineage_file))
        else:
            logger.info(f"weekly_service: no artifacts for {day_str}, skipping")

    if not collected:
        logger.info("weekly_service: no daily artifacts found for this week. Nothing to do.")
        return

    logger.info(f"weekly_service: aggregating {len(collected)} days")

    aggregated = ""
    for day_str, actions_file, lineage_file in sorted(collected):
        with open(lineage_file, "r", encoding="utf-8") as f:
            aggregated += f"\n\n---\n### {day_str} — Lineage\n{f.read().strip()}"
        with open(actions_file, "r", encoding="utf-8") as f:
            aggregated += f"\n\n### {day_str} — Actions\n{f.read().strip()}"

    # Determine week identifier
    week_str = end_date.strftime("%Y-W%W")
    report_dir = os.path.join(MEMORY_DIR, "weekly")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{week_str}_report.md")

    system_prompt = LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])["memory_prompts"]["weekly"]

    # Collect tag frequency for this week's folders
    week_folders = [os.path.join(NOTES_DIR, d) for d, _, _ in collected]
    tag_freq = tag_service.collect_tag_frequency(week_folders)
    if tag_freq:
        tag_summary = ", ".join(f"{tag}: {count}" for tag, count in tag_freq.items())
        aggregated += f"\n\n---\n## Tag Frequency This Week\n{tag_summary}"

    try:
        from src.llm.client import generate_response
        report_md = generate_response(system_prompt, f"Weekly notes ({week_str}):\n{aggregated}", temperature=0.3)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Weekly Report: {week_str}\n\n{report_md}")

        logger.info(f"weekly_service: report saved to {report_path}")
        update_from_weekly(report_path)
        send_telegram_message(f"📅 **Weekly Second Brain report ready!**\nWeek {week_str} processed from {len(collected)} days.")

    except Exception as e:
        logger.error(f"weekly_service: LLM call failed: {e}")
        send_telegram_message("❌ **Weekly consolidation failed!** Check logs.")
