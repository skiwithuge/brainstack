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
