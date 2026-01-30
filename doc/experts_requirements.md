# Experts System

> **Status**: Implemented. See `doc/architecture.md` for integration details.

Experts are auto-improving collections of domain knowledge. They provide a structured mechanism for accumulating expertise and exposing it throughout the system.

## Overview

Each expert represents deep knowledge in a specific domain (e.g., "Ruby on Rails ActiveJob", "Social Marketing"). Experts consist of:
- **Core expertise**: The foundational knowledge about the domain
- **Topics**: Detailed documentation on specific subjects within the domain
- **Learnings**: Hard-fought insights from real experiences

## Directory Structure

Experts live in `.deepwork/experts/[expert-folder-name]/`:

```
.deepwork/experts/
└── rails_activejob/
    ├── expert.yml           # Core expert definition
    ├── topics/              # Detailed topic documentation
    │   └── retry_handling.md
    └── learnings/           # Experience-based insights
        └── job_errors_not_going_to_sentry.md
```

### Naming Convention

The **expert name** is derived from the folder name:
- Spaces and underscores become dashes
- Example: folder `rails_activejob` → expert name `rails-activejob`
- This name is used in CLI commands: `deepwork topics --expert "rails-activejob"`

## File Formats

### expert.yml

```yaml
discovery_description: |
  Short description used by other parts of the system to decide
  whether to invoke this expert. Keep it concise and specific.

full_expertise: |
  Unlimited text (but generally ~5 pages max) containing the
  complete current knowledge of this domain. This is the core
  expertise that gets included in the generated agent.
```

**Note**: The expert name is not a field in this file—it's derived from the folder name.

### topics/*.md

Topics are frontmatter Markdown files covering specific subjects within the domain.

```markdown
---
name: Retry Handling
keywords:
  - retry
  - exponential backoff
  - dead letter queue
last_updated: 2025-01-15
---

Detailed documentation about retry handling in ActiveJob...
```

| Field | Description |
|-------|-------------|
| `name` | Human-readable name (e.g., "Retry Handling") |
| `keywords` | Topic-specific keywords only—avoid broad terms like "Rails" |
| `last_updated` | Date stamp (manually maintained) |

Filenames are purely organizational and don't affect functionality.

### learnings/*.md

Learnings document complex experiences and hard-fought insights—like mini retrospectives.

```markdown
---
name: Job errors not going to Sentry
last_updated: 2025-01-20
summarized_result: |
  Sentry changed their standard gem for hooking into jobs.
  SolidQueue still worked but ActiveJobKubernetes did not.
---

## Context
We noticed errors from background jobs weren't appearing in Sentry...

## Investigation
After debugging, we discovered that Sentry's latest gem update...

## Resolution
Updated the initialization to explicitly configure the hook...
```

| Field | Description |
|-------|-------------|
| `name` | Human-readable title of the learning |
| `last_updated` | Date stamp (manually maintained) |
| `summarized_result` | Brief summary of the key finding |

## CLI Commands

### List Topics

```bash
deepwork topics --expert "rails-activejob"
```

Returns a Markdown list of topics:
- Name and relative file path as a Markdown link
- Followed by keywords
- Sorted by most-recently-updated

### List Learnings

```bash
deepwork learnings --expert "rails-activejob"
```

Returns a Markdown list of learnings:
- Name and relative file path as a Markdown link
- Followed by the summarized result
- Sorted by most-recently-updated

## Sync Behavior

`deepwork sync` generates Claude agents from experts (in addition to syncing jobs).

### Generated Agent Location

Agents are created in `.claude/agents/` with:
- **Filename**: `dwe_[expert-name].md` (e.g., `dwe_rails-activejob.md`)
- **name field**: `[expert-name]` (e.g., `rails-activejob`)
- **description**: The `discovery_description` from expert.yml

### Agent Body Content

The agent body combines:
1. The `full_expertise` text
2. A topics list using Claude's dynamic command embedding:
   ```
   $(deepwork topics --expert "rails-activejob")
   ```
3. A learnings list using the same mechanism:
   ```
   $(deepwork learnings --expert "rails-activejob")
   ```

This ensures the agent always has access to the latest topics and learnings at runtime.

## Standard Experts

Standard experts ship with DeepWork and are located at `src/deepwork/standard/experts/`.

When `deepwork install` runs, these are copied into `.deepwork/experts/` in the target project.

## Future Considerations

- Experts and jobs are currently independent systems
- Future versions may enable experts to reference each other and collaborate with jobs
