---
name: commit.test
description: "Pull latest code and run the test suite until all tests pass"
user-invocable: false
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Verify the tests are passing:
            1. Latest code was pulled from the branch
            2. All tests completed successfully
            3. No test failures or errors remain
            4. Test output shows passing status
            If ALL criteria are met, include `<promise>✓ Quality Criteria Met</promise>`.

---

# commit.test

**Step 1/3** in **commit** workflow

> Run tests, lint, and commit code changes


## Instructions

**Goal**: Pull latest code and run the test suite until all tests pass

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

## Quality Criteria

- Latest code was pulled from the branch
- Test command was correctly identified or used from input
- All tests are now passing
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the first step of the commit workflow. Tests must pass before proceeding to lint and commit. This ensures code quality and prevents broken code from being committed.


### Job Context

A workflow for preparing and committing code changes with quality checks.

This job runs tests until they pass, formats and lints code with ruff,
then reviews changed files before committing and pushing. The lint step
uses a sub-agent to reduce context usage.

Steps:
1. test - Pull latest code and run tests until they pass
2. lint - Format and lint code with ruff (runs in sub-agent)
3. commit_and_push - Review changes and commit/push


## Required Inputs

**User Parameters** - Gather from user before starting:
- **test_command**: Test command to run (optional - will auto-detect if not provided)


## Work Branch

Use branch format: `deepwork/commit-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/commit-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `tests_passing`

## Quality Validation

Stop hooks will automatically validate your work. The loop continues until all criteria pass.



**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 1/3 complete, outputs: tests_passing"
3. **Continue workflow**: Use Skill tool to invoke `/commit.lint`

---

**Reference files**: `.deepwork/jobs/commit/job.yml`, `.deepwork/jobs/commit/steps/test.md`