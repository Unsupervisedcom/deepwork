# Write Failing Tests

## Objective

Implement new failing (red) tests or verify existing tests against the new requirements.
Each test must explicitly reference a specific requirement from the engineering issue.

## Task

Establish the test-driven development boundary. All tests must exist and fail before any
implementation code is written. This ensures requirements drive the implementation, not
the other way around.

### Process

1. **Review the engineering issue's test definitions**
   - Read the test definitions table from `engineering_issue.md`
   - Identify which tests need to be created vs. which existing tests can be reused
   - Confirm the test framework and conventions from agent.md

2. **Implement or verify tests**
   - For each requirement, either:
     - Write a new failing test that validates the requirement
     - Verify an existing test covers the requirement and would fail without the new implementation
   - Each test MUST include a comment or annotation referencing the specific requirement
     (e.g., `# Req 3: Each test must reference a specific requirement`)

3. **Verify red state**
   - Run the test suite and confirm all new/modified tests fail
   - Capture the test output showing the failures
   - If any test unexpectedly passes, investigate — it may indicate the requirement is already met

4. **Commit the failing tests**
   - Commit tests separately from implementation: `test(scope): add failing tests for #[issue-number]`
   - Push to the remote branch
   - Update PR checkboxes for test-related tasks

5. **Create the test manifest**
   - Document each test, its requirement reference, and its red state verification

### Domain Adaptation

| Concept          | Software              | Hardware/CAD           | Firmware              | Docs                 |
|------------------|-----------------------|------------------------|-----------------------|----------------------|
| Test file        | `test_*.py`, `*.test.ts` | DRC rule file        | `test_*.c`, HIL script | `linkcheck.py`, lint config |
| Test runner      | pytest, jest, cargo   | KiCad DRC, FreeCAD    | ceedling, Unity       | sphinx linkcheck, markdownlint |
| Req reference    | Docstring/comment     | Rule comment           | Test name/comment     | Config comment       |
| Red state        | Test fails            | DRC violation          | Assert fails          | Link broken/lint error |

## Output Format

### .deepwork/tmp/test_manifest.md

**Structure**:
```markdown
# Test Manifest

## Test Suite Summary
- Framework: [test framework]
- Total new tests: [N]
- Total verified existing tests: [N]
- Red state confirmed: yes/no

## Test Details

| # | Test | File | Requirement | Type | Red State |
|---|------|------|-------------|------|-----------|
| 1 | [test name] | [file:line] | Req [N] | new | FAIL: [failure reason] |
| 2 | [test name] | [file:line] | Req [N] | existing | FAIL: [failure reason] |

## Test Output
```
[paste of test runner output showing failures]
```

## Commits
- Test commit: [sha] — [commit message]
```

## Quality Criteria

- Every requirement from the engineering issue has at least one test
- All new tests fail (red state) before implementation begins
- Each test references its requirement explicitly in code
- Tests were committed as a separate commit from implementation
- Test manifest accurately reflects the current state
