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
**Dependencies:** No new external dependencies added.

### [2026-03-31] Second Brain Feature Implementation
**Goal:** Upgrade the passive summarizer into a multi-persona intelligence engine processing Lineage, Actions, Drafts, and Analysis.
**Structural Decisions:**
- Created `src/llm/parser.py` using Regex to cleanly split the massive single output.
- Overhauled `summarizer_service.py` system prompt to strictly enforce the split boundaries.
- Adhered strictly to `verify.sh` requirements by implementing `test_parser_success` and `test_parser_failsafe` tests in `test_functional.py`.
**Dependencies:** None.
