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


def run_annual_summarizer(target_date: str = None) -> None:
    """
    Generates an annual summary report from all monthly reports in the target year,
    then triggers a wiki update.
    """
    validate_summarizer_config()

    if target_date:
        ref_date = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        ref_date = datetime.now()

    year_str = ref_date.strftime("%Y")

    monthly_dir = os.path.join(MEMORY_DIR, "monthly")
    monthly_reports = sorted(glob.glob(os.path.join(monthly_dir, f"{year_str}-*_report.md")))

    if not monthly_reports:
        logger.info(f"annual_service: no monthly reports found for {year_str}. Nothing to do.")
        return

    logger.info(f"annual_service: aggregating {len(monthly_reports)} monthly reports")

    aggregated = ""
    for report_path in monthly_reports:
        with open(report_path, "r", encoding="utf-8") as f:
            aggregated += f"\n\n---\n{f.read().strip()}"

    report_dir = os.path.join(MEMORY_DIR, "annual")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{year_str}_report.md")

    system_prompt = (
        "You are an elite personal coach synthesizing a full year of monthly reviews. "
        "Write a comprehensive annual report in Markdown covering:\n"
        "## Year in Review\n(The arc of the year — major themes, turning points)\n\n"
        "## Achievements\n(What was accomplished this year)\n\n"
        "## Unfinished Business\n(Open loops and unresolved intentions)\n\n"
        "## Growth & Patterns\n(How thinking and priorities evolved)\n\n"
        "## Letter to Next Year\n(Honest advice and intentions for the year ahead)\n\n"
        "Write with depth, honesty, and long-term perspective."
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Annual notes ({year_str}):\n{aggregated}",
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.4
            )
        )
        report_md = response.text.strip()
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Annual Report: {year_str}\n\n{report_md}")

        logger.info(f"annual_service: report saved to {report_path}")
        update_from_monthly(report_path)
        send_telegram_message(f"🗓️ **Annual Second Brain report ready!**\n{year_str} processed from {len(monthly_reports)} monthly reports.")

    except Exception as e:
        logger.error(f"annual_service: LLM call failed: {e}")
        send_telegram_message("❌ **Annual consolidation failed!** Check logs.")
