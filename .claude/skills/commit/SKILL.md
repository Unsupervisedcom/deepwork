---
name: commit
description: "Reviews code, runs tests, lints, and commits changes. Use when ready to commit work with quality checks."
---

# commit Agent

Reviews code, runs tests, lints, and commits changes. Use when ready to commit work with quality checks.

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


## Agent Overview

This agent handles the **commit** job. It contains 4 skills that can be executed as part of workflows or standalone.

### Available Workflows

**full**: Full commit workflow: review, test, lint, and commit
- Steps: review → test → lint → commit_and_push
- Start with: `review`


---

## How to Use This Agent

### Option 1: Start a Workflow
Tell the agent which workflow to run:
- "Run the full workflow"
- "Start commit"
- "full" → starts at `review`

### Option 2: Run a Specific Skill
Request a specific skill by name:
- "review" - Reviews changed code for issues, DRY opportunities, naming clarity, and test coverage using a sub-agent. Use as the first step before testing.
- "test" - Pulls latest code and runs tests until all pass. Use after code review passes to verify changes work correctly.
- "lint" - Formats and lints code with ruff using a sub-agent. Use after tests pass to ensure code style compliance.
- "commit_and_push" - Verifies changed files, creates commit, and pushes to remote. Use after linting passes to finalize changes.

### Option 3: Let the Agent Decide
Describe what you want to accomplish, and the agent will select the appropriate skill(s).

---

## Agent Execution Instructions

When invoked, follow these steps:

### Step 1: Understand Intent

Parse the user's request to determine:
1. Which workflow or skill to execute
2. Any parameters or context provided
3. Whether this is a continuation of previous work

**Workflow Detection**:
- Keywords like "full", "full commit workflow: review, " → Start `full` workflow at `review`


### Step 2: Check Work Branch

Before executing any skill:
1. Check current git branch
2. If on a `deepwork/commit-*` branch: continue using it
3. If on main/master: create new branch `deepwork/commit-[instance]-$(date +%Y%m%d)`

### Step 3: Execute the Appropriate Skill

Navigate to the relevant skill section below and follow its instructions.

### Step 4: Workflow Continuation

After completing a workflow step:
1. Inform the user of completion and outputs created
2. Automatically proceed to the next step in the workflow
3. Continue until the workflow is complete or the user intervenes

**Workflow sequences**:
- **full**: review → test → lint → commit_and_push

---

## Skills

### Skill: review

**Type**: Workflow step 1/4 in **full**

**Description**: Reviews changed code for issues, DRY opportunities, naming clarity, and test coverage using a sub-agent. Use as the first step before testing.




#### Instructions

# Code Review

## Objective

Review changed code for quality issues before running tests. This catches problems early and ensures code meets quality standards.

## Task

Use a sub-agent to review the staged/changed code and identify issues that should be fixed before committing.

### Process

**IMPORTANT**: Use the Task tool to spawn a sub-agent for this review. This saves context in the main conversation.

1. **Get the list of changed files**
   ```bash
   git diff --name-only HEAD
   git diff --name-only --staged
   ```
   Combine these to get all files that have been modified.

2. **Spawn a sub-agent to review the code**

   Use the Task tool with these parameters:
   - `subagent_type`: "general-purpose"
   - `prompt`: Instruct the sub-agent to:
     - Read the code review standards from `doc/code_review_standards.md`
     - Read each of the changed files
     - Review each file against the standards
     - Report issues found with file, line number, severity, and suggested fix

3. **Review sub-agent findings**
   - Examine each issue identified
   - Prioritize issues by severity

4. **Fix identified issues**
   - Address each issue found by the review
   - For DRY violations: extract shared code into functions/modules
   - For naming issues: rename to be clearer
   - For missing tests: add appropriate test cases
   - For bugs: fix the underlying issue

5. **Re-run review if significant changes made**
   - If you made substantial changes, consider running another review pass
   - Ensure fixes didn't introduce new issues

## Quality Criteria

- Changed files were identified
- Sub-agent read the code review standards and reviewed all changed files
- All identified issues were addressed or documented as intentional

## Context

This is the first step of the commit workflow. Code review happens before tests to catch quality issues early. The sub-agent approach keeps the main conversation context clean while providing thorough review coverage.


#### Outputs

Create these files/directories:
- `code_reviewed`
#### Quality Validation

Before completing this skill, verify:
1. Changed files were identified
2. Sub-agent reviewed the code for general issues, DRY opportunities, naming clarity, and test coverage
3. All identified issues were addressed or documented as intentional

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "review complete, outputs: code_reviewed"
3. **Continue to next skill**: Proceed to `test`

---

### Skill: test

**Type**: Workflow step 2/4 in **full**

**Description**: Pulls latest code and runs tests until all pass. Use after code review passes to verify changes work correctly.

#### Prerequisites

Before running this skill, ensure these are complete:
- `review`



#### Instructions

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
- All tests are passing

## Context

This step runs after code review. Tests must pass before proceeding to lint and commit. This ensures code quality and prevents broken code from being committed. If tests fail due to issues introduced by the code review fixes, iterate on the fixes until tests pass.


#### Outputs

Create these files/directories:
- `tests_passing`
#### Quality Validation

Before completing this skill, verify:
1. Latest code was pulled from the branch
2. All tests are passing

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "test complete, outputs: tests_passing"
3. **Continue to next skill**: Proceed to `lint`

---

### Skill: lint

**Type**: Workflow step 3/4 in **full**

**Description**: Formats and lints code with ruff using a sub-agent. Use after tests pass to ensure code style compliance.

#### Prerequisites

Before running this skill, ensure these are complete:
- `test`



#### Instructions

# Lint Code

## Objective

Format and lint the codebase using ruff to ensure code quality and consistency.

## Task

Run ruff format and ruff check to format and lint the code. This step should be executed using a sub-agent to conserve context in the main conversation.

### Process

**IMPORTANT**: Use the Task tool to spawn a sub-agent for this work. This saves context in the main conversation. Use the `haiku` model for speed.

1. **Spawn a sub-agent to run linting**

   Use the Task tool with these parameters:
   - `subagent_type`: "Bash"
   - `model`: "haiku"
   - `prompt`: See below

   The sub-agent should:

   a. **Run ruff format**
      ```bash
      ruff format .
      ```
      This formats the code according to ruff's style rules.

   b. **Run ruff check with auto-fix**
      ```bash
      ruff check --fix .
      ```
      This checks for lint errors and automatically fixes what it can.

   c. **Run ruff check again to verify**
      ```bash
      ruff check .
      ```
      Capture the final output to verify no remaining issues.

2. **Review sub-agent results**
   - Check that both format and check completed successfully
   - Note any remaining lint issues that couldn't be auto-fixed

3. **Handle remaining issues**
   - If there are lint errors that couldn't be auto-fixed, fix them manually
   - Re-run ruff check to verify

## Example Sub-Agent Prompt

```
Run ruff to format and lint the codebase:

1. Run: ruff format .
2. Run: ruff check --fix .
3. Run: ruff check . (to verify no remaining issues)

Report the results of each command.
```

## Quality Criteria

- ruff format was run successfully
- ruff check was run with --fix flag
- No remaining lint errors

## Context

This step ensures code quality and consistency before committing. It runs after tests pass and before the commit step. Using a sub-agent keeps the main conversation context clean for the commit review.


#### Outputs

Create these files/directories:
- `code_formatted`
#### Quality Validation

Before completing this skill, verify:
1. ruff format was run successfully
2. ruff check was run with --fix flag
3. No remaining lint errors

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "lint complete, outputs: code_formatted"
3. **Continue to next skill**: Proceed to `commit_and_push`

---

### Skill: commit_and_push

**Type**: Workflow step 4/4 in **full**

**Description**: Verifies changed files, creates commit, and pushes to remote. Use after linting passes to finalize changes.

#### Prerequisites

Before running this skill, ensure these are complete:
- `lint`



#### Instructions

# Commit and Push

## Objective

Review the changed files to verify they match the agent's expectations, create a commit with an appropriate message, and push to the remote repository.

## Task

Check the list of changed files against what was modified during this session, ensure they match expectations, then commit and push the changes.

### Process

1. **Get the list of changed files**
   ```bash
   git status
   ```
   Also run `git diff --stat` to see a summary of changes.

2. **Verify changes match expectations**

   Compare the changed files against what you modified during this session:
   - Do the modified files match what you edited?
   - Are there any unexpected new files?
   - Are there any unexpected deleted files?
   - Do the line counts seem reasonable for the changes you made?

   If changes match expectations, proceed to the next step.

   If there are unexpected changes:
   - Investigate why (e.g., lint auto-fixes, generated files)
   - If they're legitimate side effects of your work, include them
   - If they're unrelated or shouldn't be committed, use `git restore` to discard them

3. **Update CHANGELOG.md if needed**

   If your changes include new features, bug fixes, or other notable changes:
   - Add entries to the `## [Unreleased]` section of CHANGELOG.md
   - Use the appropriate subsection: `### Added`, `### Changed`, `### Fixed`, or `### Removed`
   - Write concise descriptions that explain the user-facing impact

   **CRITICAL: NEVER modify version numbers**
   - Do NOT change the version in `pyproject.toml`
   - Do NOT change version headers in CHANGELOG.md (e.g., `## [0.4.2]`)
   - Do NOT rename the `## [Unreleased]` section
   - Version updates are handled by the release workflow, not commits

4. **Stage all appropriate changes**
   ```bash
   git add -A
   ```
   Or stage specific files if some were excluded.

5. **View recent commit messages for style reference**
   ```bash
   git log --oneline -10
   ```

6. **Create the commit**

   Generate an appropriate commit message based on:
   - The changes made
   - The style of recent commits
   - Conventional commit format if the project uses it

   **IMPORTANT:** Use the commit job script (not `git commit` directly):
   ```bash
   .claude/hooks/commit_job_git_commit.sh -m "commit message here"
   ```

7. **Push to remote**
   ```bash
   git push
   ```
   If the branch has no upstream, use:
   ```bash
   git push -u origin HEAD
   ```

## Quality Criteria

- Changed files were verified against expectations
- CHANGELOG.md was updated with entries in [Unreleased] section (if changes warrant documentation)
- Version numbers were NOT modified (pyproject.toml version and CHANGELOG version headers unchanged)
- Commit was created with appropriate message
- Changes were pushed to remote

## Context

This is the final step of the commit workflow. The agent verifies that the changed files match its own expectations from the work done during the session, then commits and pushes. This catches unexpected changes while avoiding unnecessary user interruptions.


#### Outputs

Create these files/directories:
- `changes_committed`
#### Quality Validation

Before completing this skill, verify:
1. Changed files were verified against expectations
2. CHANGELOG.md was updated with entries in [Unreleased] section (if changes warrant documentation)
3. Version numbers were NOT modified (pyproject.toml version and CHANGELOG version headers unchanged)
4. Commit was created with appropriate message
5. Changes were pushed to remote

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "full workflow complete, outputs: changes_committed"
3. Consider creating a PR to merge the work branch

---

## Guardrails

- **Never skip prerequisites**: Always verify required steps are complete before running a skill
- **Never produce partial outputs**: Complete all required outputs before marking a skill done
- **Always use the work branch**: Never commit directly to main/master
- **Follow quality criteria**: Use sub-agent review when quality criteria are specified
- **Ask for clarification**: If user intent is unclear, ask before proceeding

## Context Files

- Job definition: `.deepwork/jobs/commit/job.yml`
- review instructions: `.deepwork/jobs/commit/steps/review.md`
- test instructions: `.deepwork/jobs/commit/steps/test.md`
- lint instructions: `.deepwork/jobs/commit/steps/lint.md`
- commit_and_push instructions: `.deepwork/jobs/commit/steps/commit_and_push.md`
