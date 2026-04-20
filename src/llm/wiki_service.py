import os
import logging
from datetime import datetime, timedelta
from google import genai

from src.core.config import GEMINI_API_KEY, MEMORY_DIR, TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID
from src.core.locales import LOCALES
import src.core.config as _cfg

import requests

logger = logging.getLogger(__name__)

# --- Wiki page templates ---
_TEMPLATES = {
    "index.md": (
        "---\nlast_updated: {date}\n---\n\n# Memory Index\n\n"
        "| Page | Description |\n|---|---|\n"
        "| [focus.md](focus.md) | Active focus goals and next actions |\n"
        "| [patterns.md](patterns.md) | Recurring themes and thinking habits |\n"
        "| [log.md](log.md) | Append-only chronological audit trail |\n"
    ),
    "focus.md": (
        "---\nlast_updated: {date}\n---\n\n# Active Focus\n\n"
        "*No active focus recorded yet. Will be populated on the first weekly run or daily summary.*\n"
    ),
    "patterns.md": (
        "---\nlast_updated: {date}\n---\n\n# Patterns\n\n"
        "*No patterns identified yet. Will be populated on the first weekly run.*\n"
    ),
    "log.md": (
        "# Log\n\n"
        "Append-only chronological record of all memory operations.\n\n"
    ),
}


def init_memory() -> None:
    """Ensures Notes/memory/ and all wiki pages exist. Creates from template if missing."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    for subdir in ("weekly", "monthly", "annual"):
        os.makedirs(os.path.join(MEMORY_DIR, subdir), exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    for filename, template in _TEMPLATES.items():
        page_path = os.path.join(MEMORY_DIR, filename)
        if not os.path.exists(page_path):
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(template.format(date=today))
            logger.info(f"Memory wiki: created {filename}")


def _read_page(filename: str) -> str:
    page_path = os.path.join(MEMORY_DIR, filename)
    if not os.path.exists(page_path):
        return ""
    with open(page_path, "r", encoding="utf-8") as f:
        return f.read()


def _write_page(filename: str, content: str, original: str) -> bool:
    """Writes updated wiki page. Guard: aborts if new content < 50% of original."""
    if original and len(content) < len(original) * 0.5:
        logger.warning(
            f"Wiki guard triggered for {filename}: response ({len(content)} chars) "
            f"< 50% of original ({len(original)} chars). Aborting update."
        )
        return False
    page_path = os.path.join(MEMORY_DIR, filename)
    today = datetime.now().strftime("%Y-%m-%d")
    # Update frontmatter date if present
    if content.startswith("---"):
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("last_updated:"):
                lines[i] = f"last_updated: {today}"
                break
        content = "\n".join(lines)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def _append_log(entry: str) -> None:
    log_path = os.path.join(MEMORY_DIR, "log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def _call_llm(system_prompt: str, user_content: str) -> str | None:
    from src.llm.client import generate_response
    try:
        updated_markdown = generate_response(system_prompt, user_content, temperature=0.3)
        return updated_markdown.strip()
    except Exception as e:
        logger.error(f"Wiki LLM call failed: {e}")
        return None


def update_from_daily(actions_path: str) -> None:
    """Updates focus.md from today's actions file. Called after daily summarizer."""
    init_memory()

    if not os.path.exists(actions_path):
        logger.warning(f"wiki_service: actions file not found at {actions_path}")
        return

    with open(actions_path, "r", encoding="utf-8") as f:
        actions_content = f.read()

    current_focus = _read_page("focus.md")
    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])["memory_prompts"]["focus"]
    user_content = (
        f"## Current Active Focus Page\n\n{current_focus}\n\n"
        f"## Today's ({today}) Action Items\n\n{actions_content}"
    )

    updated = _call_llm(system_prompt, user_content)
    if updated:
        wrote = _write_page("focus.md", updated, current_focus)
        status = "updated" if wrote else "guard_aborted"
    else:
        status = "llm_failed"

    _append_log(f"## [{today}] daily | focus {status}")
    logger.info(f"wiki_service daily update: focus {status}")


def _update_wiki_pages(report_content: str, tier: str) -> dict:
    """Updates goals, patterns, and open_loops from a weekly/monthly report."""
    today = datetime.now().strftime("%Y-%m-%d")
    results = {}

    pages_to_update = {
        "focus.md": LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])["memory_prompts"]["focus"],
        "patterns.md": LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])["memory_prompts"]["patterns"],
    }

    for filename, system_prompt in pages_to_update.items():
        current = _read_page(filename)
        user_content = f"## Current Page\n\n{current}\n\n## {tier.capitalize()} Report\n\n{report_content}"
        updated = _call_llm(system_prompt, user_content)
        if updated:
            wrote = _write_page(filename, updated, current)
            results[filename] = "updated" if wrote else "guard_aborted"
        else:
            results[filename] = "llm_failed"

    return results


def update_from_weekly(report_path: str) -> None:
    """Updates all wiki pages from a weekly report. Also fires stale loop nudge."""
    init_memory()
    today = datetime.now().strftime("%Y-%m-%d")

    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    results = _update_wiki_pages(report_content, "weekly")
    summary = ", ".join(f"{k.split('.')[0]} {v}" for k, v in results.items())
    _append_log(f"## [{today}] weekly | {summary}")
    logger.info(f"wiki_service weekly update: {summary}")

    _send_stale_loop_nudge()


def update_from_monthly(report_path: str) -> None:
    """Updates all wiki pages from a monthly report."""
    init_memory()
    today = datetime.now().strftime("%Y-%m-%d")

    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    results = _update_wiki_pages(report_content, "monthly")
    summary = ", ".join(f"{k.split('.')[0]} {v}" for k, v in results.items())
    _append_log(f"## [{today}] monthly | {summary}")
    logger.info(f"wiki_service monthly update: {summary}")


def _send_stale_loop_nudge() -> None:
    """Reads open_loops.md and sends a Telegram nudge for items older than 7 days."""
    if not TELEGRAM_BOT_TOKEN or not AUTHORIZED_USER_ID:
        return

    focus_content = _read_page("focus.md")
    if not focus_content:
        return

    threshold = datetime.now() - timedelta(days=7)
    stale_items = []

    for line in focus_content.splitlines():
        # Match lines like: - [YYYY-MM-DD] item text
        if line.strip().startswith("- [") and not "[CLOSED" in line:
            try:
                date_str = line.strip()[3:13]
                item_date = datetime.strptime(date_str, "%Y-%m-%d")
                if item_date < threshold:
                    item_text = line.strip()[16:].strip()
                    stale_items.append(f"• ({date_str}) {item_text}")
            except (ValueError, IndexError):
                continue

    if not stale_items:
        return

    message = (
        f"⚠️ *Active Focus Reminder* — {len(stale_items)} action(s) have been open for over 7 days:\n\n"
        + "\n".join(stale_items[:10])  # cap at 10 to avoid Telegram message length limits
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": AUTHORIZED_USER_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        logger.info(f"Stale focus nudge sent: {len(stale_items)} items")
    except Exception as e:
        logger.error(f"Failed to send stale loop nudge: {e}")


def get_stale_loops(threshold_days: int = 7) -> list[str]:
    """Returns list of stale focus action lines (for testing)."""
    focus_content = _read_page("focus.md")
    threshold = datetime.now() - timedelta(days=threshold_days)
    stale = []
    for line in focus_content.splitlines():
        if line.strip().startswith("- [") and "[CLOSED" not in line:
            try:
                date_str = line.strip()[3:13]
                if datetime.strptime(date_str, "%Y-%m-%d") < threshold:
                    stale.append(line.strip())
            except (ValueError, IndexError):
                continue
    return stale
