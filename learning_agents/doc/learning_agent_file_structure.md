# LearningAgent File Structure

All LearningAgents live in `.deepwork/learning-agents/`. Each agent has its own subdirectory named with dashes (e.g., `rails-activejob`).

## Directory Layout

```
.deepwork/learning-agents/
└── <agent-name>/
    ├── core-knowledge.md                  # Core expertise (required)
    ├── topics/                            # Detailed topic documentation
    │   └── <topic-name>.md
    └── learnings/                         # Experience-based insights
        └── <learning-name>.md
```

## core-knowledge.md

The agent's core expertise, written in second person ("You should...") because this text becomes the agent's system instructions. Structure it as:

1. Identity statement ("You are an expert on...")
2. Core concepts and terminology
3. Common patterns and best practices
4. Pitfalls to avoid
5. Decision frameworks

This file is plain markdown (no frontmatter needed). It is dynamically included into the agent's prompt at invocation time via the `.claude/agents/<agent-name>.md` file.

The agent's discovery description (used to decide whether to invoke this agent) lives in the `.claude/agents/<agent-name>.md` frontmatter `description` field, not in this directory.

The folder name is the source of truth for the agent's name.

> **Note**: `learning_last_performed_timestamp` is tracked per-conversation in the session log folder (`.deepwork/tmp/agent_sessions/`), not here. See `learning_log_folder_structure.md`.

## Topics vs Learnings

Topics and learnings serve different purposes:

- **Topics** are conceptual reference material about areas within the agent's domain. They document *how things work* — patterns, APIs, conventions, decision frameworks. Think of them as chapters in a reference manual.
- **Learnings** are detailed post-mortems of specific incidents where the agent made mistakes and something was learned. They document *what went wrong and why* — like debugging war stories. They're suited for complex experiences (e.g., a multi-step debugging session that uncovered a subtle interaction) where the narrative context matters for understanding the lesson.

Both are injected into the agent's prompt at invocation time, but they serve different retrieval needs: topics answer "how should I approach X?" while learnings answer "what went wrong last time I tried X?"

## topics/ Directory

Reference documentation on conceptual areas within the agent's domain. Each topic is a markdown file with YAML frontmatter:

```markdown
---
name: Retry Handling
keywords:
  - retry
  - exponential backoff
  - dead letter queue
last_updated: 2025-01-15
---

Detailed documentation about retry handling...
```

**Frontmatter fields:**
- `name` (required): Human-readable topic name
- `keywords` (optional): Topic-specific search terms. Avoid broad domain terms.
- `last_updated` (optional): Date in YYYY-MM-DD format

## learnings/ Directory

Incident post-mortems from real agent sessions. Each learning captures a specific mistake or failure, what investigation revealed, and the generalizable insight. These are most valuable for complex experiences — multi-step debuggings, subtle misunderstandings, or surprising interactions — where the full narrative context helps the agent avoid repeating the same mistake.

Each learning is a markdown file with YAML frontmatter:

```markdown
---
name: Job errors not going to Sentry
last_updated: 2025-01-20
summarized_result: |
  Brief 1-3 sentence summary of the key takeaway.
---

## Context
What was happening when the issue occurred.

## Investigation
What was discovered during investigation.

## Resolution
How the issue was resolved.

## Key Takeaway
The generalizable insight that should inform future behavior.
```

**Frontmatter fields:**
- `name` (required): Descriptive name of the learning
- `last_updated` (optional): Date in YYYY-MM-DD format
- `summarized_result` (optional but recommended): 1-3 sentence summary

## Naming Conventions

- **Folder names**: Use dashes (`rails-activejob`, `data-pipeline`)
- **Agent names in Claude Code**: Match folder names (`rails-activejob`)
- **Topic/learning filenames**: Use dashes, descriptive names (`retry-handling.md`)
