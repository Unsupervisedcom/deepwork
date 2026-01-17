---
name: "Manual Test: Set Mode"
set:
  - manual_tests/test_set_mode/test_set_mode_source.py
  - manual_tests/test_set_mode/test_set_mode_test.py
compare_to: prompt
---

# Manual Test: Set Mode (Bidirectional Correspondence)

Source and test files must change together!

**Changed:** `{trigger_files}`
**Missing:** `{expected_files}`

## What to do:

1. If you changed the source file, update the corresponding test file
2. If you changed the test file, ensure the source file reflects those changes
3. Or acknowledge with `<promise>Manual Test: Set Mode</promise>`

## This tests:

The "set" detection mode where files in a set must ALL change together.
This is bidirectional - the rule fires regardless of which file in the set
was edited first.
