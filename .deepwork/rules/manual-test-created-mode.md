---
name: "Manual Test: Created Mode"
created: manual_tests/test_created_mode/*.yml
compare_to: prompt
prompt_runtime: send_to_stopping_agent
---

# Manual Test: Created Mode (File Creation Trigger)

A new test file was created in the created mode test directory!

**Created:** `{created_files}`

## What to do:

1. Verify the created mode detection is working correctly
2. Acknowledge with `<promise>Manual Test: Created Mode</promise>`

## This tests:

The "created" detection mode where rules only fire for newly created files,
not for modifications to existing files. This is useful for enforcing standards
on new code specifically.
