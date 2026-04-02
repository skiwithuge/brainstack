---
description: Update the AI Agent Memory with latest task outcomes and architectural decisions
---

# Agent Memory Protocol

When instructed to update your memory or immediately prior to concluding a major session, you MUST execute these steps systematically:

1. **Locate the Memory File**: Use your file reading tools to view `.agents/AGENT_MEMORY.md`.
2. **Review Chronology**: Quickly review the last entry to maintain architectural consistency.
3. **Formulate New Entry**: Generate a new Markdown section formatted as:
    - `### [Current Date]`
    - `**Goal:**` What task was resolved.
    - `**Architectural Decisions:**` Detail any structurally significant tradeoffs, new files, libraries, or frameworks.
    - `**Security/State:**` Note if strict `.gitignore` safety or Docker configurations were altered.
4. **Append Memory**: Safely write this new section to the bottom of the `.agents/AGENT_MEMORY.md` document without wiping history.
5. **Validation**: Execute `./scripts/commit.sh "Docs: Update Agent Project Memory"` to synchronize.
