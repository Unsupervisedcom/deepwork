---
name: Architecture Documentation Accuracy
trigger: src/**/*
safety: doc/architecture.md
compare_to: base
prompt_runtime: claude
---
Source code in src/ has been modified. Please review doc/architecture.md for accuracy:
1. Verify the documented architecture matches the current implementation
2. Check that file paths and directory structures are still correct
3. Ensure component descriptions reflect actual behavior
4. Update any diagrams or flows that may have changed

If the architecture documentation needs updates, make the changes directly. If the documentation is accurate, confirm it matches the current implementation.
