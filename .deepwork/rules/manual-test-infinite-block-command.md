---
name: "Manual Test: Infinite Block Command"
trigger: manual_tests/test_infinite_block_command/test_infinite_block_command.py
action:
  command: "false"
  run_for: each_match
compare_to: prompt
prompt_runtime: send_to_stopping_agent
---

# Manual Test: Infinite Block Command (Promise Required)

This rule runs a command that ALWAYS FAILS (`false` returns exit code 1).

## Why this blocks

The command action always fails, creating an infinite block. The only way
to proceed should be to provide a promise acknowledging that you understand
the restriction.

## Expected behavior

If promises work correctly for command actions:
- Without promise: Command runs, fails, blocks
- With promise: Command is SKIPPED entirely, allows

If there's a bug:
- The command will run and fail even when a promise is provided

## What to do

You MUST include the following promise tag in your response:

```
<promise>Manual Test: Infinite Block Command</promise>
```

## This tests

Whether the promise mechanism works for COMMAND-type rules. If a rule is
promised, the command should not run at all - the rule should be skipped
during evaluation.
