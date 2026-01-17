---
name: "Manual Test: Pair Mode"
pair:
  trigger: manual_tests/claude/test_pair_mode_trigger.py
  expects: manual_tests/claude/test_pair_mode_expected.md
---

# Manual Test: Pair Mode (Directional Correspondence)

API code changed without documentation update!

**Changed:** `{trigger_files}`
**Expected:** `{expected_files}`

## What to do:

1. Update the API documentation in `test_pair_mode_expected.md`
2. Or acknowledge with `<promise>Manual Test: Pair Mode</promise>`

## This tests:

The "pair" detection mode where there's a ONE-WAY relationship.
When the trigger file changes, the expected file must also change.
BUT the expected file can change independently (docs can be updated
without requiring code changes).
