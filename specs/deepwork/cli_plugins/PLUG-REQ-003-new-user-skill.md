# PLUG-REQ-003: New User Onboarding Skill

## Overview

The `new_user` skill provides a guided onboarding experience for users who have just installed DeepWork. It introduces the three main capabilities (Workflows, Reviews, DeepSchemas), optionally sets up review rules for code projects, and offers to record a first workflow. It is user-invocable only — the agent cannot trigger it autonomously.

## Requirements

### PLUG-REQ-003.1: Skill Setup

1. The plugin MUST provide a `new_user` skill at `plugins/claude/skills/new_user/SKILL.md`.
2. The skill MUST set `disable-model-invocation: true` in its YAML frontmatter so it is only triggered by explicit user invocation (`/new_user`), not autonomously by the agent.
3. The skill's YAML frontmatter `name` field MUST be `"new_user"`.
4. The skill's YAML frontmatter MUST include a `description` field.

### PLUG-REQ-003.2: GitHub Star Prompt

1. As the very first step, the skill MUST check if the `gh` CLI is installed (via `which gh`).
2. If `gh` is available, the skill MUST use `AskUserQuestion` to thank the user for installing DeepWork and offer to star the repo on GitHub so they get update notifications.
3. If the user agrees, the skill MUST run `gh api -X PUT /user/starred/Unsupervisedcom/deepwork`.
4. If `gh` is not installed, the skill MUST skip this step entirely without mentioning it.

### PLUG-REQ-003.3: DeepWork Introduction

1. The skill MUST print a concise introduction explaining what DeepWork does.
2. The introduction MUST cover Workflows (structured multi-step processes with quality gates), Reviews (automated code review rules), and DeepSchemas (file-level contracts with write-time validation).
3. The introduction MUST mention that the three systems work together.

### PLUG-REQ-003.4: Review Rule Setup (Code Projects)

1. The skill MUST check whether the project appears to be a code project (e.g., presence of `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `src/` directory, or similar indicators).
2. If it is a code project, the skill MUST use `AskUserQuestion` to explain automated review rules and ask if the user wants to set them up now.
3. If the user agrees, the skill MUST invoke the `/deepwork:configure_reviews` skill.
4. If it is not a code project, the skill MUST skip this step.

### PLUG-REQ-003.5: Workflow Recording Offer

1. After the review setup step completes or is skipped, the skill MUST use `AskUserQuestion` to explain what workflows are and ask if the user wants to record one now.
2. If the user agrees, the skill MUST invoke the `/deepwork:record` skill.
3. If the user declines, the skill MUST inform them they can run `/deepwork:record` anytime and that `/deepwork` is the main entry point for all DeepWork features.
