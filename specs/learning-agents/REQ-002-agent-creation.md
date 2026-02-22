# REQ-002: Agent Creation

## Overview

The `create-agent` skill scaffolds a new LearningAgent by creating the required directory structure, placeholder files, and a Claude Code agent file. It then guides the user through initial configuration.

## Requirements

### REQ-002.1: Skill Invocation

The `create-agent` skill MUST be invocable via `/learning-agents create <name>`. If no name argument is provided, the skill MUST prompt the user for a name.

### REQ-002.2: Name Normalization

The skill MUST normalize agent names by converting spaces and uppercase letters to lowercase dashes (e.g., `"Rails ActiveJob"` becomes `"rails-activejob"`).

### REQ-002.3: Conflict Detection -- Claude Agent File

Before creation, the skill MUST check `.claude/agents/` for an existing file matching `<agent-name>.md`. If a conflict is found, the skill MUST inform the user and ask how to proceed before taking any action.

### REQ-002.4: Conflict Detection -- Agent Directory

If the agent directory `.deepwork/learning-agents/<agent-name>/` already exists, the skill MUST inform the user and ask whether to proceed with updating the configuration or stop.

### REQ-002.5: Scaffold Script Execution

The skill MUST execute the scaffold script at `${CLAUDE_PLUGIN_ROOT}/scripts/create_agent.sh` passing the normalized agent name as the argument.

### REQ-002.6: Scaffold Script -- Agent Directory Creation

The `create_agent.sh` script MUST create the following directory structure when the agent directory does not exist:
- `.deepwork/learning-agents/<agent-name>/core-knowledge.md` -- with TODO placeholder content
- `.deepwork/learning-agents/<agent-name>/topics/` -- with `.gitkeep`
- `.deepwork/learning-agents/<agent-name>/learnings/` -- with `.gitkeep`
- `.deepwork/learning-agents/<agent-name>/additional_learning_guidelines/` -- containing `README.md`, `issue_identification.md`, `issue_investigation.md`, and `learning_from_issues.md`

### REQ-002.7: Scaffold Script -- Additional Learning Guidelines README

The `create_agent.sh` script MUST create an `additional_learning_guidelines/README.md` file that describes the purpose of each guideline file (`issue_identification.md`, `issue_investigation.md`, `learning_from_issues.md`).

### REQ-002.8: Scaffold Script -- Claude Agent File Creation

The `create_agent.sh` script MUST create `.claude/agents/<agent-name>.md` with:
- YAML frontmatter containing `name` and `description` fields (initially set to `"TODO"`)
- Dynamic context injection for `core-knowledge.md` using `!` backtick syntax
- A Topics section with dynamic listing of topic files
- A Learnings section referencing the learnings directory

### REQ-002.9: Scaffold Script -- Agent Name Substitution

The `create_agent.sh` script MUST replace the `__AGENT__` placeholder in the generated Claude agent file with the actual agent name using `sed`.

### REQ-002.10: Scaffold Script -- Idempotency

The `create_agent.sh` script MUST NOT overwrite existing directories or files. If the agent directory already exists, it MUST print a message to stderr and skip directory creation. If the Claude agent file already exists, it MUST print a message to stderr and skip file creation.

### REQ-002.11: Scaffold Script -- Input Validation

The `create_agent.sh` script MUST require a non-empty agent name argument. If no argument is provided, it MUST print a usage message to stderr and exit with code 1.

### REQ-002.12: Interactive Configuration

After scaffolding, the skill MUST ask the user about the agent's domain of expertise and the kinds of tasks it will handle, then update:
- `core-knowledge.md` -- replacing the TODO content with domain expertise written in second person
- `.claude/agents/<agent-name>.md` frontmatter -- replacing TODO `name` with a human-readable display name and TODO `description` with a concise invocation description (2-3 sentences max)

### REQ-002.13: Optional Knowledge Seeding

The skill MUST offer the user the option to seed initial topics or learnings. If the user accepts, the skill MUST create files following the topic and learning file formats defined in REQ-003.

### REQ-002.14: Creation Summary

Upon completion, the skill MUST output a summary listing all files created or modified, usage instructions for invoking the agent via the Task tool, and a note about the learning cycle.

### REQ-002.15: No Overwrites Without Confirmation

The skill MUST NOT overwrite any existing file without explicit user confirmation.
