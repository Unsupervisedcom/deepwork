---
name: Version and Changelog Update
trigger: src/**/*
safety:
  - pyproject.toml
  - CHANGELOG.md
compare_to: base
---
Source code in src/ has been modified. **You MUST evaluate whether version and changelog updates are needed.**

**Evaluate the changes:**
1. Is this a bug fix, new feature, breaking change, or internal refactor?
2. Does this change affect the public API or user-facing behavior?
3. Would users need to know about this change when upgrading?

**If version update is needed:**
1. Update the `version` field in `pyproject.toml` following semantic versioning:
   - PATCH (0.1.x): Bug fixes, minor internal changes
   - MINOR (0.x.0): New features, non-breaking changes
   - MAJOR (x.0.0): Breaking changes
2. Add an entry to `CHANGELOG.md` under an appropriate version header:
   - Use categories: Added, Changed, Fixed, Removed, Deprecated, Security
   - Include a clear, user-facing description of what changed
   - Follow the Keep a Changelog format

**If NO version update is needed** (e.g., tests only, comments, internal refactoring with no behavior change):
- Explicitly state why no version bump is required

**This rule requires explicit action** - either update both files or justify why no update is needed.
