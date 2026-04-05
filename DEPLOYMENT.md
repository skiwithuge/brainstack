# Proxmox LXC Deployment Guide

This guide walks you through deploying the Telegram "Second Brain" Bot into a 24/7 standalone Proxmox LXC (Linux Container).

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
| `TELEGRAM_BOT_TOKEN` | *(required)* | Your Telegram bot token |
| `AUTHORIZED_USER_ID` | *(required)* | Your Telegram numeric user ID |
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `WEB_PASSWORD` | `brainstack` | Password for the web viewer |
| `APP_LANGUAGE` | `en` | Language for LLM output (`en` or `it`) |
| `WHISPER_MODEL_SIZE` | `small` | Whisper model size (`tiny`, `small`, `medium`) |

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

