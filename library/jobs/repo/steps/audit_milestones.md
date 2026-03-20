# Audit Milestones

## Objective

Deep consistency check on milestones. Fix label drift on issues — add missing labels, correct mismatches.

## Task

### Process

1. **Read platform context** from `platform_context.md`

2. **For each open milestone:**

   a. **List all issues**
      - Use the provider's CLI or API to list all issues for the milestone with their title, state, labels, and assignees

   b. **Check consolidated issue**
      - Look for an issue whose title matches the milestone title
      - If missing, flag but do not create

   c. **Audit labels on each issue**
      - Every issue SHOULD have at least one of: `product`, `engineering`, `plan`
      - Apply heuristic to add missing labels:
        - Issues with specs, user stories, or UX mentions → `product`
        - Issues with implementation, code, or technical mentions → `engineering`
        - Issues about planning, coordination, or tracking → `plan`
      - Fix label drift using the provider's issue edit command

   d. **Check assignees**
      - Flag issues with no assignees
      - Do NOT auto-assign — just report

   e. **State consistency**
      - If all issues are closed, flag the milestone for closure
      - If milestone has a due date in the past and open issues remain, flag as overdue

3. **Compile audit findings and actions taken**

## Output Format

### milestones_audit.md

```markdown
# Milestones Audit

## Summary
- **Milestones Audited**: [count]
- **Issues Audited**: [count]
- **Labels Added**: [count]
- **Unassigned Issues**: [count]
- **Overdue Milestones**: [count]

## Milestones

### [Milestone Title] (#[number])

**Issues:**

| # | Title | State | Labels | Assignees | Action |
|---|-------|-------|--------|-----------|--------|
| ... | ... | ... | ... | ... | [added "engineering" label \| ok] |

**Findings:**
- Consolidated issue: [found (#N) \| missing]
- Unassigned issues: [list or "none"]
- State: [ok \| all closed — recommend closing milestone \| overdue]

## Actions Taken
- [List of label additions and other fixes]

## Manual Actions Needed
- [Milestones to close, issues to assign, etc.]
```

## Quality Criteria

- Every open milestone was deeply inspected
- Issues with incorrect or missing labels were corrected
- Milestone-issue relationships are consistent
- Unassigned issues and overdue milestones are flagged
