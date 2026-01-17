---
name: "Manual Test: Trigger Safety"
trigger: manual_tests/claude/test_trigger_safety_mode.py
safety: manual_tests/claude/test_trigger_safety_mode_doc.md
---

# Manual Test: Trigger/Safety Mode

You edited `{trigger_files}` without updating the documentation.

## What to do:

1. Review the changes in the source file
2. Update `manual_tests/claude/test_trigger_safety_mode_doc.md` to reflect changes
3. Or acknowledge this is intentional with `<promise>Manual Test: Trigger Safety</promise>`

## This tests:

The basic trigger/safety detection mode where editing the trigger file
causes the rule to fire UNLESS the safety file is also edited.
