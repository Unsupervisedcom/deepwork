# PLUG-REQ-001: Claude Code Plugin

## Overview

The Claude Code plugin is the primary distribution mechanism for DeepWork on the Claude Code CLI. It provides users with skills for running workflows, running code reviews, and configuring review rules. It also registers the DeepWork MCP server so the agent can interact with the workflow engine, and installs hooks that integrate with the developer's commit workflow.

## Requirements

### PLUG-REQ-001.1: Plugin Manifest following Claude Code Plugin Conventions

1. The plugin MUST provide a manifest at `plugins/claude/.claude-plugin/plugin.json`.
2. The manifest `name` field MUST be `"deepwork"`.
3. The manifest MUST include a `description`, `version`, `author`, and `repository` field.

### PLUG-REQ-001.2: MCP Server Registration following Claude Code Plugin Conventions

1. The plugin MUST register the DeepWork MCP server via `plugins/claude/.mcp.json`.
2. The MCP server command MUST be `uvx` with `deepwork` and `serve` as the first two arguments.
3. The MCP server arguments MUST include `--platform claude` so the server knows it is running under Claude Code.
4. The MCP server arguments MUST include `--path .` so job discovery starts from the project root.

### PLUG-REQ-001.3: Deepwork Skill

1. The plugin MUST provide a `deepwork` skill at `plugins/claude/skills/deepwork/SKILL.md`.
2. The skill MUST be user-invocable as `/deepwork`.
3. The skill MUST instruct the agent to use the MCP server tools (`get_workflows`, `start_workflow`, `finished_step`) for all workflow operations.
4. The skill MUST support discovering available workflows, starting a named workflow, inferring the best workflow from a freeform request, and prompting the user to choose when no context is given.
5. The skill MUST support creating new jobs by routing to the `deepwork_jobs` job's `new_job` workflow.

### PLUG-REQ-001.4: Review Skill

1. The plugin MUST provide a `review` skill at `plugins/claude/skills/review/SKILL.md`.
2. The skill MUST be user-invocable as `/review`.
3. The skill MUST instruct the agent to run reviews by calling the DeepWork MCP review tools, not by invoking CLI commands directly.
4. The skill MUST instruct the agent to launch review tasks in parallel.
5. The skill MUST instruct the agent to automatically apply findings that are obviously correct with no downsides (e.g., typo fixes, unused import removal).
6. The skill MUST instruct the agent to present findings with trade-offs or subjective judgment to the user individually for decision.
7. The skill MUST instruct the agent to re-run reviews after making changes, repeating until no further actionable findings remain.
8. The skill MUST redirect configuration requests (creating or modifying `.deepreview` files) to the `configure_reviews` skill.
9. When no review rules are configured, the skill MUST offer to help the user discover and set up rules rather than silently producing no results.

### PLUG-REQ-001.5: Configure Reviews Skill

1. The plugin MUST provide a `configure_reviews` skill at `plugins/claude/skills/configure_reviews/SKILL.md`.
2. The skill MUST be user-invocable as `/configure_reviews`.
3. The skill MUST instruct the agent to consult the `README_REVIEWS.md` reference documentation before creating or modifying rules.
4. The skill MUST instruct the agent to reuse existing review rules and instructions where possible rather than creating duplicates.
5. The skill MUST instruct the agent to test new rules by triggering a review run and verifying the new rule appears in the output.

### PLUG-REQ-001.6: Review Reference Documentation

1. The plugin MUST include `README_REVIEWS.md` at `plugins/claude/README_REVIEWS.md`.
2. This file MUST be a symlink to `../../README_REVIEWS.md` (the project root copy) so that updates to the canonical file are automatically reflected in the plugin.

### PLUG-REQ-001.7: Post-Commit Review Reminder

1. The plugin MUST register a `PostToolUse` hook on the `Bash` tool via `plugins/claude/hooks/hooks.json`.
2. When the agent runs a `git commit` command, the hook MUST prompt the agent to offer the user a review of the committed changes.

### PLUG-REQ-001.8: Skill Directory Conventions

1. Each skill MUST reside in its own directory under `plugins/claude/skills/`.
2. Each skill directory MUST contain a `SKILL.md` file.
3. The `name` field in each skill's YAML frontmatter MUST match its directory name.
4. Each skill's YAML frontmatter MUST include a `description` field.

### PLUG-REQ-001.9: Shared Skill Content

1. The `deepwork` skill body MUST be kept in sync with the canonical platform content in `platform/skill-body.md`.
2. Both the Claude and Gemini plugins MUST deliver equivalent workflow functionality (discovering, starting, and completing workflows; creating new jobs) so that users have a consistent experience regardless of which CLI they use.

### PLUG-REQ-001.10: MCP configures Claude Code

1. When the MCP server starts, it MUST configure Claude Code settings to allow the invocation of the MCP tool without user prompts.

### PLUG-REQ-001.11: Post-Compaction Context Restoration

1. The plugin MUST register a `SessionStart` hook with matcher `"compact"` via `plugins/claude/hooks/hooks.json`.
2. When Claude Code compacts context, the hook MUST call `deepwork jobs get-stack` to retrieve active workflow sessions.
3. If active sessions are found, the hook MUST inject workflow context (session ID, workflow name, goal, current step, completed steps, common job info, and step instructions) as `additionalContext` in the `SessionStart` hook response.
4. If no active sessions are found or the `deepwork` command fails, the hook MUST output an empty JSON object `{}` (graceful degradation).
5. The hook MUST NOT produce errors or non-zero exit codes under any failure condition.
