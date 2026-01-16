---
description: Update standard jobs in src/ and sync to installed locations
---

# update

You are executing the **update** job. Update standard jobs in src/ and sync to installed locations

A workflow for maintaining standard jobs bundled with DeepWork. Standard jobs
(like `deepwork_jobs` and `deepwork_policy`) are source-controlled in
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

Determine what the user wants to do and route to the appropriate step.

1. **Analyze user intent** from the text that follows `/update`

2. **Match intent to a step**:
   - job: Edit standard job source files and sync to installed locations

3. **Invoke the matched step** using the Skill tool:
   ```
   Skill: <step_command_name>
   ```

4. **If intent is ambiguous**, ask the user which step they want:
   - Present the available steps as numbered options
   - Use AskUserQuestion to let them choose

**Critical**: You MUST invoke the step using the Skill tool. Do not copy/paste the step's instructions. The Skill tool invocation ensures the step's quality validation hooks fire.

## Context Files

- Job definition: `.deepwork/jobs/update/job.yml`