---
name: deepplan
description: "Start structured planning — explores, designs, and produces an executable plan"
---

# DeepPlan

Structured planning workflow that explores the codebase, generates competing
designs, and produces an executable DeepWork job definition.

## How to Use

1. Call `EnterPlanMode` if not already in plan mode
2. Call `start_workflow` with:
   - `job_name`: `"deepplan"`
   - `workflow_name`: `"create_deep_plan"`
   - `goal`: the user's planning request
3. Follow the step instructions returned by the MCP tools — they supersede
   the default planning phases

## Intent Parsing

When the user invokes `/deepplan`, parse their intent:
- **With goal**: `/deepplan <goal>` → enter plan mode and start the workflow
  with `<goal>`
- **No context**: `/deepplan` alone → enter plan mode and start the workflow
  using conversation context as the goal; if no context, ask the user what
  they want to plan
