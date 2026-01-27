---
name: commit
description: "Reviews code, runs tests, lints, and commits changes. Use when ready to commit work with quality checks."
---

# commit

Reviews code, runs tests, lints, and commits changes. Use when ready to commit work with quality checks.

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for preparing and committing code changes with quality checks.

The **full** workflow starts with a code review to catch issues early, runs tests until
they pass, formats and lints code with ruff, then reviews changed files
before committing and pushing. The review and lint steps use sub-agents
to reduce context usage.

Steps:
1. review - Code review for issues, DRY opportunities, naming, and test coverage (runs in sub-agent)
2. test - Pull latest code and run tests until they pass
3. lint - Format and lint code with ruff (runs in sub-agent)
4. commit_and_push - Review changes and commit/push


## Workflows

### full

Full commit workflow: review, test, lint, and commit

**Steps in order**:
1. **review** - Reviews changed code for issues, DRY opportunities, naming clarity, and test coverage using a sub-agent. Use as the first step before testing.
2. **test** - Pulls latest code and runs tests until all pass. Use after code review passes to verify changes work correctly.
3. **lint** - Formats and lints code with ruff using a sub-agent. Use after tests pass to ensure code style compliance.
4. **commit_and_push** - Verifies changed files, creates commit, and pushes to remote. Use after linting passes to finalize changes.

**Start workflow**: `/commit.review`


## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/commit` to determine user intent:
- "full" or related terms → start full workflow at `commit.review`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: commit.review
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the workflow sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

**Note**: Standalone skills do not auto-continue to other steps.

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available workflows and standalone skills as options
- Let user select the starting point

## Guardrails

- Do NOT copy/paste step instructions directly; always use the Skill tool to invoke steps
- Do NOT skip steps in a workflow unless the user explicitly requests it
- Do NOT proceed to the next step if the current step's outputs are incomplete
- Do NOT make assumptions about user intent; ask for clarification when ambiguous

## Context Files

- Job definition: `.deepwork/jobs/commit/job.yml`