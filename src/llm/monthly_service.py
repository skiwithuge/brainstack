import logging
import glob
import os
from datetime import datetime

from src.core.config import GEMINI_API_KEY, MEMORY_DIR, TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, validate_summarizer_config
from src.llm.wiki_service import update_from_monthly

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

    system_prompt = (
        "You are an elite personal coach synthesizing a month of weekly reviews into a structured monthly report. "
        "Write a comprehensive monthly report in Markdown covering:\n"
        "## Monthly Summary\n(Key themes, achievements, and milestones)\n\n"
        "## Goals Progress\n(Progress on goals, wins, setbacks)\n\n"
        "## Persistent Patterns\n(Recurring themes across the month)\n\n"
        "## Open Loops\n(Action items still unresolved)\n\n"
        "## Next Month Focus\n(Priorities and intentions for the coming month)\n\n"
        "Be analytical, honest, and constructive."
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Monthly notes ({month_str}):\n{aggregated}",
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )
        report_md = response.text.strip()
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Monthly Report: {month_str}\n\n{report_md}")

        logger.info(f"monthly_service: report saved to {report_path}")
        update_from_monthly(report_path)
        send_telegram_message(f"📆 **Monthly Second Brain report ready!**\n{month_str} processed from {len(weekly_reports)} weekly reports.")

    except Exception as e:
        logger.error(f"monthly_service: LLM call failed: {e}")
        send_telegram_message("❌ **Monthly consolidation failed!** Check logs.")
