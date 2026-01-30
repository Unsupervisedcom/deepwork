---
name: Prompt Hooks Not Executed in Claude Code
last_updated: 2025-01-30
summarized_result: |
  Claude Code parses but does not execute prompt-based stop hooks.
  Only script/command hooks actually run. Use quality_criteria for validation.
---

## Context

When implementing quality validation for job steps, developers often try
to use inline `prompt` or `prompt_file` hooks for validation.

## Investigation

Testing revealed that Claude Code's hook system only executes `command` type
hooks in the settings.json hooks configuration. Prompt-based hooks are parsed
by DeepWork but not rendered into the skill's hook frontmatter because they
would not be executed.

The template code explicitly filters:
```jinja
{%- set script_hooks = event_hooks | selectattr("type", "equalto", "script") | list %}
```

## Resolution

Two recommended approaches for quality validation:

1. **Use `quality_criteria` field** (preferred):
   ```yaml
   quality_criteria:
     - "Each competitor has description"
     - "Sources are cited"
   ```
   This generates instructions for sub-agent review, which works reliably.

2. **Use script hooks** for objective validation:
   ```yaml
   hooks:
     after_agent:
       - script: hooks/run_tests.sh
   ```
   Scripts actually execute and can fail the step.

## Key Takeaway

For subjective quality checks, use the `quality_criteria` field which triggers
sub-agent review. For objective checks (tests, linting), use script hooks.
Avoid prompt hooks until Claude Code supports them.
