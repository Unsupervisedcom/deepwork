# Doctor Report

## Objective

Compile a summary of all audit findings, fixes applied, and remaining issues across all four concerns.

## Task

### Process

1. **Read all input reports**
   - `platform_context.md` — provider and repo info
   - `labels_audit.md` — label audit findings and fixes
   - `branch_protection_audit.md` — protection audit and fixes
   - `milestones_audit.md` — milestone audit and label drift fixes
   - `boards_audit.md` — board audit and status corrections

2. **Summarize findings per concern**
   - Count total findings, fixes applied, and remaining issues

3. **Determine health status for each concern**
   - HEALTHY: no issues found (nothing to fix)
   - FIXED: issues were found and all were automatically fixed
   - NEEDS ATTENTION: issues remain that require manual intervention

4. **Compile remaining manual actions**
   - Aggregate all items from each audit that still need human attention

## Output Format

### doctor_report.md

```markdown
# Doctor Report

## Repository
- **Repo**: [owner/repo]
- **Provider**: [github | forgejo | etc.]
- **Date**: [YYYY-MM-DD]

## Overall Health: [HEALTHY | FIXED | NEEDS ATTENTION]

## Summary

| Concern | Findings | Fixed | Remaining | Status |
|---------|----------|-------|-----------|--------|
| Labels | [count] | [count] | [count] | [HEALTHY \| FIXED \| NEEDS ATTENTION] |
| Branch Protection | [count] | [count] | [count] | [HEALTHY \| FIXED \| NEEDS ATTENTION] |
| Milestones | [count] | [count] | [count] | [HEALTHY \| FIXED \| NEEDS ATTENTION] |
| Boards | [count] | [count] | [count] | [HEALTHY \| FIXED \| NEEDS ATTENTION] |

## Details

### Labels
- **Findings**: [summary from labels_audit.md]
- **Actions Taken**: [list]
- **Remaining**: [list or "None"]

### Branch Protection
- **Findings**: [summary from branch_protection_audit.md]
- **Actions Taken**: [list]
- **Remaining**: [list or "None"]

### Milestones
- **Findings**: [summary from milestones_audit.md]
- **Actions Taken**: [list]
- **Remaining**: [list or "None"]

### Boards
- **Findings**: [summary from boards_audit.md]
- **Actions Taken**: [list]
- **Remaining**: [list or "None"]

## Manual Actions Needed
1. [Numbered list of items requiring human attention]
[Or "None — repository is healthy"]
```

## Quality Criteria

- Report covers all four concerns: labels, branch protection, milestones, boards
- All audit findings are summarized with counts
- All fix actions taken are listed
- Any issues still needing manual attention are documented
