---
name: commit
description: "Run tests, lint, and commit code changes"
---

# commit

**Multi-step workflow**: Run tests, lint, and commit code changes

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for preparing and committing code changes with quality checks.

This job runs tests until they pass, formats and lints code with ruff,
then reviews changed files before committing and pushing. The lint step
uses a sub-agent to reduce context usage.

Steps:
1. test - Pull latest code and run tests until they pass
2. lint - Format and lint code with ruff (runs in sub-agent)
3. commit_and_push - Review changes and commit/push


## Available Steps

1. **test** - Pull latest code and run the test suite until all tests pass
2. **lint** - Format and lint code with ruff using a sub-agent (requires: test)
3. **commit_and_push** - Verify changed files, commit, and push to remote (requires: lint)

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/commit` to determine user intent:
- "test" or related terms → start at `commit.test`
- "lint" or related terms → start at `commit.lint`
- "commit_and_push" or related terms → start at `commit.commit_and_push`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: commit.test
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available steps as numbered options
- Let user select the starting point

## Context Files

- Job definition: `.deepwork/jobs/commit/job.yml`