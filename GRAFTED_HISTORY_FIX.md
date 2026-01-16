# Fix for Grafted Git History Issue

## Problem Identified

The repository was experiencing issues with "grafted history" which was causing new branches to start from the wrong place. Upon investigation, the following issues were found:

1. **Shallow Clone**: The repository contained a `.git/shallow` file, indicating it was a shallow clone
2. **Truncated History**: The git history was cut off at commit `e813b39bb4b8840df873239cc6371ad1a3dade64`
3. **Grafted Marker**: This commit was marked as "(grafted)" in git log output
4. **Missing Local Main**: No local main branch was present, only the remote tracking branch

## Root Cause

A shallow clone is a git clone operation that only fetches a limited commit history (typically just the latest commit or a specified number of commits). This creates a "grafted" history where the repository acts as if certain commits have no parents, even though they do in the remote repository. This causes:

- Incomplete history visibility
- Incorrect branch base points
- Potential merge and rebase issues
- Confusion about the actual state of the repository

## Solution Applied

The issue was resolved by running the following command:

```bash
git fetch origin main:main --unshallow
```

This command:
1. Fetches the complete git history from origin (not just the shallow history)
2. Creates a local `main` branch that tracks `origin/main`
3. Removes the `.git/shallow` file
4. Converts the repository from a shallow clone to a full clone

## Verification

After applying the fix, the following changes were verified:

### Before Fix
```
* d884c6b (HEAD -> copilot/fix-grafted-history-issue, origin/copilot/fix-grafted-history-issue) Initial plan
* e813b39 (grafted) Add update job for maintaining standard jobs (#41)
```
- Notice the "(grafted)" marker indicating truncated history
- Only 2 commits visible

### After Fix
```
* e813b39 (HEAD, main) Add update job for maintaining standard jobs (#41)
* ef29d3d Update tests to run on all pull requests (#51)
* 29df4d9 Configure workflows to run on merge queue and fix CLA for copilot PRs (#47)
* 08207ba Impt cla signatures (#49)
* 4dfdc2c Fix e2e CI test not running on PRs (#46)
* c14e5b1 Add full e2e test: define -> implement -> execute workflow (#45)
* c9bac58 Separate policy files for projects (#42)
* c95f3e5 Add automated tests for all scripts (#40)
... (many more commits)
```
- The "(grafted)" marker is gone
- Full commit history is now accessible
- Local main branch is properly created and updated

## Impact

With this fix:
- ✅ New branches will now start from the correct base commit
- ✅ Full git history is available for inspection
- ✅ Merge and rebase operations will work correctly
- ✅ Git commands will have access to the complete history
- ✅ No more "(grafted)" markers in git log

## Recommendations

To prevent this issue in the future:
1. Avoid using `git clone --depth=N` unless specifically needed for performance reasons
2. If a shallow clone is necessary, document it clearly in the project README
3. Run `git fetch --unshallow` as soon as full history is needed
4. Ensure CI/CD systems clone the full repository when branch operations are required
