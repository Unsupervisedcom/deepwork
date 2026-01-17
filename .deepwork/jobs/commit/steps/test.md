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
