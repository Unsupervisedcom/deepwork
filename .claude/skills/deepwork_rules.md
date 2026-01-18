---
description: "Rules enforcement for AI agent sessions"
---

# deepwork_rules

**Multi-step workflow**: Rules enforcement for AI agent sessions

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

Manages rules that automatically trigger when certain files change during an AI agent session.
Rules help ensure that code changes follow team guidelines, documentation is updated,
and architectural decisions are respected.

Rules are stored as individual markdown files with YAML frontmatter in the `.deepwork/rules/`
directory. Each rule file specifies:
- Detection mode: trigger/safety, set (bidirectional), or pair (directional)
- Patterns: Glob patterns for matching files, with optional variable capture
- Instructions: Markdown content describing what the agent should do

Example use cases:
- Update installation docs when configuration files change
- Require security review when authentication code is modified
- Ensure API documentation stays in sync with API code
- Enforce source/test file pairing


## Available Steps

1. **define** - Create a new rule file in .deepwork/rules/

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/deepwork_rules` to determine user intent:
- "define" or related terms → start at `deepwork_rules.define`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: deepwork_rules.define
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

## Context Files

- Job definition: `.deepwork/jobs/deepwork_rules/job.yml`