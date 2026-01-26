# Run Tests

## Objective

Run the project's test suite and fix any failing tests until all tests pass.

## Task

Execute the test suite for the project and iteratively fix any failures until all tests pass.

### Process

1. **Pull latest code from the branch**
   - Run `git pull` to fetch and merge any changes from the remote
   - If there are merge conflicts, resolve them before proceeding
   - This ensures you're testing against the latest code

2. **Run the test command**
   ```bash
   [test command]
   ```
   Capture the output.

3. **Analyze failures**
   - If tests pass, proceed to output
   - If tests fail, analyze the failure messages
   - Identify the root cause of each failure

4. **Fix failing tests**
   - Make the necessary code changes to fix failures
   - This may involve fixing bugs in implementation code or updating tests
   - Re-run tests after each fix

5. **Iterate until passing**
   - Continue the fix/test cycle until all tests pass

## Quality Criteria

- Latest code was pulled from the branch
- All tests are passing

## Context

This step runs after code review. Tests must pass before proceeding to lint and commit. This ensures code quality and prevents broken code from being committed. If tests fail due to issues introduced by the code review fixes, iterate on the fixes until tests pass.
