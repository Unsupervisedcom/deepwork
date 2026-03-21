# Create Reproduction Plan

## Objective

Transform the reproducibility analysis into a structured engineering plan with actionable tasks, dependencies, and acceptance criteria. Output the plan as markdown and optionally create issues on Forgejo or GitHub based on user preference or system context.

## Task

### Process

1. **Read the reproducibility analysis**

   Read `reproducibility_analysis.md` from the analyze step. Focus on:
   - P0 and P1 priority items (P2 items are optional)
   - Prerequisites and resource requirements
   - Dependencies between items
   - Missing information that needs resolution

2. **Design the task breakdown**

   For each reproducible item (starting with P0):

   - Break it into concrete engineering tasks
   - Each task should be independently assignable and completable
   - Define clear acceptance criteria (what "done" looks like)
   - Identify dependencies between tasks
   - Estimate relative effort

   Follow these principles:
   - Tasks should be small enough for one work session (hours, not days)
   - Prerequisites (setup, data acquisition) are their own tasks
   - Validation/verification is its own task, not buried in implementation

3. **Map task dependencies**

   Create a dependency graph:
   - Which tasks must complete before others can start?
   - Which tasks can run in parallel?
   - What's the critical path?

4. **Determine output format**

   Check the context to decide how to deliver the plan:

   a. **Check for explicit user preference**: Did the user specify they want issues created?
   b. **Check system context**: Is there a configured Forgejo or GitHub repo? Check for:
      - `FORGEJO_HOST` / `FORGEJO_USER` environment variables
      - `.git/config` for remote URL (GitHub or Forgejo)
      - `gh` CLI availability
      - `forgejo-project` CLI availability
   c. **Default to markdown only**: If no clear context for issue creation, produce the markdown plan.
   d. **If issue creation is appropriate**: Ask the user to confirm before creating issues.

5. **Write reproduction_plan.md**

   Always produce the markdown plan regardless of whether issues are created.

6. **Create issues (optional)**

   If the user wants issues and a repo is available:

   **For GitHub** (`gh` CLI):
   ```bash
   gh issue create --title "[Task title]" --body "[Task body with acceptance criteria]" --label "reproduction"
   ```

   **For Forgejo** (`forgejo-project` or API):
   - Create issues via the Forgejo API
   - Optionally add them to a project board
   - Tag with appropriate labels

   Link issues in the markdown plan for reference.

## Output Format

### reproduction_plan.md

**Location**: `research/[topic_slug]/reproduction_plan.md`

```markdown
# Reproduction Plan: [Topic Name]

**Source**: [title of original research material]
**Date**: [YYYY-MM-DD]
**Total tasks**: [count]
**Estimated effort**: [total range]

## Overview

[2-3 sentences: what this plan covers and the expected outcome of completing it]

## Prerequisites

- [ ] [Setup task or resource acquisition needed before starting]
- [ ] [Another prerequisite]

## Tasks

### Task 1: [Task Title]

**Priority**: [P0 | P1 | P2]
**From**: [Which reproducible item this task addresses]
**Effort**: [hours | days]
**Depends on**: [Task numbers, or "none"]
**Issue**: [link to created issue, or "N/A"]

**Description**:
[What to do, in enough detail for an engineer to start working]

**Acceptance criteria**:
- [ ] [Specific, verifiable criterion]
- [ ] [Another criterion]

---

### Task 2: [Task Title]

[Same structure]

---

[Repeat for all tasks]

## Dependency Graph

```
Task 1 (setup) ──→ Task 2 (implement) ──→ Task 4 (validate)
                ──→ Task 3 (implement) ──↗
```

## Handoff Notes

**For sweng workflow**: To execute these tasks via the DeepWork sweng workflow, use each task as the goal parameter when starting the workflow.

**For issue tracker**: [If issues were created: "N issues created on [repo]. See links above."
If not: "To create issues, run this workflow again with a configured repo, or manually create from the task descriptions above."]

## Open Questions

- [Any unresolved questions that need answers before work can begin]
- [Missing information from the original research]
```

### issues (optional)

If issues were created, report their URLs/numbers. Each issue should contain:
- Task description from the plan
- Acceptance criteria as a checklist
- Link back to the reproduction plan and original research
- Labels: `reproduction`, priority label

## Quality Criteria

- Plan contains specific, actionable tasks with clear acceptance criteria
- Task dependencies and ordering are clearly specified
- Plan is structured for handoff to a sweng workflow or issue tracker
- Each task is small enough to be independently completable
- Prerequisites are identified and listed separately
- Dependency graph shows the critical path

## Context

This is the final step of the **reproduce** workflow. The plan bridges research and engineering — it translates "what we learned" into "what to build." The output should be immediately actionable: an engineer (or an AI agent running the sweng workflow) should be able to pick up any task and start working with minimal additional context.
