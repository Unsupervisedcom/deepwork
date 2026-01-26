# Commit Job

A structured workflow for committing code changes with built-in quality checks.

## Overview

This job implements a comprehensive commit workflow that ensures code quality before every commit. Instead of allowing direct `git commit` commands, this job:

1. **Reviews** changed code for issues, DRY opportunities, naming clarity, and test coverage
2. **Tests** the code to ensure all tests pass
3. **Lints** the code to ensure consistent formatting and style
4. **Commits** and pushes only after all checks pass

## Why Hijack `git commit`?

The core design principle of this job is that **every commit should pass through quality checks**. To enforce this, we intercept `git commit` commands and redirect the agent to use the `/commit` skill instead.

Without this interception, an AI agent might:
- Commit code that hasn't been reviewed
- Push changes without running tests
- Skip linting, leading to inconsistent code style
- Bypass the structured workflow entirely

By blocking `git commit` and requiring the commit job's script, we guarantee that:
- Code is reviewed before testing (catching issues early)
- Tests pass before linting (no point linting broken code)
- Linting completes before committing (consistent style)
- All quality gates are passed before code reaches the repository

## IMPORTANT: REQUIRED CUSTOMIZATION

When installing this job to a new project, you must customize the following:

### 1. Replace `[test command]`

In `steps/test.md`, replace `[test command]` with your project's test command (e.g., `pytest`, `npm test`, `go test ./...`).

### 2. Replace `[format command]`

In `steps/lint.md`, replace `[format command]` with your project's code formatting command (e.g., `ruff format .`, `npx prettier --write .`, `go fmt ./...`).

### 3. Replace `[lint check command]`

In `steps/lint.md`, replace `[lint check command]` with your project's lint check command (e.g., `ruff check --fix .`, `npx eslint --fix .`, `golangci-lint run`).

### 4. Replace `[code review standards path]`

In `steps/review.md`, replace `[code review standards path]` with the path to your project's code review standards file (e.g., `docs/code_review_standards.md`).

If your project doesn't have a code review standards file yet, you can use the provided example as a starting point:

```bash
cp library/jobs/commit/code_review_standards.example.md docs/code_review_standards.md
```

Then customize `docs/code_review_standards.md` to match your project's specific requirements, coding style, and quality expectations.

### 5. Replace `[commit script path]`

In `steps/commit_and_push.md`, replace `[commit script path]` with the path to your commit wrapper script (e.g., `.deepwork/jobs/commit/commit_job_git_commit.sh`). See installation step 3 below for how to create this script.

## Installation

### 1. Copy the Job Folder

Copy this entire `commit` folder to your project's `.deepwork/jobs/` directory:

```bash
cp -r library/jobs/commit .deepwork/jobs/
```

### 2. Add the Hook Configuration to settings.json

Add a PreToolUse hook to your `.claude/settings.json` that blocks `git commit` and redirects to the commit skill. This is the key mechanism that enforces the commit workflow.

First, create the hook script at `.claude/hooks/block_bash_with_instructions.sh`:

```bash
#!/bin/bash
# block_bash_with_instructions.sh - Blocks specific bash commands and provides alternative instructions

set -e

BLOCKED_COMMANDS=(
    'git[[:space:]]+commit|||All commits must be done via the `/commit` skill. Do not use git commit directly. Instead, run `/commit` to start the commit workflow which includes code review, testing, and linting before committing.'
)

# Read stdin into variable
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Exit early if no input
if [ -z "${HOOK_INPUT}" ]; then
    exit 0
fi

# Extract tool_name from input
TOOL_NAME=$(echo "${HOOK_INPUT}" | jq -r '.tool_name // empty' 2>/dev/null)

# Only process Bash tool calls
if [ "${TOOL_NAME}" != "Bash" ]; then
    exit 0
fi

# Extract the command from tool_input
COMMAND=$(echo "${HOOK_INPUT}" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Exit if no command
if [ -z "${COMMAND}" ]; then
    exit 0
fi

# Check each blocked pattern
for entry in "${BLOCKED_COMMANDS[@]}"; do
    pattern="${entry%%|||*}"
    instructions="${entry##*|||}"

    if echo "${COMMAND}" | grep -qE "${pattern}"; then
        cat << EOF
{"error": "${instructions}"}
EOF
        exit 2
    fi
done

exit 0
```

Make it executable:
```bash
chmod +x .claude/hooks/block_bash_with_instructions.sh
```

Then add this to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block_bash_with_instructions.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. Create the Commit Wrapper Script

Create a wrapper script that the commit job will use to actually run `git commit`. This script bypasses the hook interception.

Create `.deepwork/jobs/commit/commit_job_git_commit.sh`:

```bash
#!/bin/bash
# commit_job_git_commit.sh - Wrapper for git commit invoked via the /commit skill

exec git commit "$@"
```

Make it executable:
```bash
chmod +x .deepwork/jobs/commit/commit_job_git_commit.sh
```

### 4. Allow the Commit Script in Permissions

Add the commit script to your allowed permissions in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(.deepwork/jobs/commit/commit_job_git_commit.sh:*)"
    ]
  }
}
```

### 5. Customize the Placeholders

Replace all placeholders in the step files as described in the "Required Customization" section above.

### 6. Sync the Skills

Run `deepwork sync` to generate the slash commands for your AI coding assistant.

## Workflow Steps

### 1. Code Review (`/commit.review`)

Uses a sub-agent to review changed files against the standards defined in your project's code review standards file. The example standards file checks for:
- General issues (bugs, security, performance)
- DRY opportunities (duplicated code)
- Naming clarity (descriptive names)
- Test coverage (missing tests)

### 2. Run Tests (`/commit.test`)

- Pulls latest code from the branch
- Runs the test suite
- Fixes any failing tests
- Iterates until all tests pass

### 3. Lint Code (`/commit.lint`)

Uses a sub-agent to:
- Format code according to project style
- Run lint checks
- Fix any auto-fixable issues

### 4. Commit and Push (`/commit.commit_and_push`)

- Reviews changed files against expectations
- Creates commit with appropriate message
- Pushes to remote repository

## Usage

Once installed and synced, simply run:

```
/commit
```

This will execute all steps in order. You can also run individual steps:

```
/commit.review
/commit.test
/commit.lint
/commit.commit_and_push
```
