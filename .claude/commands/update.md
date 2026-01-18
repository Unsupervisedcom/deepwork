---
description: Update standard jobs in src/ and sync to installed locations
---

# update

You are executing the **update** job. Update standard jobs in src/ and sync to installed locations

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

This job has 1 step(s):

### job
**Update Standard Job**: Edit standard job source files and sync to installed locations
- Command: `uw.update.job`

## Instructions

This is a **multi-step workflow**. Determine the starting point and run through the steps in sequence.

1. **Analyze user intent** from the text that follows `/update`

2. **Identify the starting step** based on intent:
   - job: Edit standard job source files and sync to installed locations

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

- Job definition: `.deepwork/jobs/update/job.yml`