#!/usr/bin/env bash
# Proxmox LXC Setup Script for Brainstack (Ubuntu/Debian)
# Run this as root inside your fresh LXC.

set -e

echo "📦 1. Installing System Dependencies (ffmpeg, python, git)..."
apt-get update
apt-get install -y python3 python3-venv python3-pip git ffmpeg curl nano

WORKDIR="/opt/brainstack"

echo "📂 2. Checking repository location..."
if [ ! -d "$WORKDIR" ]; then
    echo "⚠️  Repository not found at $WORKDIR."
    echo "Please run: git clone <your-repo-url> /opt/brainstack"
    echo "Then re-run this script."
    exit 1
fi

cd "$WORKDIR"

echo "🐍 3. Creating Virtual Environment and installing Python packages..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "⚙️  4. Installing Systemd Daemon..."
if [ -f "scripts/brainstack.service" ]; then
    # Setup Systemd Services
    echo "Configuring background services..."
    cp /opt/brainstack/scripts/brainstack.service /etc/systemd/system/
    cp /opt/brainstack/scripts/brainstack-web.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable brainstack.service
    systemctl enable brainstack-web.service
    systemctl start brainstack.service
    systemctl start brainstack-web.service

    echo "✅ Systemd services installed and enabled!"
else
    echo "⚠️  scripts/brainstack.service not found. Skipping daemon install."
fi

echo "=========================================================="
echo "🎉 Setup Complete!"
echo "- Telegram bot is running as a daemon."
echo "- Web Viewer is running on port 8000."
echo ""
echo "Next Steps:"
echo "1. Create your environment file: cp .env.example .env"
echo "2. Edit your keys: nano .env"
echo "3. Start the bot: systemctl start brainstack"
echo "4. Check logs: journalctl -fu brainstack"
echo ""
echo "To schedule the nightly summarizer, run 'crontab -e' and add:"
echo "59 23 * * * cd /opt/brainstack && /opt/brainstack/venv/bin/python summarizer.py >> /var/log/brainstack_cron.log 2>&1"
echo "=========================================================="
