<div align="center">
  <img src="docs/architecture.png" alt="Brainstack Architecture" width="800"/>
  <h1>🧠 Brainstack</h1>
  <p><strong>Your Self-Hosted AI Second Brain</strong></p>
</div>

## 🌟 What is Brainstack?
Brainstack is a personal, fully self-hosted Telegram bot that records your unstructured audio thoughts, transcribes them using local `faster-whisper`, and meticulously organizes them into a daily Markdown journal using `google-genai`. It includes a built-in FastAPI web viewer to securely traverse and edit your digital mind.

## 🚀 Quick Start (Docker)

Deploying Brainstack to your homelab is natively supported via Docker Compose.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/brainstack.git
   cd brainstack
   ```
2. **Configure your Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram token, Gemini API key, and Web Password
   ```
3. **Launch the Stack:**
   ```bash
   docker-compose up -d
   ```

*The bot will immediately start listening on your private Telegram channel, and your web viewer will be running securely at `http://localhost:8000`.*

---

## 🏗️ Architecture Design
Brainstack strictly follows a microservice philosophy:
- **`brainstack-bot`**: Listens to Telegram audio, transcribes it cleanly, and prompts Gemini to categorize your thoughts into 4 distinct phases (Lineage, Actions, Content Drafts, Psychologist Analysis). 
- **`brainstack-web`**: A lightweight FastAPI wrapper serving pure HTML templates, meaning there is zero Javascript bloat when managing your Markdown strings.

Personal Notes and Environment configurations are strictly `.dockerignore`'d and `.gitignore`'d to maintain complete data supremacy. 

## 🤝 Contributing
Open-source contributions are welcome! To maintain the strict deterministic logic of the parser, please read [CONTRIBUTING.md](CONTRIBUTING.md) for information on using the mandated `./scripts/verify.sh` test suite before filing Pull Requests.
