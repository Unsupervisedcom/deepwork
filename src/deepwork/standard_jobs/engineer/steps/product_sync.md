# Synchronize Product Issue

## Objective

After PR merge and engineering issue closure, author a formal comment on the parent
product issue documenting completed user stories with immutable links to the merged PR
and closed engineering issue.

## Task

Close the traceability loop by updating the product issue so product managers have
up-to-date visibility without parsing engineering telemetry. This step is designed to
run after the PR has been merged — if the PR is still under review, pause and resume
this step later.

### Process

1. **Verify prerequisites**
   - Confirm the PR has been merged (check PR state)
   - Confirm the engineering issue is closed (check issue state)
   - If either is still open, inform the user and pause — this step can be resumed later
     via `go_to_step`

2. **Gather immutable links**
   - Merged PR URL (the canonical merged-state URL, not a draft URL)
   - Closed engineering issue URL
   - Any relevant commit SHAs for key changes

3. **Identify completed user stories**
   - Cross-reference the engineering issue's implementation plan with the product issue's
     user story and requirements
   - Summarize which high-level user stories were addressed
   - Note any requirements that were partially addressed or deferred

4. **Author the product issue comment**
   - Post a formal comment on the parent product issue
   - The comment MUST include:
     - Which user stories were completed
     - Immutable links to the merged PR and closed engineering issue
     - Any deferred items or follow-up needed
   - The comment SHOULD be written for a product manager audience (no engineering jargon)

5. **Record the synchronization**
   - Document what was posted and when

### Domain Adaptation

| Concept          | Software              | Hardware/CAD           | Firmware              | Docs                 |
|------------------|-----------------------|------------------------|-----------------------|----------------------|
| "Merged PR"      | Code PR merged        | Design PR merged       | FW PR merged          | Content PR merged    |
| User story       | Feature/fix           | Design requirement     | HW interface need     | Content requirement  |
| Follow-up        | Tech debt, next phase | Prototype feedback     | Integration test plan | Review feedback      |

## Output Format

### .deepwork/tmp/product_sync_record.md

**Structure**:
```markdown
# Product Sync Record

## Prerequisites
- PR merged: yes/no — [PR URL]
- Engineering issue closed: yes/no — [issue URL]

## Comment Posted
- Product issue: [product issue URL]
- Timestamp: [ISO 8601]

## Comment Content
---
[The exact text of the comment that was posted]
---

## Traceability
- User stories completed: [list]
- Deferred items: [list or "none"]
- Follow-up needed: [yes/no — description]
```

## Quality Criteria

- The product issue comment was posted only after the PR was merged and engineering issue closed
- The comment includes immutable links to the merged PR and closed engineering issue
- User stories completed are summarized in product-manager-friendly language
- Any deferred items are explicitly documented
- The comment provides enough context for product visibility without engineering telemetry
