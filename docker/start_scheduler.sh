#!/bin/bash
set -e

echo "[scheduler] Installing crontab..."
crontab /opt/brainstack/docker/crontab

echo "[scheduler] Starting cron daemon..."
touch /var/log/brainstack_cron.log

# Run cron in background, tail the log to Docker stdout so
# logs are visible via 'docker compose logs brainstack-scheduler'
cron && tail -f /var/log/brainstack_cron.log
