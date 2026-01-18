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

## Output Format

### commit_summary.md

A summary of the commit.

**Structure**:
```markdown
# Commit Summary

## Changed Files
[List of files that were committed]

## Commit Details
- Hash: [commit hash]
- Message: [commit message]
- Branch: [branch name]

## Push Status
[Pushed to origin/branch-name]

## User Confirmation
[User confirmed changes matched expectations at: timestamp]
```

## Quality Criteria

- Changed files list was presented to user
- User explicitly confirmed the files match expectations
- Commit message follows project conventions
- Commit was created successfully
- Changes were pushed to remote
- Summary is captured in commit_summary.md
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the final step of the commit workflow. It ensures the user has reviewed and approved the changes before they are committed and pushed. This prevents accidental commits of unintended files or changes.
