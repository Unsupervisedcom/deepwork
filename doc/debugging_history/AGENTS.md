# Debugging History Documentation Guide

This directory contains documentation of debugging sessions for DeepWork. Each file focuses on a specific subsystem (e.g., `hooks.md` for the hooks system).

## Purpose

Recording debugging sessions helps:
1. Preserve institutional knowledge about subtle bugs
2. Prevent regressions by documenting root causes
3. Provide context for future developers encountering similar issues
4. Build a pattern library of common issues and solutions

## Template for Debugging Entries

When documenting a debugging session, use this structure:

```markdown
## YYYY-MM-DD: Brief Issue Title

### Symptoms
What was observed? What tests were failing?

### Investigation
What was examined? What code paths were traced?

### Root Cause
What was the actual bug?

### The Fix
What changes were made?

### Test Cases Affected
Which tests verify this fix?

### Key Learnings
What general lessons apply to future development?

### Related Files
Which files are involved?
```

## Guidelines

1. **Be specific**: Include exact file paths, line numbers, and code snippets
2. **Document the journey**: Explain what you tried, not just what worked
3. **Highlight patterns**: Note if the issue represents a common class of bugs
4. **Link to commits/PRs**: Reference the fix for easy lookup
5. **Keep it concise**: Focus on what's useful for future debugging

## File Organization

- One file per subsystem (e.g., `hooks.md`, `queue.md`, `parser.md`)
- Entries within each file are in reverse chronological order (newest first)
- Use consistent heading levels for easy navigation
