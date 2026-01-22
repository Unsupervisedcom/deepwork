# Reset Manual Tests Environment

## Objective

Reset the manual tests environment by reverting all file changes and clearing the rules queue.

## Purpose

This step contains all the reset logic that other steps can call when they need to clean up between or after tests. It ensures consistent cleanup across all test steps.

## Reset Commands

Run these commands to reset the environment:

```bash
git reset HEAD manual_tests/ && git checkout -- manual_tests/ && rm -f manual_tests/test_created_mode/new_config.yml
deepwork rules clear_queue
```

## Command Explanation

- `git reset HEAD manual_tests/` - Unstages files from the index (rules_check uses `git add -A` which stages changes)
- `git checkout -- manual_tests/` - Reverts working tree to match HEAD
- `rm -f manual_tests/test_created_mode/new_config.yml` - Removes any new files created during tests (the created mode test creates this file)
- `deepwork rules clear_queue` - Clears the rules queue so rules can fire again (prevents anti-infinite-loop mechanism from blocking subsequent tests)

## When to Reset

- **After each serial test**: Reset immediately after observing the result to prevent cross-contamination
- **After parallel tests complete**: Reset once all parallel sub-agents have returned
- **On early termination**: Reset before reporting failure results
- **Before starting a new test step**: Ensure clean state

## Quality Criteria

- **All changes reverted**: `git status` shows no changes in `manual_tests/`
- **Queue cleared**: `.deepwork/tmp/rules/queue/` is empty
- **New files removed**: `manual_tests/test_created_mode/new_config.yml` does not exist
