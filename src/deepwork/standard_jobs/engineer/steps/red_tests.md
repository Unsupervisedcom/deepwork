# Write Failing Tests

Implement new failing (red) tests or verify existing tests against the new requirements.
Each test MUST reference a specific requirement from the engineering issue. All tests MUST
fail before any implementation begins.

## Process

1. Review the test definitions from `engineering_issue.md` — identify which tests to create vs. reuse
2. For each requirement, write a new failing test or verify an existing test covers it
   - Include a comment or annotation referencing the requirement (e.g., `# Req 3: ...`)
3. Run the test suite and confirm all new/modified tests fail; investigate any unexpected passes
4. Commit tests separately from implementation: `test(scope): add failing tests for #[issue-number]`
5. Push to the remote branch and update PR checkboxes for test-related tasks

## Output Format

### .deepwork/tmp/test_manifest.md

```markdown
# Test Manifest

## Summary
- Framework: [test framework]
- New tests: [N]
- Verified existing: [N]
- Red state confirmed: yes/no

## Tests

| # | Test | File | Requirement | Type | Red State |
|---|------|------|-------------|------|-----------|
| 1 | [test name] | [file:line] | Req [N] | new | FAIL: [reason] |
| 2 | [test name] | [file:line] | Req [N] | existing | FAIL: [reason] |

## Test Output
[paste of test runner output showing failures]

## Commits
- [sha] — [commit message]
```
