# Check Boards

## Objective

Verify that each milestone has a corresponding project board and that item counts match the milestone's issue count.

## Prerequisite

Requires `platform_context.md` (board inventory) and `milestones_report.md` (milestone data). Board checks depend on milestones because boards are organized per-milestone.

## Task

### Process

1. **Handle providers without a board API**
   - If `boards_api: false` in `platform_context.md`, output manual instructions:
     - Board URL pattern: `https://{host}/{owner}/{repo}/projects`
     - Steps to create a board manually in the web UI
     - Skip all CLI automation steps below

2. **For each open milestone:**

   a. **Check for corresponding board**
      - Match board title against milestone title (from `platform_context.md` boards inventory)

   b. **If board exists, verify item count**
      - Use the provider's CLI or API to count board items
      - Compare board item count against milestone issue count (from `milestones_report.md`)
      - Flag mismatches

   c. **If no board exists**
      - Flag as missing
      - Do NOT create it in the setup workflow — only report

3. **Check board columns** (for existing boards)
   - Verify the five standard columns exist: Backlog, To Do, In Progress, In Review, Done

## Output Format

### boards_report.md

```markdown
# Boards Report

## Provider
- **Provider**: [github | forgejo | etc.]
- **Boards API**: [true | false]

## Summary
- **Milestones Checked**: [count]
- **Boards Found**: [count]
- **Boards Missing**: [count]
- **Item Count Mismatches**: [count]

## Milestones

### [Milestone Title]
- **Board**: [found (#{number}) | missing]
- **Board URL**: [url | N/A]
- **Milestone Issues**: [count]
- **Board Items**: [count | N/A]
- **Match**: [yes | no — [details] | N/A]
- **Columns OK**: [yes | no — missing: [list] | N/A]

## Manual Instructions (if no board API)

[Step-by-step web UI instructions for creating and managing boards, or "N/A — using CLI"]
```

## Quality Criteria

- Each milestone was checked for a corresponding board
- Board item counts are compared against milestone issue counts
- Missing boards are flagged
- If the provider lacks a board API, manual instructions are provided
