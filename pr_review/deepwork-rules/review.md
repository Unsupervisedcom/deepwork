# deepwork-rules Review

**PR**: #197
**Date**: 2026-02-01
**Reviewer**: deepwork-rules expert

## Summary

This PR performs a significant architectural restructuring of the DeepWork rules system. The changes migrate `deepwork_rules` from a "standard job" under `src/deepwork/standard_jobs/` to a "standard expert" under `src/deepwork/standard/experts/`. The migration involves:

1. **Directory relocation**: Moving from `standard_jobs/deepwork_rules/` to `standard/experts/deepwork_rules/`
2. **Schema change**: Converting from `job.yml` format to `workflow.yml` format, with workflows nested under the expert structure
3. **Naming convention update**: The skill name changed from `deepwork_rules.define` to `deepwork-rules.define` (underscores to dashes)
4. **Instruction update**: Removing reference to `AskUserQuestion` tool in favor of simpler "ask questions one at a time" guidance

From a rules system perspective, the core functionality (detection modes, pattern syntax, comparison modes, hooks) remains intact and well-documented. The rules themselves in `.deepwork/rules/` continue to work the same way.

## Issues Found

### Issue 1
- **File**: `src/deepwork/standard/experts/deepwork_rules/workflows/define/steps/define.md`
- **Line(s)**: 9
- **Severity**: Minor
- **Issue**: The instruction text "Ask questions one at a time - present a question, wait for the user's response, then ask the next. Do not output all questions as a list." is less explicit than the previous `AskUserQuestion` tool reference. While the previous version referenced a specific tool that may no longer exist, the new wording could be more precise about the expected UX pattern.
- **Suggestion**: Consider whether this instruction achieves the desired interaction pattern. If Claude Code has an `AskUserQuestion` tool or similar mechanism, referencing it directly would provide clearer guidance. If no such tool exists, the current wording is acceptable but could benefit from mentioning that the agent should use natural conversational turn-taking.

### Issue 2
- **File**: `src/deepwork/standard/experts/deepwork_rules/expert.yml`
- **Line(s)**: 67 (end of file)
- **Severity**: Minor
- **Issue**: The `full_expertise` field provides a good overview of rules but lacks documentation about the `action` field in rules (e.g., `action: command` for running shell commands like `uv sync` when `pyproject.toml` changes). The old `job.yml` description mentioned this feature: "Command action rules: Execute their command (e.g., `uv sync`) when the agent stops".
- **Suggestion**: Add documentation about command-action rules to the `full_expertise` section. This is an important feature that allows rules to execute shell commands rather than just prompting the agent.

### Issue 3
- **File**: `src/deepwork/standard/experts/deepwork_rules/workflows/define/steps/define.md`
- **Line(s)**: 103-143 (Step 6 section)
- **Severity**: Minor
- **Issue**: The rule file format examples do not document the `action` field for command-based rules. Users cannot learn how to create rules that automatically run commands (like `uv sync`) when certain files change.
- **Suggestion**: Add an example for command-action rules.

### Issue 4
- **File**: `src/deepwork/standard/experts/deepwork_rules/workflows/define/workflow.yml`
- **Line(s)**: 1-21
- **Severity**: Suggestion
- **Issue**: The workflow.yml only has one step (`define`) which makes the workflow structure somewhat redundant. The old `job.yml` was simpler for this single-step job.
- **Suggestion**: This is acceptable given the broader architectural shift to the experts system. Single-step workflows are a valid pattern.

## Code Suggestions

### Suggestion 1: Adding Command Action Documentation to expert.yml

**File**: src/deepwork/standard/experts/deepwork_rules/expert.yml

Before:
```yaml
  ## When to Use Rules

  Rules are most valuable for:
  - Keeping documentation in sync with code
  - Enforcing security reviews for sensitive changes
  - Ensuring test coverage follows source changes
  - Maintaining team guidelines automatically
```

After:
```yaml
  ## Action Types

  Rules support two action types:

  - **prompt** (default): Show instructions to the agent
  - **command**: Execute a shell command automatically

  Command actions are useful for:
  - Auto-running `uv sync` when pyproject.toml changes
  - Running linters when source files change
  - Generating documentation when schemas change

  ## When to Use Rules

  Rules are most valuable for:
  - Keeping documentation in sync with code
  - Enforcing security reviews for sensitive changes
  - Ensuring test coverage follows source changes
  - Maintaining team guidelines automatically
  - Auto-running commands when specific files change
```

**Rationale**: The command action feature is a powerful capability that differentiates DeepWork rules from simple trigger-based reminders. Users should be aware this option exists when the expert is consulted.

## Approval Status

**APPROVED**

No blocking issues within my domain. The migration preserves all core rules system functionality (detection modes, pattern syntax, comparison modes, hooks configuration). The rules continue to work correctly with the same file format and location (`.deepwork/rules/`). The suggestions above are improvements that would enhance documentation completeness, but the system is functional as-is.
