---
description: Fetch remote, rebase if needed, commit with simple summary message, and push
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. Did the agent fetch from the remote to check for updates?
            2. If there were remote changes, did the agent rebase local changes on top?
            3. Did the agent generate a simple summary commit message based on the changes?
            4. Did the agent commit the changes?
            5. Did the agent push to the remote branch?

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response AND
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met OR the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
---

# commit.reconcile_and_push

**Step 3 of 3** in the **commit** workflow

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


## Prerequisites

This step requires completion of the following step(s):
- `/commit.format`

Please ensure these steps have been completed before proceeding.

## Instructions

# Reconcile and Push

## Objective

Fetch the latest changes from the remote, rebase if necessary, generate a commit message, commit the changes, and push to the remote branch.

## Task

Ensure the local branch is up-to-date with the remote, commit all staged changes with a clear summary message, and push to the remote repository.

### Process

1. **Fetch from remote**
   ```bash
   git fetch origin
   ```

2. **Check for remote changes**
   ```bash
   git status
   ```
   Look for "Your branch is behind" or "Your branch and 'origin/...' have diverged"

3. **Rebase if needed**
   If the remote has changes that aren't in your local branch:
   ```bash
   git rebase origin/<branch-name>
   ```

   **If rebase conflicts occur**:
   - Resolve conflicts in the affected files
   - Stage resolved files: `git add <file>`
   - Continue rebase: `git rebase --continue`
   - If conflicts are too complex, abort and report to user: `git rebase --abort`

4. **Review changes to commit**
   ```bash
   git status
   git diff --staged
   git diff
   ```

   Stage any unstaged changes that should be committed:
   ```bash
   git add -A
   ```

5. **Generate commit message**
   Analyze the changes and create a **simple summary** commit message:
   - Look at the diff to understand what changed
   - Write a clear, concise description (1-2 sentences)
   - Focus on the "what" and "why", not the "how"
   - No conventional commits format needed - just a clear summary

   **Good commit messages**:
   - "Add user authentication with session management"
   - "Fix race condition in data processing pipeline"
   - "Update dependencies and fix compatibility issues"
   - "Refactor database queries for better performance"

6. **Commit the changes**
   ```bash
   git commit -m "<your commit message>"
   ```

7. **Push to remote**
   ```bash
   git push origin <branch-name>
   ```

   If push is rejected (remote has new changes), fetch and rebase again, then retry push.

### Handling Edge Cases

**No changes to commit**:
- If `git status` shows nothing to commit, inform the user and skip the commit/push

**Protected branch**:
- If push fails due to branch protection, inform the user they may need to create a PR

**Rebase conflicts**:
- Attempt to resolve simple conflicts
- For complex conflicts, abort the rebase and ask the user for guidance

**Diverged branches**:
- Always use rebase (not merge) to maintain linear history
- If rebase fails repeatedly, report the issue to the user

## Output Format

No file output is required. Success is determined by successfully pushing to the remote.

**On success**: Report the commit hash and confirm the push succeeded.

**On failure**: Report what went wrong (conflicts, push rejection, etc.) and suggest next steps.

## Quality Criteria

- Fetched latest changes from remote
- Rebased on top of remote changes if any existed
- Generated a clear, simple summary commit message
- Successfully committed all changes
- Successfully pushed to the remote branch
- When all steps complete successfully, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the final step in the commit workflow. By this point, tests pass and code is formatted. This step ensures your changes are properly committed with a good message and pushed to share with the team. The rebase strategy keeps the git history linear and clean.



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

### Quality Criteria

1. Did the agent fetch from the remote to check for updates?
2. If there were remote changes, did the agent rebase local changes on top?
3. Did the agent generate a simple summary commit message based on the changes?
4. Did the agent commit the changes?
5. Did the agent push to the remote branch?


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
   - Step 3 of 3 is complete
   - This is the final step - the job is complete!

## Workflow Complete

This is the final step in the commit workflow. All outputs should now be complete and ready for review.

Consider:
- Reviewing all work products
- Creating a pull request to merge the work branch
- Documenting any insights or learnings

---

## Context Files

- Job definition: `.deepwork/jobs/commit/job.yml`
- Step instructions: `.deepwork/jobs/commit/steps/reconcile_and_push.md`