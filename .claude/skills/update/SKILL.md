---
name: update
description: "Update standard jobs in src/ and sync to installed locations"
---

# update

**Multi-step workflow**: Update standard jobs in src/ and sync to installed locations

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


## Available Steps

1. **job** - Edit standard job source files and sync to installed locations

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/update` to determine user intent:
- "job" or related terms → start at `update.job`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: update.job
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

- Job definition: `.deepwork/jobs/update/job.yml`