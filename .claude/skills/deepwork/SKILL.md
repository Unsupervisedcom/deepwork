---
name: deepwork
description: "Start or continue DeepWork workflows using MCP tools"
---

# DeepWork Workflow Manager

Execute multi-step workflows with quality gate checkpoints.

> **IMPORTANT**: Use the DeepWork MCP server tools. All workflow operations
> are performed through MCP tool calls and following the instructions they return,
> not by reading instructions from files.

## How to Use

1. Call `get_workflows` to discover available workflows
2. Call `start_workflow` with goal, job_name, and workflow_name
3. Follow the step instructions returned
4. Call `finished_step` with your outputs when done
5. Handle the response: `needs_work`, `next_step`, or `workflow_complete`

## Intent Parsing

When the user invokes `/deepwork`, parse their intent:

- **Explicit workflow**: `/deepwork new_job` → start the `new_job` workflow
- **General request**: `/deepwork I want to create a new workflow` → infer best match from available workflows
- **No context**: `/deepwork` alone → call `get_workflows` and ask user to choose