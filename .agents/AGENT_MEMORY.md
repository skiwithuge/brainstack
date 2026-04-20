# Agent Context Memory

This document serves as the persistent memory and "building flow" tracker for autonomous AI agents working within this repository. 
> **Rule Requirement:** For every task completed, the active agent must log an entry in this document detailing the Date, Task Goal, Structural/Architectural Decisions, and any dependencies added.

## Project Origin
- **Initial Setup:** The project started as a dual-script setup (`bot.py` and `summarizer.py`).
- **Refactoring (Current State):** Highly modular agent-safe skeleton with memory system, enforced by `verify.sh`.

## Action Log

### [2026-03-31] Agent-Oriented Project Restructuring Initiation
**Goal:** Transition codebase into a mature, agent-safe skeleton.
**Structural Decisions:**
- Created `.agent_rules.md`. Enforced venv execution. Re-architected into `/src` modules. Adopted `unittest` tests.
**Dependencies:** None.

### [2026-03-31] Second Brain Feature Implementation
**Goal:** Upgrade passive summarizer into multi-persona intelligence engine.
**Structural Decisions:**
- `src/llm/parser.py` with Regex splitting. Strict 4-section system prompt. Parser tests in `verify.sh`.
**Dependencies:** None.

### [2026-04-02] FastAPI Web Viewer Integration
**Goal:** Add password-protected web UI for traversing and editing notes.
**Structural Decisions:**
- `src/web/server.py` with FastAPI + Jinja2. HTTP Basic Auth via `WEB_PASSWORD`. Zero-JS editing.
**Security/State:** Fixed `python-multipart` and `TemplateResponse` bugs.

### [2026-04-02] Open Source Docker Package
**Goal:** One-click Docker deployment for public release.
**Structural Decisions:**
- `Dockerfile` + `docker-compose.yml` with `brainstack-bot` and `brainstack-web` services. `CONTRIBUTING.md` and `README.md` overhauled.
**Security/State:** `.gitignore` and `.dockerignore` lock out `.env` and `Notes/`.

### [2026-04-02] Agent Memory Workflow Enforcement
**Goal:** Protect AI context tracking via formal workflow system.
**Structural Decisions:**
- Created `.agents/` namespace. `update-memory.md` workflow. Removed loose text rules from `.agent_rules.md`.

### [2026-04-02] Internationalization (i18n) Locale Integration
**Goal:** Abstract hardcoded Italian strings for open-source adoption.
**Structural Decisions:**
- `APP_LANGUAGE` env var (default `en`). `src/core/locales.py` mapping dict. Dual-language parser tests.

### [2026-04-02] Docker Compose V2 + Model Fixes
**Goal:** Resolve Docker warnings and API model string issues.
**Structural Decisions:**
- Removed deprecated `version` key from `docker-compose.yml`.
- Reverted `gemini-3-flash` to `gemini-2.5-flash` (API v1beta endpoint not yet available).

### [2026-04-03] Historical Summarizer Processing
**Goal:** Allow reprocessing of past days after an API failure.
**Structural Decisions:**
- `summarizer.py` accepts optional `sys.argv[1]` date string, passed to `run_summarizer(target_date)`.

### [2026-04-05] Memory System — Full Implementation
**Goal:** Build a Karpathy-inspired LLM wiki memory system with tiered periodic reports.
**Structural Decisions:**
- **Raw isolation (A1):** `save_note()` now writes to `Notes/YYYY-MM-DD/raw/`. Glob updated to `raw/*_note.md`.
- **MEMORY_DIR:** `src/core/config.py` adds `MEMORY_DIR = os.path.join(NOTES_DIR, "memory")`. Gitignored by inheritance.
- **wiki_service:** `src/llm/wiki_service.py` — `init_memory()`, `update_from_daily()`, `update_from_weekly()`, `update_from_monthly()`. Guard aborts LLM writes < 50% of original. Log is append-only.
- **Tiered services:** `weekly_service.py`, `monthly_service.py`, `annual_service.py` + CLI entry points `weekly.py`, `monthly.py`, `annual.py` (all accept optional date arg).
- **Proactive nudge:** Weekly run scans `open_loops.md` for items > 7 days old → Telegram notification.
- **Tests added:** `test_wiki_init`, `test_wiki_init_idempotent`, `test_stale_loop_detection`, `test_wiki_guard` — all passing (7/7 total).
**Dependencies:** None new (reuses `google-genai`, `requests`).
**Privacy:** `Notes/memory/` is gitignored — never pushed to GitHub.

### [2026-04-07] Web Interface Redesign & Authentication Upgrade
**Goal:** Transition from basic HTTP auth to session cookie and upgrade dashboard UI.
**Architectural Decisions:** 
- Replaced HTTP Basic Auth with session cookie login.
- Transformed empty `/` dashboard to an active "Working Desk" displaying dynamic memory wiki data (Goals + Open Loops).
- Aggressive LLM prompts for `open_loops` (10 items max, strict single lines) without conversational filler.

### [2026-04-07] LLM Configuration Centralization
**Goal:** Refactor LLM string usage to a central configuration point.
**Architectural Decisions:**
- Handled `LLM_MODEL` inside `src/core/config.py` and mapped environments variables.
- Refactored multiple service orchestrators (weekly, monthly, annual, summarizer, etc.) to use the centralized config.

### [2026-04-07] Tag System and Knowledge Graph
**Goal:** Implement automated, zero-JS tagging for knowledge discovery from daily artifacts to recurring topics analysis.
**Architectural Decisions:**
- Created `src/llm/tag_service.py` with multi-tier logic (LLM based tag extraction, YAML frontmatter injection, frequency indexing via filesystems).
- Two-pass summarization: Extracts tags separately from daily briefing using a focused LLM query to keep the 4-header parser robust.
- Added `/tags` Web UI route and template rendering a tag cloud grouped by occurrences without JavaScript.
- Updated weekly and monthly services to inject tag frequency data directly into the LLM context to power a new "Recurring Topics" analysis.
**Security/State:** Zero-JS philosophy maintained. Used raw regex for YAML parsing to avoid adding new third-party dependencies (like `pyyaml`).

### [2026-04-09] Tagging System Optimization — Quota Removal
**Goal:** Improve tag relevance by removing the forced 3-5 tag quota.
**Architectural Decisions:**
- Updated `src/core/locales.py` prompts for both `en` and `it` to specify "up to 5 highly relevant" tags instead of "exactly 3 to 5".
- Instructed LLM to return nothing if no relevant topics are found, preventing hallucinated tags.
**Security/State:** No changes to file system structure or security guards.
### [2026-04-09] Full Self-Hosted Deployment Documentation
**Goal:** Document the complete self-hosting workflow including local LLM (Ollama) and hidden environment variables.
**Architectural Decisions:**
- Overhauled `DEPLOYMENT.md` to include a "Privacy First" section for local transcription and local LLM.
- Documented Ollama installation and recommended models (`mistral-nemo`, `llama3.1`).
- Expanded Environment Variables table with `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, and `NOTES_DIR`.
- Updated `.env.example` with grouped headers and clearer comments for self-hosting.
**Security/State:** Emphasized the local data privacy of the self-hosted stack.

### Text Message Notes Support
* **Date:** 2026-04-10
* **Goal:** Allow rapid note capture without requiring audio transcription.
* **Design Decisions:** Added a simple text handler to telegram bot that bypasses whisper entirely and links directly to the save_note pipeline.
* **Outcome:** Implemented handle_text checking against authorized id. Added isolated asyncio mocking in tests.

### Merging Open Loops and Goals
* **Date:** 2026-04-20
* **Goal:** Simplify Brainstack layout to reduce actionable noise.
* **Design Decisions:** Deleted separate tracking files for open_loops and goals, consolidating them into an Active Focus schema within focus.md. Strictly limited tracking sizes via prompt injection (max 3 macro goals, max 3 actions per goal).
* **Outcome:** Cleaned up UI mapping context on dashboard.html and successfully rerouted test verification checks to focus logic.
