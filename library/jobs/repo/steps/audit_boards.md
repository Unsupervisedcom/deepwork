# Audit Boards

## Objective

Full board audit: add missing items, correct wrong statuses, flag stale cards. For providers without a board API, output manual instructions.

## Prerequisite

Requires `platform_context.md` and `milestones_audit.md`. Board audit depends on milestone audit because it needs accurate milestone-issue mappings.

## Task

### Process

1. **Handle providers without a board API**
   - If `boards_api: false` in `platform_context.md`, output manual review instructions:
     - How to check boards in the web UI:
       - For GitHub / Gitea / Forgejo: `https://{host}/{owner}/{repo}/projects`
       - For GitLab: `https://{host}/{owner}/{repo}/-/boards`
     - Checklist of things to verify manually
     - Skip all CLI automation steps below

2. **For each open milestone with a board:**

   a. **Fetch board items**
      - Use the provider's CLI or API to list all items on the board

   b. **Fetch milestone issues**
      - Use the provider's CLI or API to list all issues in the milestone

   c. **Find missing items** — milestone issues not on the board
      - Add missing items using the provider's board item add command

   d. **Cross-reference statuses** — for each board item:
      - Check linked issue state and PR state
      - Expected status rules:
        - Closed issue → Done
        - Open + non-draft PR with reviewers → In Review
        - Open + draft PR or open non-draft PR without reviewers → In Progress
        - Open + no PR → Backlog
      - Correct wrong statuses using the provider's board item edit command

   e. **Find stale cards** — board items whose linked issue is NOT in the milestone
      - Flag but do NOT auto-remove

3. **For milestones without boards:**
   - Flag as missing
   - Optionally create if there are issues to track (ask user or just report)

## Output Format

### boards_audit.md

```markdown
# Boards Audit

## Provider
- **Provider**: [github | forgejo | etc.]
- **Boards API**: [true | false]

## Summary
- **Boards Audited**: [count]
- **Items Added**: [count]
- **Statuses Corrected**: [count]
- **Stale Cards Flagged**: [count]
- **Missing Boards**: [count]

## Per-Board Details

### [Milestone Title] — Board #{number}

**Items Added:**

| Issue # | Item ID | Status Set | Reason |
|---------|---------|------------|--------|
| ... | ... | ... | ... |

**Statuses Corrected:**

| Issue # | Item ID | Old Status | New Status | Reason |
|---------|---------|------------|------------|--------|
| ... | ... | ... | ... | ... |

**Stale Cards:**

| Item ID | Linked Issue | Recommendation |
|---------|-------------|----------------|
| ... | ... | ... |

## Missing Boards
- [Milestone Title] — [count] issues, no board

## Manual Instructions (if no board API)
[Manual review checklist, or "N/A"]

## Actions Taken
- [Summary of all automated fixes]

## Remaining Issues
- [Items needing manual attention]
```

## Quality Criteria

- Every milestone's board was inspected
- Missing items were added to boards
- Wrong statuses were corrected based on issue/PR state
- Stale cards (not in milestone) are flagged
- If the provider lacks a board API, manual instructions are provided
