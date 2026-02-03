---
name: deepwork
description: "Start or continue DeepWork workflows using MCP tools"
---

# DeepWork Workflow Manager

Execute multi-step workflows with quality gate checkpoints.

> **IMPORTANT**: This skill uses the DeepWork MCP server. All workflow operations
> are performed through MCP tool calls, not by reading instructions from files.

## Quick Start

1. **Discover workflows**: Call `get_workflows` to see available options
2. **Start a workflow**: Call `start_workflow` with your goal
3. **Execute steps**: Follow the instructions returned
4. **Checkpoint**: Call `finished_step` with your outputs
5. **Iterate or continue**: Handle `needs_work`, `next_step`, or `workflow_complete`

## MCP Tools Reference

### get_workflows

Lists all available workflows in this project.

```
Tool: deepwork.get_workflows
Parameters: none
```

Returns jobs with their workflows, steps, and summaries.

### start_workflow

Begins a new workflow session.

```
Tool: deepwork.start_workflow
Parameters:
  - goal: string (required) - What you want to accomplish
  - job_name: string (required) - Name of the job
  - workflow_name: string (required) - Name of the workflow
  - instance_id: string (optional) - Identifier like "acme" or "q1-2026"
```

Returns session ID, branch name, and first step instructions.

### finished_step

Reports completion of the current step.

```
Tool: deepwork.finished_step
Parameters:
  - outputs: list[string] (required) - File paths of created outputs
  - notes: string (optional) - Notes about what was done
```

Returns one of:
- `needs_work`: Quality criteria not met; fix and retry
- `next_step`: Proceed to next step with new instructions
- `workflow_complete`: All steps done; workflow finished

## Execution Flow

```
User: /deepwork [intent]
     │
     ▼
┌─────────────────┐
│ get_workflows   │ ◄── Discover available workflows
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse intent    │ ◄── Match user intent to workflow
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ start_workflow  │ ◄── Begin session, get first step
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute step    │ ◄── Follow step instructions
│ Create outputs  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ finished_step   │ ◄── Report completion
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
needs_work  next_step ─────► Loop back to "Execute step"
    │         │
    │    workflow_complete
    │         │
    ▼         ▼
┌─────────────────┐
│ Fix issues and  │      Done!
│ retry           │
└─────────────────┘
```

## Intent Parsing

When the user invokes `/deepwork`, parse their intent:

1. **Explicit workflow**: `/deepwork new_job` → start `new_job` workflow
2. **General request**: `/deepwork I want to create a new workflow` → infer best match
3. **No context**: `/deepwork` alone → call `get_workflows` and ask user to choose

## Quality Gates

Steps may have quality criteria. When you call `finished_step`:

1. Outputs are evaluated against criteria
2. If any fail → `needs_work` status with feedback
3. Fix issues based on feedback
4. Call `finished_step` again
5. After passing → proceed to next step

## Git Workflow

DeepWork creates branches for workflow instances:
- Format: `deepwork/{job_name}-{workflow_name}-{instance_id or date}`
- Example: `deepwork/competitive_research-full_analysis-acme`

Commit work as you go. Create PR when workflow completes.

## Guardrails

- Always use MCP tools; never manually read step instruction files
- Create ALL expected outputs before calling `finished_step`
- Read quality gate feedback carefully before retrying
- Don't skip steps unless user explicitly requests it
- Ask for clarification when user intent is ambiguous