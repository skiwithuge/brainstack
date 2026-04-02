FROM python:3.11-slim

# Install system dependencies (ffmpeg for audio transcription)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/brainstack

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# We wait for docker-compose to define the ENTRYPOINT since we 
# have two separate apps (bot.py and uvicorn).
