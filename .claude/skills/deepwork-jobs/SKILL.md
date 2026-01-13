---
name: deepwork-jobs
description: Use this skill when the user wants to create, modify, or understand DeepWork jobs.
Triggers on phrases like "make a job", "create a workflow", "new job for", "define a job",
or questions about how DeepWork jobs work.

user-invocable: false
---

# DeepWork Jobs Workflow Guide

When users want to create or modify DeepWork jobs, guide them through the appropriate workflow.

## Creating a New Job

To create a new job, follow this sequence:

1. **First, run `/deepwork_jobs.define`** - This will:
   - Ask the user about their workflow goals
   - Understand the steps, inputs, and outputs
   - Create the `job.yml` specification file
   - The define step uses interactive Q&A, so let it guide the conversation

2. **Then, run `/deepwork_jobs.implement`** - This will:
   - Read the job.yml created by define
   - Generate instruction files for each step
   - Run `deepwork sync` to create slash commands
   - Create an implementation summary

3. **Tell the user to reload commands** - After implementation, they need to:
   - Run `/reload` or restart their session to see new commands

## Modifying an Existing Job

To modify an existing job:

1. **Run `/deepwork_jobs.refine`** with the job name
   - This handles changes safely and maintains consistency
   - Updates version numbers and changelog
   - Re-syncs commands after changes

## Understanding the Workflow

When users ask questions about jobs, explain:

- Jobs are multi-step workflows defined in `.deepwork/jobs/[name]/job.yml`
- Each step has inputs (user parameters or files from previous steps) and outputs
- Steps can have dependencies on other steps
- Quality hooks (stop_hooks) enable AI self-validation before completing steps
- Skills can be bundled with jobs to provide additional capabilities

## Example Interaction

User: "I want to create a job for writing blog posts"

Response: "I'll help you create a blog post workflow! Let me start the job definition process."
Then invoke: `/deepwork_jobs.define`

User: "How do jobs work?"

Response: Explain the define → implement → use workflow from the job description.

## Important Notes

- Always use the slash commands (`/deepwork_jobs.define`, etc.) rather than trying
  to create job files manually - the commands handle validation and structure
- The define step is interactive - it will ask questions; don't try to create
  the job.yml directly without going through the Q&A process
- After implementing a job, always remind users to reload commands
