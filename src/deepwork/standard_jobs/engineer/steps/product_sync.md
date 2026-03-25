# Synchronize Product Issue

After PR merge and engineering issue closure, author a formal comment on the parent
product issue documenting completed user stories with immutable links.

## Process

1. **Verify prerequisites** — confirm the PR is merged and the engineering issue is closed.
   If either is still open, inform the user and pause — resume via `go_to_step` after merge.
2. Gather immutable links: merged PR URL, closed engineering issue URL, key commit SHAs
3. Summarize which high-level user stories were addressed; note any deferred items
4. Post a formal comment on the parent product issue:
   - Which user stories were completed
   - Immutable links to merged PR and closed engineering issue
   - Any deferred items or follow-up needed
   - Written for a product manager audience (no engineering jargon)

## Output Format

### .deepwork/tmp/product_sync_record.md

```markdown
# Product Sync Record

## Prerequisites
- PR merged: yes/no — [PR URL]
- Engineering issue closed: yes/no — [issue URL]

## Comment Posted
- Product issue: [URL]
- Timestamp: [ISO 8601]

## Comment Content
---
[exact text posted]
---

## Traceability
- User stories completed: [list]
- Deferred items: [list or "none"]
- Follow-up needed: [yes/no — description]
```
