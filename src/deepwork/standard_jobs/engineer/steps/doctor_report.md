# Doctor Report

## Objective

Compile findings from the agent.md and context file audits into a consolidated pass/fail
report with specific remediation instructions for any failures.

## Task

Synthesize the previous audit steps into a single actionable report. The report serves two
audiences: the human developer who needs to fix issues, and the `implement` workflow which
needs to know if the repository is ready for automated engineering execution.

### Process

1. **Read both audit files**
   - Read `agent_md_audit.md` for agent context file findings
   - Read `context_audit.md` for supporting file findings
   - Collect all PASS and FAIL statuses

2. **Compile the consolidated report**
   - Organize findings by check category
   - For each failed check, provide:
     - What is wrong
     - Why it matters (which workflow step would fail or produce bad results)
     - Specific remediation steps (commands to run, content to add, files to create)
   - For passing checks, confirm with a brief status line

3. **Add cross-cutting recommendations**
   - If labels, branch protection, or milestones need attention, recommend the `repo`
     library job's `doctor` workflow — do not duplicate that job's scope
   - If the repository lacks CI configuration, note this as it affects artifact generation
     (Req 5)
   - If the repository is a monorepo, note that each sub-project may need its own context

4. **Determine overall readiness**
   - READY: All checks pass — the `implement` workflow can proceed
   - NOT READY: One or more critical checks fail — remediation is needed first
   - PARTIAL: Non-critical issues exist but `implement` can proceed with caveats

## Output Format

### .deepwork/tmp/doctor_report.md

**Structure**:
```markdown
# Engineer Doctor Report

## Overall Status: [READY/NOT READY/PARTIAL]

## Check Summary

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Agent context file exists | PASS/FAIL | [brief detail] |
| 2 | Engineering domain declared | PASS/FAIL | [brief detail] |
| 3 | Build instructions present | PASS/FAIL | [brief detail] |
| 4 | Test instructions present | PASS/FAIL | [brief detail] |
| 5 | Parse/navigate instructions present | PASS/FAIL | [brief detail] |
| 6 | Referenced files exist | PASS/FAIL | [N/N passed] |
| 7 | Referenced files valid syntax | PASS/FAIL | [N/N passed] |
| 8 | CODEOWNERS file present | PASS/FAIL | [path or "not found"] |

## Remediation Required

### [Check Name] — FAIL
**Problem**: [what is wrong]
**Impact**: [which workflow step would fail]
**Fix**:
1. [specific step]
2. [specific step]

### [Another Check] — FAIL
...

## Recommendations
- [recommendation about repo job, CI, or other improvements]

## Next Steps
- [If READY]: Run `engineer/implement` workflow to begin engineering work
- [If NOT READY]: Fix the issues listed above, then re-run `engineer/doctor`
- [If PARTIAL]: [specific caveats for proceeding]
```

## Quality Criteria

- Every check from both audit steps is represented in the summary table
- Failed checks have specific, actionable remediation instructions
- The report distinguishes between critical failures and non-critical recommendations
- Cross-cutting recommendations reference existing jobs (e.g., `repo/doctor`) rather than duplicating scope
- The overall status accurately reflects whether the `implement` workflow can proceed
