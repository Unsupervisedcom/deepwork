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

2. **Detect or use the test command**
   - If a test command was provided, use that
   - Otherwise, auto-detect the project type and determine the appropriate test command:
     - Python: `pytest`, `python -m pytest`, `uv run pytest`
     - Node.js: `npm test`, `yarn test`, `bun test`
     - Go: `go test ./...`
     - Rust: `cargo test`
     - Check `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` for hints

3. **Run the tests**
   - Execute the test command
   - Capture the output

4. **Analyze failures**
   - If tests pass, proceed to output
   - If tests fail, analyze the failure messages
   - Identify the root cause of each failure

5. **Fix failing tests**
   - Make the necessary code changes to fix failures
   - This may involve fixing bugs in implementation code or updating tests
   - Re-run tests after each fix

6. **Iterate until passing**
   - Continue the fix/test cycle until all tests pass
   - Document what was fixed

## Output Format

### test_results.md

A summary of the test run and any fixes made.

**Structure**:
```markdown
# Test Results

## Final Status
[PASSING/FAILING]

## Test Command
`[command used]`

## Summary
- Total tests: [N]
- Passed: [N]
- Failed: [N]

## Fixes Made
[List any code changes made to fix failing tests, or "None - all tests passed initially"]

## Test Output
```
[Final test output]
```
```

## Quality Criteria

- Latest code was pulled from the branch
- Test command was correctly identified or used from input
- All tests are now passing
- Any fixes made are documented
- Test output is captured in the results file
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the first step of the commit workflow. Tests must pass before proceeding to lint and commit. This ensures code quality and prevents broken code from being committed.
