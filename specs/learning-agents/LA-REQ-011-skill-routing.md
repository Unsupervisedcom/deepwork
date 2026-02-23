# LA-REQ-011: Skill Routing and CLI Interface

## Overview

The `/learning-agents` skill is the dispatch entry point for the plugin. It routes user input to the appropriate sub-skill based on the first token of the arguments. It also defines the public-facing command interface.

## Requirements

### LA-REQ-011.1: Entry Point Skill

The plugin MUST provide a top-level skill named `learning-agents` that serves as the dispatch entry point. This skill MUST be user-invocable.

### LA-REQ-011.2: Argument Parsing

The skill MUST split `$ARGUMENTS` on the first whitespace. The first token is the sub-command (case-insensitive); the remainder is passed to the sub-skill.

### LA-REQ-011.3: Underscore-Dash Equivalence

The skill MUST accept both underscores and dashes in sub-command names as equivalent (e.g., `report_issue` and `report-issue` MUST both route to the same sub-skill).

### LA-REQ-011.4: Create Sub-Command

The `create <name>` sub-command MUST invoke `Skill learning-agents:create-agent <name>`.

### LA-REQ-011.5: Learn Sub-Command

The `learn` sub-command MUST invoke `Skill learning-agents:learn`. Arguments after `learn` MUST be ignored.

### LA-REQ-011.6: Report Issue Sub-Command

The `report_issue <agentId> <details>` sub-command MUST:
1. Search `.deepwork/tmp/agent_sessions/` for a subdirectory whose name contains the provided `agentId`
2. If no match is found, inform the user
3. If multiple matches exist, use the most recently modified one
4. Invoke `Skill learning-agents:report-issue <resolved-path> <details>`

### LA-REQ-011.7: Help Text

When no arguments are provided or input does not match any known sub-command, the skill MUST display a help message listing all available sub-commands with descriptions and examples.

### LA-REQ-011.8: No Inline Implementation

The skill MUST always route to the appropriate sub-skill. It MUST NOT implement sub-command logic inline.

### LA-REQ-011.9: Argument Pass-Through

The skill MUST pass arguments through to sub-skills exactly as provided by the user (after extracting the sub-command token).

### LA-REQ-011.10: Available Sub-Commands

The skill MUST support exactly three sub-commands:
- `create` -- create a new LearningAgent
- `learn` -- run learning cycle on pending sessions
- `report_issue` -- report an issue with an agent

### LA-REQ-011.11: Sub-Skill Registry

The plugin MUST provide the following skills, each in its own directory under `skills/`:
- `learning-agents` -- dispatch entry point
- `create-agent` -- agent scaffolding
- `learn` -- learning cycle orchestration
- `identify` -- issue identification (non-user-invocable)
- `investigate-issues` -- issue investigation (non-user-invocable)
- `incorporate-learnings` -- learning incorporation (non-user-invocable)
- `report-issue` -- issue file creation (non-user-invocable)
- `prompt-review` -- prompt engineering review (user-invocable)

### LA-REQ-011.12: Prompt Review Skill Independence

The `prompt-review` skill MUST be independently invocable (it is NOT routed through the `/learning-agents` dispatcher). It MUST be a separate, standalone skill.
