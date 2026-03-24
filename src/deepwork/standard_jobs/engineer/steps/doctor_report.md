# Doctor Report

Compile findings from agent.md and context file audits into a pass/fail report with
remediation instructions. Serves two audiences: the developer fixing issues, and the
`implement` workflow checking readiness.

## Process

1. Read `agent_md_audit.md` and `context_audit.md`; collect all PASS/FAIL statuses
2. For each failed check, provide: what is wrong, which workflow step would fail, and
   specific remediation steps
3. Cross-cutting recommendations:
   - If labels/branch protection/milestones need attention, recommend `repo` library job's
     `doctor` workflow — do not duplicate that scope
   - If CI is not configured, note the impact on artifact generation (Req 5)
4. Determine overall readiness: READY (all pass), NOT READY (critical failures),
   or PARTIAL (non-critical issues, implement can proceed with caveats)

## Output Format

### .deepwork/tmp/doctor_report.md

```markdown
# Engineer Doctor Report

## Overall Status: [READY/NOT READY/PARTIAL]

## Check Summary

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Agent context file exists | PASS/FAIL | [detail] |
| 2 | Engineering domain declared | PASS/FAIL | [detail] |
| 3 | Build instructions present | PASS/FAIL | [detail] |
| 4 | Test instructions present | PASS/FAIL | [detail] |
| 5 | Parse/navigate instructions present | PASS/FAIL | [detail] |
| 6 | Referenced files exist | PASS/FAIL | [N/N passed] |
| 7 | Referenced files valid syntax | PASS/FAIL | [N/N passed] |
| 8 | CODEOWNERS file present | PASS/FAIL | [path or "not found"] |

## Remediation

### [Check Name] — FAIL
**Problem**: [what is wrong]
**Impact**: [which step would fail]
**Fix**: [specific steps]

## Recommendations
- [cross-cutting recommendations]

## Next Steps
- [READY]: Run `engineer/implement` to begin
- [NOT READY]: Fix issues above, re-run `engineer/doctor`
- [PARTIAL]: [caveats]
```
