---
name: deepplan
description: "Start structured planning that produces an executable DeepWork plan"
---

# DeepPlan

Structured planning workflow that explores the codebase, generates competing
designs, and produces an executable DeepWork job definition.

## How to Use

1. Call `start_workflow` with:
   - `job_name`: `"deepplan"`
   - `workflow_name`: `"create_deep_plan"`
   - `goal`: the user's planning request
2. Follow the step instructions returned by the MCP tools. They supersede any default planning phases.

## Intent Parsing

When the user invokes `/deepplan`, parse their intent:
- With goal: `/deepplan <goal>` -> start the workflow with `<goal>`
- No context: `/deepplan` alone -> start the workflow using conversation context as the goal; if no context, ask what they want to plan
