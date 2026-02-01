---
name: review_pr
description: "Coordinates expert-driven PR review with iterative improvement cycles until all feedback is addressed."
---

# review_pr

Coordinates expert-driven PR review with iterative improvement cycles until all feedback is addressed.

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A multi-phase workflow for comprehensive pull request review using domain experts.

The workflow operates in three phases:
1. **Relevance Check**: All available experts examine the PR changes in parallel to determine
   if any changes fall within their domain of expertise.
2. **Deep Review**: Experts who found relevant changes perform detailed code review, producing
   written feedback and specific code change suggestions.
3. **Improvement Cycle**: The PR is improved based on feedback, then re-reviewed by the same
   experts. This cycle repeats until all experts report no further feedback or 3 iterations
   are reached.

Produces:
- Relevance assessments from all experts
- Detailed review feedback with code suggestions
- Iteratively improved PR code

Requires: PR branch checked out, `gh` CLI available for PR metadata


## Workflows

### full

Full PR review: relevance check, deep review, and improvement cycles

**Steps in order**:
1. **check_relevance** - Invokes all available experts in parallel to assess if PR changes are relevant to their domain. Use at the start of a PR review.
2. **deep_review** - Invokes only relevant experts (from previous step) to perform detailed code review. Use after relevance check identifies applicable experts.
3. **improve_and_rereview** - Applies expert feedback to improve the PR, then re-runs expert reviews. Cycles until no further feedback or 3 iterations. Use after deep review completes.

**Start workflow**: `/review_pr.check_relevance`


## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/review_pr` to determine user intent:
- "full" or related terms → start full workflow at `review_pr.check_relevance`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: review_pr.check_relevance
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the workflow sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

**Note**: Standalone skills do not auto-continue to other steps.

### Handling Ambiguous Intent

If user intent is unclear, ask which option they want:
- Present available workflows and standalone skills as options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in a workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/review_pr/job.yml`