---
name: make_release
description: "Automate release preparation with changelog, version bump, and PR creation"
---

# make_release

**Multi-step workflow**: Automate release preparation with changelog, version bump, and PR creation

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A streamlined workflow for preparing releases of the DeepWork project. This job
automates the tedious parts of releasing: finding the latest version tag, gathering
commits since that tag, updating the changelog, bumping the version in pyproject.toml,
syncing uv.lock, and creating a pull request.

The workflow analyzes commit history to recommend an appropriate version bump
(patch, minor, or major) based on the changes, then asks for confirmation before
proceeding.

Outputs:
- Updated CHANGELOG.md with a new version entry
- Updated pyproject.toml with the new version
- Updated uv.lock
- A pull request targeting main


## Available Steps

1. **gather_changes** - Find the latest version tag and collect all commits since then
2. **prepare_release** - Update changelog, bump version in pyproject.toml, and sync uv.lock (requires: gather_changes)
3. **create_pr** - Create a pull request with the release changes targeting main (requires: prepare_release)

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/make_release` to determine user intent:
- "gather_changes" or related terms → start at `make_release.gather_changes`
- "prepare_release" or related terms → start at `make_release.prepare_release`
- "create_pr" or related terms → start at `make_release.create_pr`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: make_release.gather_changes
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available steps as numbered options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in the workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/make_release/job.yml`