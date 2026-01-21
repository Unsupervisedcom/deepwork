---
name: README Accuracy
trigger: src/**/*
safety: README.md
compare_to: base
prompt_runtime: claude
---
Source code in src/ has been modified. Please review README.md for accuracy:
1. Verify project overview still reflects current functionality
2. Check that usage examples are still correct
3. Ensure installation/setup instructions remain valid
4. Update any sections that reference changed code

If the README needs updates, make the changes directly. If the README is accurate, confirm it matches the current implementation.
