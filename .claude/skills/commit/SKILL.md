---
name: commit
description: "Run tests, lint, and commit code changes"
---

# commit

**Multi-step workflow**: Run tests, lint, and commit code changes

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for preparing and committing code changes with quality checks.

This job ensures code quality before committing by running the test suite until
all tests pass, then formatting and linting with ruff. The lint step runs in a
sub-agent to reduce context usage. Finally, it reviews changed files with you
before creating the commit and pushing to the remote.


## Available Steps

1. **test** - Pull latest code and run the test suite until all tests pass
2. **lint** - Format and lint code with ruff using a sub-agent (requires: test)
3. **commit_and_push** - Review changed files, commit, and push to remote (requires: lint)

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