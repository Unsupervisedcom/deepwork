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
