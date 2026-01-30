# Code Review Standards

This document defines the standards used during code review in the commit workflow.

## Review Categories

### General Issues

Check for:
- Logic errors or potential bugs
- Error handling gaps
- Security concerns (injection, authentication, authorization)
- Performance issues (inefficient algorithms, unnecessary computation)
- Resource leaks (unclosed files, connections)

### DRY (Don't Repeat Yourself)

Look for:
- Duplicated code that should be extracted into functions
- Repeated patterns that could be abstracted
- Copy-pasted logic with minor variations
- Similar code blocks that differ only in variable names

### Naming Clarity

Ensure:
- Variables, functions, and classes have clear, descriptive names
- Names reflect purpose and intent
- Abbreviations are avoided unless universally understood
- Naming conventions are consistent throughout the codebase

### Test Coverage

Verify:
- New functions or classes have corresponding tests
- New code paths are tested
- Edge cases are covered
- Error conditions are tested
- If tests are missing, note what should be tested

### Test Quality

Ensure tests add value and are not duplicative:
- Each test should verify a distinct behavior or scenario
- Tests should not duplicate what other tests already cover
- Test names should clearly describe what they're testing
- Tests should be meaningful, not just checking trivial cases
- Avoid testing implementation details; focus on behavior
- If multiple tests appear redundant, suggest consolidation

## Severity Levels

When reporting issues, categorize by severity:

- **Critical**: Must fix before commit (bugs, security issues)
- **High**: Should fix before commit (logic errors, missing error handling)
- **Medium**: Recommended to fix (DRY violations, unclear naming)
- **Low**: Nice to have (style improvements, minor optimizations)

## Review Output Format

For each issue found, provide:
1. File and line number
2. Severity level
3. Category (General/DRY/Naming/Tests)
4. Description of the issue
5. Suggested fix or improvement
