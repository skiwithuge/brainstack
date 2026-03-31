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

## 4. Schedule the Nightly "Second Brain" Summarizer
The bot is now recording and transcribing locally 24/7. Now we need to tell the server to run the Gemini analysis automatically every night just before midnight.

1. Open the cron editor:
```bash
crontab -e
```
2. Paste this exact line at the very bottom of the file to run the script at 11:59 PM every night:
```bash
59 23 * * * cd /opt/brainstack && /opt/brainstack/venv/bin/python summarizer.py >> /var/log/brainstack_cron.log 2>&1
```
3. Save and exit.

**You are fully deployed! Your Homelab is now your Second Brain.**
