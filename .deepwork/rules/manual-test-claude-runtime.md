---
name: "Manual Test: Claude Runtime"
trigger: manual_tests/test_claude_runtime/test_claude_runtime_code.py
compare_to: prompt
prompt_runtime: claude
---

# Manual Test: Claude Runtime

You are evaluating code changes as part of an automated rule check.

**Review the code in the trigger file for:**
1. Basic code quality (clear variable names, proper structure)
2. Presence of docstrings or comments
3. No obvious bugs or issues

**This is a test rule.** For testing purposes:
- If the code looks reasonable, respond with `allow`
- If there are obvious issues (syntax errors, missing functions, etc.), respond with `block`

Since this is a manual test, the code is intentionally simple and should pass review.

## This tests:

The `prompt_runtime: claude` feature where instead of returning the prompt to
the triggering agent, Claude Code is invoked in headless mode to process
the rule autonomously.
