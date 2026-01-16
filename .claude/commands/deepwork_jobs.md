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
- Command: `_deepwork_jobs.define`
### implement
**Implement Job Steps**: Generate instruction files for each step based on the job.yml specification
- Command: `_deepwork_jobs.implement`
- Requires: define
### learn
**Learn from Job Execution**: Reflect on conversation to improve job instructions and capture learnings
- Command: `deepwork_jobs.learn`

## Instructions

Determine what the user wants to do and route to the appropriate step.

1. **Analyze user intent** from the text that follows `/deepwork_jobs`

2. **Match intent to a step**:
   - define: Create the job.yml specification file by understanding workflow requirements
   - implement: Generate instruction files for each step based on the job.yml specification
   - learn: Reflect on conversation to improve job instructions and capture learnings

3. **Invoke the matched step** using the Skill tool:
   ```
   Skill: <step_command_name>
   ```

4. **If intent is ambiguous**, ask the user which step they want:
   - Present the available steps as numbered options
   - Use AskUserQuestion to let them choose

**Critical**: You MUST invoke the step using the Skill tool. Do not copy/paste the step's instructions. The Skill tool invocation ensures the step's quality validation hooks fire.

## Context Files

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`