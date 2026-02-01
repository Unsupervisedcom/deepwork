---
name: experts.review_pr
description: "Coordinate expert-driven PR review with iterative improvement cycles"
---

# experts.review_pr

Coordinate expert-driven PR review with iterative improvement cycles

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

Orchestrate a comprehensive PR review using domain experts:
1. Check which experts have relevant expertise for the PR changes
2. Have relevant experts perform deep code review
3. Iteratively improve the PR based on feedback until all experts approve


## Steps in Order

1. **check_relevance** - Invoke all experts in parallel to assess if PR changes are relevant to their domain
2. **deep_review** - Invoke only relevant experts to perform detailed code review
3. **improve_and_rereview** - Apply expert feedback and re-run reviews until no further feedback or 3 iterations

**Start workflow**: `/experts.check_relevance`

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/experts.review_pr` to determine user intent:
- "check_relevance" or related terms → run step `experts.check_relevance`
- "deep_review" or related terms → run step `experts.deep_review`
- "improve_and_rereview" or related terms → run step `experts.improve_and_rereview`
- No specific step mentioned → start at first step `experts.check_relevance`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: experts.check_relevance
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

- Workflow definition: `.deepwork/experts/experts/workflows/review_pr/workflow.yml`