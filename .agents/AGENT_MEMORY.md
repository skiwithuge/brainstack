# Agent Context Memory

This document serves as the persistent memory and "building flow" tracker for autonomous AI agents working within this repository. 
> **Rule Requirement:** For every task completed, the active agent must log an entry in this document detailing the Date, Task Goal, Structural/Architectural Decisions, and any dependencies added.

## Project Origin
- **Initial Setup:** The project started as a dual-script setup (`bot.py` and `summarizer.py`).
- **Refactoring (Current State):** Transitioning to a highly modular, agent-oriented skeleton enforced by a zero-dependency verification script to preserve determinism.

## Action Log

### [2026-03-31] Agent-Oriented Project Restructuring Initiation
**Goal:** Transition codebase into a mature, agent-safe skeleton.
**Structural Decisions:**
- Created `.agent_rules.md` to dictate all agent behavior mechanically.
- Enforced a rule that all execution must happen inside the `venv` to prevent global pollution.
- Re-architected code from single monoliths into isolated functional modules (`/src/telegram`, `/src/audio`, `/src/llm`, `/src/core`).
- Adopted `unittest` based functional tests as the determinant of success (`scripts/verify.sh`).
**Dependencies:** No new external external dependencies added.

### [2026-03-31] Second Brain Feature Implementation
**Goal:** Upgrade the passive summarizer into a multi-persona intelligence engine processing Lineage, Actions, Drafts, and Analysis.
**Structural Decisions:**
- Created `src/llm/parser.py` using Regex to cleanly split the massive single output.
- Overhauled `summarizer_service.py` system prompt to strictly enforce the split boundaries.
- Adhered strictly to `verify.sh` requirements by implementing `test_parser_success` and `test_parser_failsafe` tests in `test_functional.py`.
**Dependencies:** None.

### [2026-04-02] FastAPI Web Viewer Integration
**Goal:** Add a password-protected web UI for traversing and editing the generated markdown notes.
**Structural Decisions:**
- Developed `src/web/server.py` utilizing FastAPI and Jinja2 templates.
- Enforced HTTP Basic Auth globally through a `WEB_PASSWORD` dependency.
- Maintained a strict zero-JS, static approach for HTML editing views.
**Security/State:** Handled `python-multipart` bug and `TemplateResponse` dict unhashable errors successfully. Handled security via local systemd unit `brainstack-web`.

### [2026-04-02] Open Source Docker Package
**Goal:** Restructure the deployment pipeline to permit open-source one-click Docker deployments.
**Structural Decisions:**
- Authored a `Dockerfile` with multi-process capabilities, mapping to a `docker-compose.yml` resolving as `brainstack-bot` and `brainstack-web`.
- Developed `CONTRIBUTING.md` and overhauled `README.md` into a Github landing page.
**Security/State:** Severely clamped down git leakage by isolating `.env` and `Notes/` paths inside `.gitignore` and `.dockerignore`.

### [2026-04-02] Agent Memory Workflow Enforcement
**Goal:** Protect AI Context tracking by migrating into a formal Workflow constraint system.
**Structural Decisions:**
- Created the local `.agents/` namespace to stash AI system files.
- Drafted `.agents/workflows/update-memory.md` to hijack agent execution states before completion.
- Scrapped loose textual requirements inside `.agent_rules.md`.
**Security/State:** N/A.

### [2026-04-02] Internationalization (i18n) Locale Integration
**Goal:** Abstract hardcoded Italian strings out of the LLM prompt and Regex parser to support Open Source adoption.
**Structural Decisions:**
- Added `APP_LANGUAGE` to `.env` falling back gracefully to `"en"`.
- Extracted literal string rules into a mapping dict inside `src/core/locales.py`.
- Altered `tests/test_functional.py` to loop over both English and Italian dictionaries to assert total parser stability across both configurations.
**Security/State:** All syntax validation verified perfectly.
