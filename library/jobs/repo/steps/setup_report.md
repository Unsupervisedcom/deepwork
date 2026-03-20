# Setup Report

## Objective

Compile a pass/fail readiness report across all four concerns: labels, branch protection, milestones, and boards.

## Task

### Process

1. **Read all input reports**
   - `platform_context.md` — provider and repo info
   - `labels_report.md` — label status
   - `branch_protection_report.md` — protection status
   - `milestones_report.md` — milestone consistency
   - `boards_report.md` — board existence and item counts

2. **Determine pass/fail for each concern**

   **Labels**: PASS if all three required labels exist. FAIL if any are missing after setup.

   **Branch Protection**: PASS if all expected protections are enabled. WARN if partially protected. FAIL if unprotected.

   **Milestones**: PASS if all milestones have issues, consolidated issues, and proper labels. WARN if minor issues found. FAIL if milestones are empty or severely inconsistent.

   **Boards**: PASS if every milestone has a board with matching item counts. WARN if minor mismatches. FAIL if boards are missing. N/A if provider lacks board API.

3. **Compile overall readiness**
   - READY: all concerns pass
   - NEEDS ATTENTION: one or more concerns have warnings
   - NOT READY: one or more concerns fail

## Output Format

### setup_report.md

```markdown
# Repo Setup Report

## Repository
- **Repo**: [owner/repo]
- **Provider**: [github | forgejo | etc.]
- **Default Branch**: [branch]
- **Date**: [YYYY-MM-DD]

## Readiness: [READY | NEEDS ATTENTION | NOT READY]

## Concerns

| Concern | Status | Details |
|---------|--------|---------|
| Labels | [PASS \| FAIL] | [summary] |
| Branch Protection | [PASS \| WARN \| FAIL] | [summary] |
| Milestones | [PASS \| WARN \| FAIL] | [summary] |
| Boards | [PASS \| WARN \| FAIL \| N/A] | [summary] |

## Details

### Labels
[Key findings from labels_report.md]

### Branch Protection
[Key findings from branch_protection_report.md]

### Milestones
[Key findings from milestones_report.md]

### Boards
[Key findings from boards_report.md]

## Recommended Actions
- [Numbered list of next steps to reach READY status, or "None — repo is ready for work"]
```

## Quality Criteria

- Report covers all four concerns: labels, branch protection, milestones, boards
- Each concern has a clear pass/fail/warn status with supporting details
- Overall readiness is determined
- Recommended actions are listed
