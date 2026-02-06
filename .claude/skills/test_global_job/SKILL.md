---
name: test_global_job
description: "A test global job for demonstration"
---

# test_global_job

A test global job for demonstration

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

This is a test job to demonstrate global job functionality

## Standalone Skills

These skills can be run independently at any time:

- **test_step** - A simple test step
  Command: `/test_global_job.test_step`


## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/test_global_job` to determine user intent:
- "test_step" or related terms → run standalone skill `test_global_job.test_step`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: test_global_job.test_step
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the workflow sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

**Note**: Standalone skills do not auto-continue to other steps.

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available steps as numbered options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in a workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/test_global_job/job.yml`