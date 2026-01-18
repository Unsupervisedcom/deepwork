---
description: Rules enforcement for AI agent sessions
---

# deepwork_rules

You are executing the **deepwork_rules** job. Rules enforcement for AI agent sessions

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

This job has 1 step(s):

### define
**Define Rule**: Create a new rule file in .deepwork/rules/
- Command: `uw.deepwork_rules.define`

## Instructions

This is a **multi-step workflow**. Determine the starting point and run through the steps in sequence.

1. **Analyze user intent** from the text that follows `/deepwork_rules`

2. **Identify the starting step** based on intent:
   - define: Create a new rule file in .deepwork/rules/

3. **Run the workflow** starting from the identified step:
   - Invoke the starting step using the Skill tool
   - When that step completes, **automatically continue** to the next step in the workflow
   - Continue until the workflow is complete or the user intervenes

4. **If intent is ambiguous**, ask the user which step to start from:
   - Present the available steps as numbered options
   - Use AskUserQuestion to let them choose

**Critical**:
- You MUST invoke each step using the Skill tool. Do not copy/paste step instructions.
- After each step completes, check if there's a next step and invoke it automatically.
- The workflow continues until all dependent steps are complete.

## Context Files

- Job definition: `.deepwork/jobs/deepwork_rules/job.yml`