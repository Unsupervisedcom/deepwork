---
name: experts.new_workflow
description: "Create a new multi-step DeepWork workflow with spec definition, review, and implementation"
---

# experts.new_workflow

Create a new multi-step DeepWork workflow with spec definition, review, and implementation

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

Guide the user through creating a new DeepWork workflow by:
1. Understanding their workflow requirements through interactive questioning
2. Creating a validated workflow.yml specification
3. Reviewing the spec against quality criteria
4. Generating step instruction files and syncing skills


## Steps in Order

1. **define** - Create a workflow.yml by gathering requirements through structured questions
2. **review_workflow_spec** - Review workflow.yml against quality criteria using a sub-agent for unbiased validation
3. **implement** - Generate step instruction files and sync skills from the validated workflow.yml

**Start workflow**: `/experts.define`

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/experts.new_workflow` to determine user intent:
- "define" or related terms → run step `experts.define`
- "review_workflow_spec" or related terms → run step `experts.review_workflow_spec`
- "implement" or related terms → run step `experts.implement`
- No specific step mentioned → start at first step `experts.define`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: experts.define
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the workflow sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in a workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Workflow definition: `.deepwork/experts/experts/workflows/new_workflow/workflow.yml`