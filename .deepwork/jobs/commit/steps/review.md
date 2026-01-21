# Code Review

## Objective

Review changed code for quality issues before running tests. This catches problems early and ensures code meets quality standards.

## Task

Use a sub-agent to review the staged/changed code and identify issues that should be fixed before committing.

### Process

**IMPORTANT**: Use the Task tool to spawn a sub-agent for this review. This saves context in the main conversation.

1. **Get the list of changed files**
   ```bash
   git diff --name-only HEAD
   git diff --name-only --staged
   ```
   Combine these to get all files that have been modified.

2. **Spawn a sub-agent to review the code**

   Use the Task tool with these parameters:
   - `subagent_type`: "general-purpose"
   - `prompt`: Include the list of changed files and the review criteria below

   The sub-agent should review each changed file for:

   **General Issues**
   - Logic errors or potential bugs
   - Error handling gaps
   - Security concerns
   - Performance issues

   **DRY Opportunities**
   - Duplicated code that should be extracted into functions
   - Repeated patterns that could be abstracted
   - Copy-pasted logic with minor variations

   **Naming Clarity**
   - Variables, functions, and classes should have clear, descriptive names
   - Names should reflect purpose and intent
   - Avoid abbreviations that aren't universally understood
   - Consistent naming conventions throughout

   **Test Coverage**
   - New functions or classes should have corresponding tests
   - New code paths should be tested
   - Edge cases should be covered
   - If tests are missing, note what should be tested

3. **Review sub-agent findings**
   - Examine each issue identified
   - Prioritize issues by severity

4. **Fix identified issues**
   - Address each issue found by the review
   - For DRY violations: extract shared code into functions/modules
   - For naming issues: rename to be clearer
   - For missing tests: add appropriate test cases
   - For bugs: fix the underlying issue

5. **Re-run review if significant changes made**
   - If you made substantial changes, consider running another review pass
   - Ensure fixes didn't introduce new issues

## Example Sub-Agent Prompt

```
Review the following changed files for code quality issues:

Files to review:
- src/module.py
- src/utils.py
- tests/test_module.py

For each file, check for:

1. **General issues**: Logic errors, bugs, error handling gaps, security concerns
2. **DRY opportunities**: Duplicated code, repeated patterns that should be extracted
3. **Naming clarity**: Are variable/function/class names clear and descriptive?
4. **Test coverage**: Does new functionality have corresponding tests?

Read each file and provide a structured report of issues found, organized by category.
For each issue, include:
- File and line number
- Description of the issue
- Suggested fix

If no issues are found in a category, state that explicitly.
```

## Quality Criteria

- Changed files were identified
- Sub-agent reviewed all changed files
- Issues were categorized (general, DRY, naming, tests)
- All identified issues were addressed or documented as intentional
- Sub-agent was used to conserve context
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the first step of the commit workflow. Code review happens before tests to catch quality issues early. The sub-agent approach keeps the main conversation context clean while providing thorough review coverage.
