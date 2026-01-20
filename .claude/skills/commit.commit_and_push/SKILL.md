---
name: commit.commit_and_push
description: "Review changed files, commit, and push to remote"
user-invocable: false
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Verify the commit is ready:
            1. Changed files list was reviewed with user
            2. User confirmed the files match expectations
            3. Commit was created with appropriate message
            4. Changes were pushed to remote
            If ALL criteria are met, include `<promise>✓ Quality Criteria Met</promise>`.

---

# commit.commit_and_push

**Step 3/3** in **commit** workflow

> Run tests, lint, and commit code changes

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/commit.lint`

## Instructions

**Goal**: Review changed files, commit, and push to remote

# Commit and Push

## Objective

Review the changed files with the user, create a commit with an appropriate message, and push to the remote repository.

## Task

Present the list of changed files for user review, ensure they match expectations, then commit and push the changes.

### Process

1. **Get the list of changed files**
   ```bash
   git status
   ```
   Also run `git diff --stat` to see a summary of changes.

2. **Present changes to the user for review**

   Use the AskUserQuestion tool to ask structured questions about the changes:

   Show the user:
   - List of modified files
   - List of new files
   - List of deleted files
   - Summary of changes (lines added/removed)

   Ask them to confirm:
   - "Do these changed files match your expectations?"
   - Provide options: "Yes, proceed with commit" / "No, let me review first" / "No, some files shouldn't be included"

3. **Handle user response**

   - If user confirms, proceed to commit
   - If user wants to review first, wait for them to come back
   - If user says some files shouldn't be included, ask which files to exclude and use `git restore` or `git checkout` to unstage them

4. **Stage all appropriate changes**
   ```bash
   git add -A
   ```
   Or stage specific files if user excluded some.

5. **View recent commit messages for style reference**
   ```bash
   git log --oneline -10
   ```

6. **Create the commit**

   Generate an appropriate commit message based on:
   - The changes made
   - The style of recent commits
   - Conventional commit format if the project uses it

   ```bash
   git commit -m "commit message here"
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

- Changed files list was presented to user
- User explicitly confirmed the files match expectations
- Commit message follows project conventions
- Commit was created successfully
- Changes were pushed to remote
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the final step of the commit workflow. It ensures the user has reviewed and approved the changes before they are committed and pushed. This prevents accidental commits of unintended files or changes.


### Job Context

A workflow for preparing and committing code changes with quality checks.

This job runs tests until they pass, formats and lints code with ruff,
then reviews changed files before committing and pushing. The lint step
uses a sub-agent to reduce context usage.

Steps:
1. test - Pull latest code and run tests until they pass
2. lint - Format and lint code with ruff (runs in sub-agent)
3. commit_and_push - Review changes and commit/push



## Work Branch

Use branch format: `deepwork/commit-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/commit-[instance]-$(date +%Y%m%d)`

## Outputs

No specific file outputs required.

## Quality Validation

Stop hooks will automatically validate your work. The loop continues until all criteria pass.



**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 3/3 complete"
3. **Workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/jobs/commit/job.yml`, `.deepwork/jobs/commit/steps/commit_and_push.md`