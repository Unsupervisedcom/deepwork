---
description: DeepWork job management commands
---

# deepwork_jobs

You are executing the **deepwork_jobs** job. DeepWork job management commands

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `define` command guides you through an interactive process to create a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
and generating all necessary files.

The `learn` command reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Available Steps

This job has 3 step(s):

### define
**Define Job Specification**: Create the job.yml specification file by understanding workflow requirements
- Command: `uw.deepwork_jobs.define`
### implement
**Implement Job Steps**: Generate instruction files for each step based on the job.yml specification
- Command: `uw.deepwork_jobs.implement`
- Requires: define
### learn
**Learn from Job Execution**: Reflect on conversation to improve job instructions and capture learnings
- Command: `deepwork_jobs.learn`

## Instructions

This is a **multi-step workflow**. Determine the starting point and run through the steps in sequence.

1. **Analyze user intent** from the text that follows `/deepwork_jobs`

2. **Identify the starting step** based on intent:
   - define: Create the job.yml specification file by understanding workflow requirements
   - implement: Generate instruction files for each step based on the job.yml specification
   - learn: Reflect on conversation to improve job instructions and capture learnings

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

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`