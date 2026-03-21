# Execute Migration

## Objective

Execute the infrastructure migration by following the migration plan step by step, running validation gates between each step, tracking progress in the GitHub issue, and producing a final migration report. MUST NOT proceed past a failed validation gate without explicit user approval. MUST NOT execute destructive actions without explicit user confirmation.

## Task

Follow the migration plan from `migration_plan.md`, executing each step in order, validating success at each gate, updating the GitHub issue checklist, and handling failures with appropriate rollback when needed.

### Process

#### 1. Read the migration plan

- Load `migration_plan.md` from the previous step
- Extract:
  - The full list of steps (pre-migration, migration, post-migration) and their validation gates
  - The rollback plan and point of no return
  - The GitHub issue number (from `github_issue_url.md`)
  - The estimated durations for each step
  - The risk level and any special precautions noted

- Verify the plan is complete:
  - Every migration step has a validation gate
  - The rollback plan is documented
  - The GitHub issue exists and is open
  - Pre-migration steps include a backup step

If any element is missing, use `AskUserQuestion` to flag the gap and get guidance before proceeding.

#### 2. Execute each step with validation gates

Work through the steps in the order defined in the migration plan. For each step:

**a. Announce the step to the user:**
- State which step is about to be executed (step number, title)
- State the estimated duration
- If this step is at or past the point of no return, explicitly warn the user

**b. Confirm with the user before executing:**
- Use `AskUserQuestion` to get explicit approval before executing the step
- The question MUST state what the step will do and whether it is destructive
- For pre-migration and post-migration steps that are non-destructive (health checks, backups, verification), a brief confirmation is sufficient
- For migration steps that modify infrastructure, the confirmation MUST include:
  - What will change
  - Whether it is reversible
  - What the rollback procedure is for this specific step

**c. Execute the step:**
- Run the commands specified in the migration plan
- Replace any `<PLACEHOLDER>` values with actual values (ask the user if values are unknown)
- Capture command output for the migration report
- If a command fails, do NOT proceed — go to the failure handling process (section 3)

**d. Run the validation gate:**
- Execute the validation check specified in the migration plan for this step
- Record the result: PASS or FAIL
- If PASS: proceed to the next step
- If FAIL: do NOT proceed — go to the failure handling process (section 3)

**e. Update the GitHub issue:**
- Check off the completed item in the GitHub issue checklist using `gh issue edit` or by posting a comment
- Per convention 45, the issue MUST reflect which steps are completed and which are pending
- Include a brief note of the validation result

**f. Log the step in the execution log:**
- Record: step number, step title, start time, end time, validation result, any notes

#### 3. Handle validation gate failures

When a step fails or its validation gate does not pass:

**a. Stop and assess:**
- Do NOT proceed to the next step
- Document what failed and the error output
- Check whether this is before or after the point of no return

**b. Diagnose the failure:**
- Review the error output for obvious causes
- Check related logs (kubectl logs, systemd journal, cloud provider logs as appropriate)
- Check whether the failure is transient (network timeout, rate limit) or structural (misconfiguration, missing prerequisite)

**c. Present options to the user via AskUserQuestion:**

If the failure is before the point of no return:
- **Option 1: Fix and retry** — describe what needs to be fixed and attempt the fix
- **Option 2: Rollback** — execute the rollback procedure from the migration plan
- **Option 3: Skip (with justification)** — only if the step is non-critical and the user explicitly approves

If the failure is at or after the point of no return:
- **Option 1: Fix and retry** — describe what needs to be fixed
- **Option 2: Forward-fix** — continue the migration with a modified approach
- Explain clearly that full rollback may not be possible and what data implications exist

**d. If rollback is chosen:**
- Execute the rollback procedure from the migration plan
- Run the rollback verification checks
- Update the GitHub issue with rollback status
- Document the rollback in the migration report

**e. If fix-and-retry is chosen:**
- Apply the fix
- Re-run the step from the beginning
- Re-run the validation gate
- If the retry also fails after 3 attempts, strongly recommend rollback or escalation

#### 4. Complete post-migration verification

After all migration steps pass their validation gates, execute the post-migration phase:

**a. Comprehensive health check:**
- Run all health check endpoints on the migrated system
- Verify all dependent services can connect to the migrated component
- Check that no error alerts are firing

**b. Metrics comparison (if dashboards are available):**
- Compare key metrics between the old and new system:
  - Request rate: should be comparable
  - Error rate: should not have increased
  - Latency (p50, p99): should not have degraded significantly
- If Grafana MCP is available, use it to query dashboards per convention 55
- If Grafana MCP is not available, use CLI tools per convention 56
- Define "comparable" thresholds: within 10% for rate metrics, within 20% for latency

**c. Data integrity verification (for data migrations):**
- Compare row counts between old and new data stores
- Spot-check sample records
- Verify any checksums or hashes computed during the migration
- Run any application-specific data validation queries

**d. Monitoring soak period:**
- Inform the user of the soak period duration (from the migration plan)
- Use `AskUserQuestion` to check in after the soak period:
  - "The migration soak period of <duration> has started. Have you observed any issues with the migrated system during this period?"
- If issues are reported during the soak period, investigate and determine whether rollback is needed

**e. Cleanup (after soak period passes):**
- List the old resources to be removed (from the migration plan)
- Confirm with the user via `AskUserQuestion` before removing any old resources
- Remove old resources
- Validate that removal did not affect the new system

**f. Update documentation:**
- Update infrastructure documentation to reflect the new state per convention 14
- Update any connection strings, endpoints, or configuration references in the repository
- Update the GitHub issue with final completion status

#### 5. Finalize the migration report

After all phases complete (or if the migration was rolled back), produce the final migration report.

## Output Format

### migration_report.md

```markdown
# Migration Report: <brief description>

**Date**: YYYY-MM-DD
**Migration**: <what was migrated>
**Status**: COMPLETED / ROLLED BACK / PARTIALLY COMPLETED
**Duration**: <total wall-clock time>
**GitHub Issue**: <issue URL>

## Executive Summary

<2-3 sentence summary of what happened, whether it succeeded, and any notable issues>

## Execution Log

| # | Step | Phase | Started | Completed | Validation | Notes |
|---|------|-------|---------|-----------|------------|-------|
| P1 | Create Backup | Pre-migration | HH:MM | HH:MM | PASS | <brief note> |
| P2 | Freeze Automated Changes | Pre-migration | HH:MM | HH:MM | PASS | <brief note> |
| M1 | <step title> | Migration | HH:MM | HH:MM | PASS/FAIL | <brief note> |
| M2 | <step title> | Migration | HH:MM | HH:MM | PASS/FAIL | <brief note> |
| V1 | Health Check | Post-migration | HH:MM | HH:MM | PASS/FAIL | <brief note> |
| ... | ... | ... | ... | ... | ... | ... |

## Issues Encountered

### Issue 1: <title>
- **Step**: <which step failed>
- **Error**: <error message or output>
- **Root Cause**: <what caused the failure>
- **Resolution**: <how it was resolved — fix applied, retried, rolled back>
- **Time Lost**: <how long the issue added to the migration>

### Issue 2: <title>
...

(If no issues: "No issues were encountered during the migration.")

## Final State

### Migrated Component
- **Status**: Running / Healthy / Degraded
- **Endpoint**: <new endpoint or connection string>
- **Version**: <version of the new component>

### Metrics Comparison (if applicable)
| Metric | Before Migration | After Migration | Delta | Acceptable? |
|--------|-----------------|-----------------|-------|-------------|
| Request rate | <value> | <value> | <% change> | Yes / No |
| Error rate | <value> | <value> | <% change> | Yes / No |
| Latency p99 | <value> | <value> | <% change> | Yes / No |

### Data Integrity (if applicable)
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Row count (<table>) | <count> | <count> | MATCH / MISMATCH |
| Checksum | <hash> | <hash> | MATCH / MISMATCH |

### Old Resources
| Resource | Status | Action |
|----------|--------|--------|
| <resource> | Removed / Retained (grace period until <date>) / Still running | <reason> |

## Post-Migration Monitoring

- **Soak Period**: <duration> starting <time>
- **Key Dashboards to Watch**: <list>
- **Alerts to Monitor**: <list>
- **Issues During Soak**: <description or "none">

## Lessons Learned

1. <what went well>
2. <what could be improved>
3. <what was unexpected>

## Documentation Updated

- [ ] Infrastructure docs updated to reflect new state
- [ ] Connection strings updated in repo
- [ ] Runbooks updated (if applicable)
- [ ] GitHub issue closed
```

## Quality Criteria

- **Steps Completed**: All migration steps from the plan are accounted for in the execution log with PASS/FAIL status. No steps are silently skipped. Skipped steps (if any) are documented with the user's explicit approval and rationale.
- **Validations Passed**: Each validation gate result is documented in the execution log. Failed validations include the error output and the resolution taken (fix, retry, rollback, or user-approved skip).
- **State Tracked**: Migration progress is tracked in the GitHub issue per convention 45. Checklist items are checked off as steps complete. Comments are posted for notable events (failures, rollbacks, completion).
- **Final State Verified**: The post-migration state is verified and documented, including health check results, metrics comparison (if applicable), and data integrity checks (if applicable). The final state section clearly shows whether the migrated system is healthy.
- **User Confirmed**: Every destructive or irreversible action was confirmed with the user via AskUserQuestion before execution. The point of no return was explicitly communicated. Rollback decisions were made by the user, not the agent.
- **Failures Documented**: Every issue encountered during the migration is documented with the error, root cause, resolution, and time impact. If the migration was rolled back, the rollback procedure and verification are fully documented.
- **Cleanup Completed**: Old resources are either removed (after soak period and user approval) or explicitly retained with a documented grace period and reason. No orphaned resources are left undocumented.

## Context

This step is the second of two in the `infrastructure_migration` workflow (`plan_migration` -> `execute_migration`). It receives the `migration_plan.md` from the planning step, which contains the full sequence of steps, validation gates, and rollback procedures.

The execution step is inherently interactive — it requires user confirmation at multiple points. This is by design: infrastructure migrations carry real risk, and the agent MUST NOT take destructive actions unilaterally (per convention 1 and convention 2).

The GitHub issue created in the planning step serves as the live tracking document. The `execute_migration` step updates it as steps complete per convention 45. After the migration, the issue should be closeable as a complete record of what happened.

Key conventions referenced:
- Convention 1: Agents MUST NOT take destructive actions during investigation
- Convention 2: Agents MUST suggest remediation commands but MUST NOT execute them without explicit user approval
- Convention 5: Confidence levels MUST follow the defined scale
- Convention 40: Migrations MUST have a documented rollback plan before execution begins
- Convention 44: Each migration step MUST have a validation gate
- Convention 45: Migration state MUST be tracked in the GitHub issue
- Convention 55: Agents SHOULD use Grafana MCP tools when available
- Convention 56: If Grafana MCP is not available, agents MUST fall back to CLI tools
