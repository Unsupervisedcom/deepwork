---
name: UV Lock Sync
trigger: pyproject.toml
action:
  command: uv sync
compare_to: prompt
---

# UV Lock Sync

Automatically runs `uv sync` when `pyproject.toml` is modified to keep
`uv.lock` in sync with dependency changes.

This ensures the lock file is always up-to-date when dependencies are
added, removed, or updated in pyproject.toml.
