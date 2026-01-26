# Lint Code

## Objective

Format and lint the codebase to ensure code quality and consistency.

## Task

Run the project's format and lint commands. This step should be executed using a sub-agent to conserve context in the main conversation.

### Process

**IMPORTANT**: Use the Task tool to spawn a sub-agent for this work. This saves context in the main conversation. Use the `haiku` model for speed.

1. **Spawn a sub-agent to run linting**

   Use the Task tool with these parameters:
   - `subagent_type`: "Bash"
   - `model`: "haiku"
   - `prompt`: See below

   The sub-agent should:

   a. **Run the format command**
      ```bash
      [lint and format command]
      ```
      This formats the code according to the project's style rules.

   b. **Run the lint check command**
      ```bash
      [lint and format command]
      ```
      This checks for lint errors.

   c. **Run lint check again to verify**
      Capture the final output to verify no remaining issues.

2. **Review sub-agent results**
   - Check that both format and check completed successfully
   - Note any remaining lint issues that couldn't be auto-fixed

3. **Handle remaining issues**
   - If there are lint errors that couldn't be auto-fixed, fix them manually
   - Re-run lint check to verify

## Example Sub-Agent Prompt

```
Run the lint and format commands for the codebase:

1. Run: [lint and format command]
2. Run: [lint check command]
3. Verify no remaining issues

Report the results of each command.
```

## Quality Criteria

- Format command was run successfully
- Lint check was run successfully
- No remaining lint errors (or all are documented and intentional)
- Sub-agent was used to conserve context
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This step ensures code quality and consistency before committing. It runs after tests pass and before the commit step. Using a sub-agent keeps the main conversation context clean for the commit review.
