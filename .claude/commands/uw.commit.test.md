---
description: Run pytest and fix any failures until all tests pass (max 5 attempts)
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/jobs/commit/hooks/run_tests.sh"
---

# commit.test

**Step 1 of 3** in the **commit** workflow

**Summary**: Validate, format, and push changes with tests passing

## Job Overview

A pre-commit workflow that ensures code quality before pushing changes.

This job runs through three validation and preparation steps:
1. Runs the test suite and fixes any failures until all tests pass (max 5 attempts)
2. Runs ruff formatting and linting, fixing issues until clean (max 5 attempts)
3. Fetches from remote, rebases if needed, generates a simple commit message,
   commits changes, and pushes to the remote branch

Each step uses a quality validation loop to ensure it completes successfully
before moving to the next step. The format step runs as a subagent to
minimize token usage.

Key behaviors:
- Rebase strategy when remote has changes (keeps linear history)
- Simple summary commit messages (no conventional commits format)
- Maximum 5 fix attempts before stopping

Designed for developers who want a reliable pre-push workflow that catches
issues early and ensures consistent code quality.



## Instructions

# Run Tests

## Objective

Run the project test suite and fix any failing tests until all tests pass (maximum 5 attempts).

## Task

Execute pytest to run all tests. If any tests fail, analyze the failures and fix them. Continue this cycle until all tests pass or you've made 5 fix attempts.

### Process

1. **Run the test suite**
   ```bash
   uv run pytest tests/ -v
   ```

2. **Analyze test results**
   - If all tests pass, you're done with this step
   - If tests fail, examine the failure output carefully

3. **Fix failing tests** (if needed)
   - Read the failing test to understand what it's testing
   - Read the relevant source code
   - Determine if the issue is in the test or the implementation
   - Make the minimal fix needed to pass the test
   - Re-run tests to verify the fix

4. **Repeat if necessary**
   - Continue the fix cycle until all tests pass
   - Track your attempts - stop after 5 fix attempts if tests still fail
   - If you cannot fix after 5 attempts, report the remaining failures to the user

### Important Notes

- **Don't skip tests** - All tests must pass before proceeding
- **Minimal fixes** - Make the smallest change needed to fix each failure
- **Understand before fixing** - Read and understand failing tests before attempting fixes
- **Track attempts** - Keep count of fix attempts to respect the 5-attempt limit

## Output Format

No file output is required. Success is determined by all tests passing.

**On success**: Report that all tests pass and proceed to the next step.

**On failure after 5 attempts**: Report which tests are still failing and why you couldn't fix them.

## Quality Criteria

- All tests pass (`uv run pytest tests/ -v` exits with code 0)
- Any fixes made are minimal and don't break other functionality
- If tests couldn't be fixed in 5 attempts, clear explanation provided

## Hook Behavior

After you complete this step, a hook will automatically run `uv run pytest tests/ -v` and show you the results.

**Interpreting the hook output:**
- **All tests passed (exit code 0)**: The step is complete. Proceed to the next step.
- **Tests failed (exit code non-zero)**: You must fix the failing tests. Analyze the output, make fixes, and try again. The hook will re-run after each attempt.

**Important**: The hook runs automatically - you don't need to run pytest yourself after the initial run. Just focus on making fixes when tests fail, and the hook will verify your fixes.

## Context

This is the first step in the commit workflow. Tests must pass before code formatting is checked, ensuring that any changes being committed are functionally correct.



## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `deepwork/commit-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b deepwork/commit-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

## Output Requirements

No specific files are output by this command.

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.


**Validation Script**: `.deepwork/jobs/commit/hooks/run_tests.sh`

The validation script will be executed automatically when you attempt to complete this step.

### Completion Promise

To signal that all quality criteria have been met, include this tag in your final response:

```
<promise>✓ Quality Criteria Met</promise>
```

**Important**: Only include this promise tag when you have verified that ALL quality criteria above are satisfied. The validation loop will continue until this promise is detected.

## Completion

After completing this step:

1. **Verify outputs**: Confirm all required files have been created

2. **Inform the user**:
   - Step 1 of 3 is complete
   - Ready to proceed to next step: `/commit.format`

## Next Step

To continue the workflow, run:
```
/commit.format
```

---

## Context Files

- Job definition: `.deepwork/jobs/commit/job.yml`
- Step instructions: `.deepwork/jobs/commit/steps/test.md`