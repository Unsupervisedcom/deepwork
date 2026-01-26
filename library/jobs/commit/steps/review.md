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

2. **Read the code review standards**

   First, read the project's code review standards file:
   ```
   [code review standards path]
   ```

3. **Spawn a sub-agent to review the code**

   Use the Task tool with these parameters:
   - `subagent_type`: "general-purpose"
   - `prompt`: Include the list of changed files and the review standards from the file above

   The sub-agent should review each changed file against the standards defined in your project's code review standards file.

4. **Review sub-agent findings**
   - Examine each issue identified
   - Prioritize issues by severity

5. **Fix identified issues**
   - Address each issue found by the review
   - For DRY violations: extract shared code into functions/modules
   - For naming issues: rename to be clearer
   - For missing tests: add appropriate test cases
   - For bugs: fix the underlying issue

6. **Re-run review if significant changes made**
   - If you made substantial changes, consider running another review pass
   - Ensure fixes didn't introduce new issues

## Example Sub-Agent Prompt

```
Review the following changed files for code quality issues.

Files to review:
- src/module.py
- src/utils.py
- tests/test_module.py

Use the code review standards defined in [code review standards path].

Read each file and provide a structured report of issues found, organized by the categories in the standards file.
For each issue, include:
- File and line number
- Severity level
- Category
- Description of the issue
- Suggested fix

If no issues are found in a category, state that explicitly.
```

## Quality Criteria

- Changed files were identified
- Code review standards file was read
- Sub-agent reviewed all changed files against the standards
- All identified issues were addressed or documented as intentional
- Sub-agent was used to conserve context
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the first step of the commit workflow. Code review happens before tests to catch quality issues early. The sub-agent approach keeps the main conversation context clean while providing thorough review coverage.
