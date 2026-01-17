---
name: "Manual Test: Multi Safety"
trigger: manual_tests/test_multi_safety.py
safety:
  - manual_tests/test_multi_safety_changelog.md
  - manual_tests/test_multi_safety_version.txt
---

# Manual Test: Multiple Safety Patterns

You changed the source file without updating version info!

**Changed:** `{trigger_files}`

## What to do:

1. Update the changelog: `manual_tests/test_multi_safety_changelog.md`
2. And/or update the version: `manual_tests/test_multi_safety_version.txt`
3. Or acknowledge with `<promise>Manual Test: Multi Safety</promise>`

## This tests:

Trigger/safety mode with MULTIPLE safety patterns. The rule is
suppressed if ANY of the safety files are also edited.
