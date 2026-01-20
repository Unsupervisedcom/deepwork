---
name: "Manual Test: Infinite Block Prompt"
trigger: manual_tests/test_infinite_block_prompt/test_infinite_block_prompt.py
compare_to: prompt
---

# Manual Test: Infinite Block Prompt (Promise Required)

You edited `{trigger_files}` which triggers an infinite block.

## Why this blocks

This rule has NO safety file option and uses a PROMPT action. The only way
to proceed is to provide a promise acknowledging that you understand the
restriction.

## What to do

You MUST include the following promise tag in your response:

```
<promise>Manual Test: Infinite Block Prompt</promise>
```

This simulates scenarios where:
- An operation requires explicit acknowledgment before proceeding
- There is no alternative action that can suppress the rule
- The agent must demonstrate understanding of the constraint

## This tests

The promise mechanism for PROMPT-type rules that cannot be satisfied by
editing additional files. This is useful for enforcing policies where
acknowledgment is the only valid response.
