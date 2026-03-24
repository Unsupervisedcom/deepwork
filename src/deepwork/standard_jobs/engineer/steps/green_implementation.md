# Implement to Pass Tests

Implement the necessary logic, parameters, or configuration to transition all tests from
red to green. Keep PR checkboxes synchronized with progress throughout.

## Process

1. Review the implementation plan and test manifest to plan execution order
2. For each task:
   - Write the necessary changes
   - Run relevant tests to verify red-to-green transition
   - Commit: `feat(scope): implement [task description]`
   - Push to remote
   - **Immediately update the PR checkbox** for the completed task
3. Run the full test suite and confirm all tests pass
4. Verify all PR checkboxes reflect the current branch state

## Output Format

### .deepwork/tmp/implementation_summary.md

```markdown
# Implementation Summary

## Overview
- Tasks completed: [N]/[total]
- All tests green: yes/no

## Tasks

### Task 1: [task name]
- Requirement: Req [N]
- Changes: [files modified/created]
- Test result: PASS
- Commit: [sha]

## Test Output
[paste of test runner output showing all passes]

## PR State
- Checkboxes synchronized: yes/no
- Checked: [N]/[total]
- Divergences from plan: [none, or description]

## Commits
1. [sha] — [message]
```
