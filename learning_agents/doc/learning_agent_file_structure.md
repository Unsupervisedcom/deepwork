# LearningAgent File Structure

All LearningAgents live in `.deepwork/learning_agents/`. Each agent has its own subdirectory named with underscores (e.g., `rails_activejob`).

## Directory Layout

```
.deepwork/learning_agents/
└── <agent_name>/
    ├── agent.yml                          # Core agent definition (required)
    ├── topics/                            # Detailed topic documentation
    │   └── <topic_name>.md
    └── learnings/                         # Experience-based insights
        └── <learning_name>.md
```

## agent.yml

The core definition file. Two required fields:

```yaml
discovery_description: |
  Short description used to decide whether to invoke this agent.
  Keep concise and domain-specific. This is what the outer agent
  sees when deciding which sub-agent to delegate to.

full_expertise: |
  Complete current knowledge of this domain.
  Written in second person ("You should...") because this text
  becomes the agent's system instructions. Structure it as:
  1. Identity statement ("You are an expert on...")
  2. Core concepts and terminology
  3. Common patterns and best practices
  4. Pitfalls to avoid
  5. Decision frameworks
```

The folder name is the source of truth for the agent's name. No `name` field is needed in `agent.yml`.

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

- **Folder names**: Use underscores (`rails_activejob`, `data_pipeline`)
- **Agent names in Claude Code**: Underscores converted to dashes (`rails-activejob`)
- **Topic/learning filenames**: Use underscores, descriptive names (`retry_handling.md`)
