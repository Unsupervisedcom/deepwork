---
name: update
description: "Updates DeepWork standard jobs in src/ and syncs to installed locations. Use when modifying deepwork_jobs or deepwork_rules."
---

# update

Updates DeepWork standard jobs in src/ and syncs to installed locations. Use when modifying deepwork_jobs or deepwork_rules.

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for maintaining standard jobs bundled with DeepWork. Standard jobs
(like `deepwork_jobs` and `deepwork_rules`) are source-controlled in
`src/deepwork/standard_jobs/` and must be edited there—never in `.deepwork/jobs/`
or `.claude/commands/` directly.

This job guides you through:
1. Identifying which standard job(s) to update from conversation context
2. Making changes in the correct source location (`src/deepwork/standard_jobs/[job_name]/`)
3. Running `deepwork install` to propagate changes to `.deepwork/` and command directories
4. Verifying the sync completed successfully

Use this job whenever you need to modify job.yml files, step instructions, or hooks
for any standard job in the DeepWork repository.


## Standalone Skills

These skills can be run independently at any time:

- **job** - Edits standard job source files in src/ and runs deepwork install to sync changes. Use when updating job.yml or step instructions.
  Command: `/update.job`


## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/update` to determine user intent:
- "job" or related terms → run standalone skill `update.job`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: update.job
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the workflow sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

**Note**: Standalone skills do not auto-continue to other steps.

### Handling Ambiguous Intent

If user intent is unclear, ask which option they want:
- Present available steps as numbered options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in a workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/update/job.yml`