# Check Milestones

## Objective

Verify milestone-issue consistency: each milestone's issues are properly labeled, states are correct, and milestone metadata is complete.

## Task

### Process

1. **Read milestones** from `platform_context.md`

2. **For each open milestone, verify:**

   a. **Issues exist** — milestone has at least one issue
      - Use the provider's CLI or API to list all issues for the milestone

   b. **Consolidated issue exists** — look for an issue whose title matches the milestone title
      (this is the "tracking issue" pattern where a parent issue tracks the milestone's work)
      - Flag if missing, but do not create it (just report)

   c. **Labels are correct** — each issue should have at least one of the required labels
      (`product`, `engineering`, or `plan`)
      - Flag issues missing all three labels

   d. **State consistency** — if all issues are closed, the milestone should be closeable
      - Flag milestones where all issues are closed but milestone is still open

3. **Compile findings per milestone**

## Output Format

### milestones_report.md

```markdown
# Milestones Report

## Summary
- **Total Open Milestones**: [count]
- **Milestones with Issues**: [count]
- **Empty Milestones**: [count]
- **Issues Missing Labels**: [count]

## Milestones

### [Milestone Title] (#[number])
- **Open Issues**: [count]
- **Closed Issues**: [count]
- **Consolidated Issue**: [found (#N) | missing]
- **Unlabeled Issues**: [count]
  - #[N] — [title]
- **State Issues**: [none | "all issues closed but milestone open"]
```

## Quality Criteria

- Every open milestone was inspected
- Each milestone's issues are listed with state and label correctness
- Missing consolidated issues are flagged
- Unlabeled issues are identified
