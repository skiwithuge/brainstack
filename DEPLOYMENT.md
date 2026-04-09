# Proxmox LXC Deployment Guide

This guide covers two deployment methods: **Docker Compose** (recommended, self-contained) and a **bare-metal Proxmox LXC** setup.

---

## 🐳 Docker Compose Deployment (Recommended)

This is the simplest and most portable way to run Brainstack. All three services run as isolated containers with no impact on the host machine.

### Services

| Container | Role |
|---|---|
| `brainstack-bot` | Telegram bot — records and transcribes voice notes 24/7 |
| `brainstack-web` | Web viewer — browse and edit notes via browser |
| `brainstack-scheduler` | Cron daemon — runs daily/weekly/monthly/annual processing |

### Quick Start

```bash
# 1. Clone and enter the repo
git clone <YOUR_REPO_URL> brainstack && cd brainstack

# 2. Configure your environment
cp .env.example .env
nano .env   # Fill in TELEGRAM_BOT_TOKEN, AUTHORIZED_USER_ID, GEMINI_API_KEY

# 3. Build and start all containers
docker compose up -d

# 4. Verify all three containers are running
docker compose ps
```

### Monitoring Docker Logs

```bash
# Live logs from all services
docker compose logs -f

# Scheduler cron output only
docker compose logs -f brainstack-scheduler

# Bot activity only
docker compose logs -f brainstack-bot
```

### Manual Reprocessing (Docker)

```bash
# Reprocess a specific day
docker exec brainstack_scheduler python summarizer.py 2026-04-02

# Trigger weekly report manually
docker exec brainstack_scheduler python weekly.py

# Trigger monthly report manually
docker exec brainstack_scheduler python monthly.py
```

### Cron Schedule (UTC)

The `brainstack-scheduler` container runs all jobs automatically:

| Job | Schedule |
|---|---|
| Daily summary | 11:59 PM every night |
| Weekly report + memory wiki | 11:00 PM every Sunday |
| Monthly report + memory wiki | 10:00 PM on the 1st |
| Annual report + memory wiki | 9:00 PM on January 1st |

To customise the schedule, edit `docker/crontab` and rebuild: `docker compose build brainstack-scheduler`.

---

## 🏗️ Service Architecture

Brainstack consists of three distinct modules that work together:

1.  **The Bot (`bot.py`)**: A permanent background listener that records voice notes and handles immediate transcription via `faster-whisper`.
2.  **The Web Viewer (`src.web.server`)**: A FastAPI interface for browsing and editing your notes.
3.  **The Scheduler (`summarizer.py`, `weekly.py`, etc.)**: A set of processing jobs that run periodically to analyze your data and build the memory index.


## 🖥️ Proxmox LXC Deployment (Bare Metal)

## 1. Create the Container in Proxmox
1. Open your Proxmox Web GUI.
2. Click **Create CT** (Container).
3. **General:** Uncheck "Unprivileged container" ONLY if you intend to bind-mount an external NAS drive with strict UID mappings later. Otherwise, leave it **Unprivileged** (Recommended).
4. **Template:** Select an `Ubuntu 22.04` or `Debian 12` template.
5. **Disk:** 4GB - 8GB is plenty.
6. **CPU:** 2 vCores is recommended for brief `faster-whisper` transcription spikes.
7. **Memory:** 1024MB - 2048MB.
8. **Network:** Assign a static IP or use DHCP.

## 2. Install the Application
Once the container is running, open its **Console** in Proxmox and log in as `root`.

Run the following commands to install the bot into `/opt/brainstack`:

```bash
# 1. Clone the repository
git clone <URL_TO_YOUR_REPO> /opt/brainstack

# 2. Enter the folder
cd /opt/brainstack

# 3. Make the setup script executable and run it
chmod +x scripts/setup_lxc.sh
./scripts/setup_lxc.sh
```

The script will automatically install `ffmpeg`, Python 3, create the isolated `venv`, install PIP dependencies, and configure the `systemd` daemon!

## 3. Configuration & Startup
After the script finishes, you need to add your API keys.

```bash
cd /opt/brainstack
cp .env.example .env
nano .env
```
*(Paste your `TELEGRAM_BOT_TOKEN`, `AUTHORIZED_USER_ID`, and `GEMINI_API_KEY` in nano, then press `CTRL+X`, `Y`, `Enter` to save).*

### Start the Bot Daemon
The `setup_lxc.sh` script installed a systemd service. To start the bot running forever in the background:
```bash
systemctl start brainstack
```

To see the live bot logs and ensure it is working:
```bash
journalctl -fu brainstack
```

## 4. Configuration Options

Before starting, review your `.env` file — key options:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | *(required)* | Your Telegram bot token from @BotFather |
| `AUTHORIZED_USER_ID` | *(required)* | Your numeric User ID to lock the bot to your account |
| `LLM_PROVIDER` | `gemini` | `gemini` (Cloud) or `ollama` (Local) |
| `LLM_MODEL` | `gemini-2.5-flash` | LLM model tag (e.g., `mistral-nemo`, `llama3.1:8b`) |
| `LLM_BASE_URL` | `http://localhost:11434/api/generate` | Local Ollama endpoint |
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key (optional if using Ollama) |
| `NOTES_DIR` | `./Notes` | Where your raw audio and summaries are saved |
| `WHISPER_MODEL_SIZE` | `small` | Transcription quality (`tiny`, `small`, `medium`) |
| `WEB_PASSWORD` | `brainstack` | Password for the browser dashboard |
| `APP_LANGUAGE` | `en` | Language for LLM analysis (`en` or `it`) |

---

## 🛡️ Privacy First: Full Self-Hosted Workflow

Brainstack is designed to run entirely on your own hardware without sending a single byte of content to the cloud. This requires two components to be local: **Transcription (Whisper)** and **Analysis (Ollama)**.

### 1. Local Transcription (Whisper)
By default, Brainstack uses `faster-whisper` locally. 
*   **Hardware Requirement:** 2+ CPU cores. 
*   **Recommendation:** Set `WHISPER_MODEL_SIZE="large-v3"` in your `.env` for significantly better accuracy in Italian or complex English, if you have at least 8GB of RAM.

### 2. Local LLM (Ollama Installation)
If you don't want to use Google Gemini, you can use **Ollama**.

**Installation (Linux/LXC):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Pull the recommended models:**
For Brainstack's analytical tasks (on a light hardware pc), we recommend `mistral-nemo` (12B) or `llama3.1` (8B).
```bash
ollama pull mistral-nemo
ollama pull llama3.1
```

### 3. Connection
Update your `.env` to point to your Ollama instance:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=mistral-nemo
LLM_BASE_URL=http://localhost:11434/api/generate
```

*Note: If Ollama is running in a different LXC or VM, change `localhost` to its static IP.*

---

## 5. Schedule All Automated Jobs

The bot records 24/7. Use `cron` to schedule all automated processing jobs.

Open the cron editor:
```bash
crontab -e
```

Paste these lines at the bottom:

```bash
# Daily Second Brain — runs at 11:59 PM every night
59 23 * * * cd /opt/brainstack && /opt/brainstack/venv/bin/python summarizer.py >> /var/log/brainstack_cron.log 2>&1

# Weekly Memory Report — runs at 11:00 PM every Sunday
0 23 * * 0 cd /opt/brainstack && /opt/brainstack/venv/bin/python weekly.py >> /var/log/brainstack_cron.log 2>&1

# Monthly Memory Report — runs at 10:00 PM on the 1st of each month
0 22 1 * * cd /opt/brainstack && /opt/brainstack/venv/bin/python monthly.py >> /var/log/brainstack_cron.log 2>&1

# Annual Memory Report — runs at 9:00 PM on January 1st
0 21 1 1 * cd /opt/brainstack && /opt/brainstack/venv/bin/python annual.py >> /var/log/brainstack_cron.log 2>&1
```

Save and exit.

## 6. Memory System

Brainstack maintains a **private living wiki** at `Notes/memory/` that compounds your self-knowledge over time. This folder is **never pushed to GitHub** — it stays on your server only.

It contains:
- `open_loops.md` — unresolved action items tracked with dates
- `goals.md` — your evolving goals (updated weekly)
- `patterns.md` — recurring thinking themes (updated weekly)
- `log.md` — append-only audit trail of all memory operations

### Manual Reprocessing

If a scheduled job fails, you can reprocess any past date manually:

```bash
cd /opt/brainstack

# Reprocess a specific day
/opt/brainstack/venv/bin/python summarizer.py 2026-04-02

# Reprocess a specific week (pass the Sunday date)
/opt/brainstack/venv/bin/python weekly.py 2026-04-06

# Reprocess a specific month (pass any date in that month)
/opt/brainstack/venv/bin/python monthly.py 2026-04-01
```

### Monitoring

```bash
# Watch live cron output
tail -f /var/log/brainstack_cron.log

# Check bot daemon status
journalctl -fu brainstack

# Check web viewer status
journalctl -fu brainstack-web
```

**You are fully deployed! Your Homelab is now your Second Brain.**

