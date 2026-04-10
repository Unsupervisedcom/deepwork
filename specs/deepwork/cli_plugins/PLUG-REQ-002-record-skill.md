# PLUG-REQ-002: Record Skill (New User Flow)

## Overview

The `record` skill provides a "watch and learn" approach to creating DeepWork workflows. Instead of defining a job upfront, users do their work naturally with Claude Code while the skill observes, clarifies non-obvious decisions, and then turns the session into a repeatable DeepWork job via `/deepwork learn`.

This skill targets new users who know *what* they want to automate but haven't yet learned how to define a DeepWork job from scratch.

## Requirements

### PLUG-REQ-002.1: Skill Setup

1. The plugin MUST provide a `record` skill at `plugins/claude/skills/record/SKILL.md`.
2. The skill MUST set `disable-model-invocation: true` in its YAML frontmatter so it is only triggered by explicit user invocation (`/record`), not autonomously by the agent.
3. The skill's YAML frontmatter `name` field MUST be `"record"`.
4. The skill's YAML frontmatter MUST include a `description` field.

### PLUG-REQ-002.2: Browser Access Check

1. The skill MUST check whether browser automation tools (`mcp__claude-in-chrome__*` or `mcp__plugin_playwright_playwright__*`) are available in the current session.
2. If browser tools are already available, the skill MUST skip the browser question entirely.
3. If no browser tools are available, the skill MUST ask the user (via `AskUserQuestion`) whether they expect to need website access during the workflow.
4. If the user confirms they need website access, the skill MUST tell them to run `/chrome` to set up Claude for Chrome and wait for confirmation before proceeding.

### PLUG-REQ-002.3: Handoff Message

1. After collecting the workflow name and resolving browser access, the skill MUST display a clear, bold-formatted message that tells the user to proceed with their workflow normally using Claude Code.
2. The handoff message MUST tell the user to run `/deepwork learn` when they are satisfied with the results.

### PLUG-REQ-002.4: Clarifying Non-Obvious Actions

1. During the workflow, the agent MUST ask for reasoning when the user makes requests that would not be understandable as a repeatable workflow step — e.g., removing a specific item without explanation, applying an unexplained filter or threshold, or making a domain-specific judgment call.
2. The agent MUST NOT ask for reasoning when the instruction clearly maps to a repeatable step, the reasoning is obvious from context, or the user has already explained their reasoning.
3. When asking for reasoning, the agent SHOULD keep the question short and focused on capturing the logic for future runs.

### PLUG-REQ-002.5: Completion Detection

1. If the user signals completion (e.g., "that looks good", "we're done", "ship it") without running `/deepwork learn`, the agent MUST use `AskUserQuestion` to confirm whether they want to create a repeatable DeepWork job.
2. If the user confirms, the agent MUST invoke the `/deepwork learn` skill.

### PLUG-REQ-002.6: GitHub Star Prompt

1. As the very first step, the skill MUST check if the `gh` CLI is installed (via `which gh`).
2. If `gh` is available, the skill MUST use `AskUserQuestion` to offer to star the DeepWork repo on GitHub so the user gets update notifications.
3. If the user agrees, the skill MUST run `gh api -X PUT /user/starred/Unsupervisedcom/deepwork`.
4. If `gh` is not installed, the skill MUST skip this step entirely without mentioning it.
