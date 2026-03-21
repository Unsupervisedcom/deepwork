---
name: merge_and_update
description: "Merge the current PR, wait for merge queue/checks to complete, then switch to main and pull"
---

# Merge and Update

Merge the current branch's PR, wait for it to land, then update local main.

## Steps

1. **Merge the PR** using `gh pr merge` with `--squash --delete-branch`. This will add it to the merge queue if one is configured.

2. **Wait for PR checks to complete** using `gh pr checks --watch --fail-fast`. This blocks until all PR-level checks finish or one fails.

3. **Wait for merge queue checks** — after the PR enters the merge queue, a separate `merge_group` workflow run is triggered. Find and watch it:
   ```
   run_id=$(gh run list --event merge_group --limit 1 --json databaseId -q '.[0].databaseId')
   gh run watch "$run_id" --exit-status
   ```
   If no merge queue run is found (repo doesn't use a merge queue), skip this step.

4. **Switch to main and pull**:
   ```
   git checkout main && git pull
   ```

5. Report the result to the user.

## Error handling

- If `gh pr merge` fails (e.g., no PR for current branch, merge conflicts), stop and report the error.
- If PR checks or merge queue checks fail, report which checks failed.
- If the PR was already merged, skip to step 4.
