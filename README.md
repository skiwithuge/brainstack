# Telegram Voice Note Consolidator

A personal Telegram bot that transcribes voice notes using a local Whisper model and consolidates them at the end of the day using an LLM API.

## Architecture
- **Receiver Bot:** Listens via Telegram, transcribes locally using `faster-whisper` (optimized for Italian), and writes `.md` notes.
- **Summarizer:** A separate script invoked daily via `cron` to read the notes and create an LLM-powered Markdown summary.

## Setup Instructions

1. **Clone or Rsync this folder** to your homelab.
2. **Install Dependencies:**
   We recommend using a virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configuration:**
   - Copy `.env.example` to `.env`.
   - Add your Telegram Bot Token (from BotFather).
   - Add your numeric Telegram User ID (important for security).
   - Add your Gemini API key for the nightly summary.
4. **Running the Bot:**
   Start the receiver daemon:
   ```bash
   python bot.py
   ```
   *Consider running this using `systemd`, `tmux`, or `supervisor` so it runs continuously in the background.*
5. **Scheduling the Summarizer:**
   Setup a cron job to run the summarizer script every night at 23:59:
   ```bash
   crontab -e
   ```
   Add a line similar to this (adjusting paths to your setup):
   ```cron
   59 23 * * * cd /path/to/project && /path/to/venv/bin/python summarizer.py
   ```
