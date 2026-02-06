---
name: job_porter
description: "Helps users port DeepWork jobs between local and global locations"
---

# job_porter

Helps users port DeepWork jobs between local and global locations

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

This job assists users in managing job scope by porting jobs between local 
project-specific locations (.deepwork/jobs/) and global system-wide locations 
(~/.deepwork/jobs/). It guides users through discovering available jobs, 
understanding the differences between local and global scope, and safely 
migrating jobs between scopes.


## Standalone Skills

These skills can be run independently at any time:

- **list_jobs** - Shows all available jobs in both local and global locations with their current scope
  Command: `/job_porter.list_jobs`
- **port_job** - Moves a job between local and global scope with safety validation
  Command: `/job_porter.port_job`
- **explain_scopes** - Provides detailed explanation of local vs global jobs and when to use each
  Command: `/job_porter.explain_scopes`


## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/job_porter` to determine user intent:
- "list_jobs" or related terms → run standalone skill `job_porter.list_jobs`
- "port_job" or related terms → run standalone skill `job_porter.port_job`
- "explain_scopes" or related terms → run standalone skill `job_porter.explain_scopes`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: job_porter.list_jobs
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

- Job definition: `.deepwork/jobs/job_porter/job.yml`