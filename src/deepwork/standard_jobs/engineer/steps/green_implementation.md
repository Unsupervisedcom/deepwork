# Implement to Pass Tests

## Objective

Implement the necessary logic, hardware parameters, or configuration changes to transition
all tests from red to green. Keep PR checkboxes synchronized with progress throughout.

## Task

Execute the implementation plan from the engineering issue, working test by test until the
entire suite passes. Maintain continuous state synchronization between the worktree and the
PR throughout.

### Process

1. **Review the implementation plan and test manifest**
   - Read the engineering issue's implementation plan
   - Read the test manifest to understand what each test expects
   - Plan the implementation order (dependencies between tasks may dictate sequence)

2. **Implement task by task**
   - For each implementation task:
     - Write the necessary code, configuration, or design changes
     - Run the relevant tests to verify they transition from red to green
     - Commit with a conventional commit message: `feat(scope): implement [task description]`
     - Push to the remote branch
     - **Immediately update the PR checkbox** for the completed task

3. **Verify all tests green**
   - Run the full test suite after all tasks are implemented
   - Capture the test output showing all tests passing
   - If any tests remain red, investigate and fix before proceeding

4. **Synchronize PR state**
   - Verify all PR checkboxes reflect the current branch state
   - Update the PR description if the implementation diverged from the original plan
   - Add a comment summarizing the implementation if noteworthy decisions were made

### Domain Adaptation

| Concept          | Software              | Hardware/CAD           | Firmware              | Docs                 |
|------------------|-----------------------|------------------------|-----------------------|----------------------|
| Implementation   | Code changes          | Schematic/model edits  | Register/driver code  | Content writing      |
| Green state      | Tests pass            | DRC clean              | Tests pass            | Links valid, lint clean |
| Commit granularity | Per logical change   | Per design change      | Per module            | Per section          |

## Output Format

### .deepwork/tmp/implementation_summary.md

**Structure**:
```markdown
# Implementation Summary

## Overview
- Total tasks: [N]
- Tasks completed: [N]
- All tests green: yes/no

## Implementation Details

### Task 1: [task name]
- Requirement: Req [N]
- Changes: [files modified/created]
- Test result: PASS
- Commit: [sha]
- PR checkbox: updated

### Task 2: [task name]
...

## Test Suite Output
```
[paste of test runner output showing all tests passing]
```

## PR State
- All checkboxes synchronized: yes/no
- Checkboxes checked: [N]/[total]
- Implementation divergences: [none, or description of changes from original plan]

## Commits (in order)
1. [sha] — [commit message]
2. [sha] — [commit message]
...
```

## Quality Criteria

- All tests from the test manifest have transitioned to green
- PR checkboxes are immediately updated as each task completes
- Each implementation change is committed and pushed individually
- No unrelated changes are included in the implementation
- The implementation follows the project's conventions from agent.md
