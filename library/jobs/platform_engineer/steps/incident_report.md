# Incident Report

## Objective

Synthesize the triage scope and investigation findings into a structured incident report with timeline, root cause analysis, impact assessment, and remediation suggestions. The report format scales with incident severity — minor issues get a concise summary, significant incidents get a full postmortem-style report.

## Task

Read the triage document and investigation findings, determine the appropriate report format, and produce a report that is accurate, evidence-backed, and actionable. Remediation commands are suggested but NEVER executed.

### Process

#### 1. Determine Report Format

Read `triage.md` and `investigation_findings.md`. Assess the incident severity to choose the report format:

**Quick Summary (1-2 pages)** — Use when:
- The issue is a known/recurring problem with a straightforward fix
- Impact was limited to a single service or a small number of users
- Root cause is clear with High confidence
- No cascading failures occurred
- Resolution is straightforward with a single, low-risk action

**Full Report (comprehensive)** — Use when:
- The issue caused significant user impact or downtime
- Multiple services were affected or cascading failures occurred
- Root cause is complex or involves multiple contributing factors
- The issue reveals systemic problems that need prevention measures
- The investigation uncovered Medium or Low confidence hypotheses that need further work
- The organization would benefit from a postmortem review

If in doubt, use the Full Report format — it is better to over-document than to under-document a significant incident.

#### 2. Build the Timeline

Construct a precise chronological timeline from all available evidence. Sources include:
- Investigation findings (log timestamps, metric anomaly windows, event times)
- Triage document (reported onset, recent changes)
- Deployment history (CI/CD correlation from investigation)

Each timeline entry MUST include:
- **Time** in UTC (or the timezone used consistently throughout the report)
- **Event** description
- **Source** of the information (log, metric, user report, CI system)

Order events strictly chronologically. Distinguish between:
- **Known facts** (observed in data)
- **Inferred events** (deduced from evidence, marked as such)

#### 3. Synthesize Root Cause Analysis

Take the hypotheses from the investigation findings and synthesize them into a root cause analysis:

- **Primary root cause**: The highest-confidence hypothesis, stated as a clear narrative
- **Contributing factors**: Lower-confidence hypotheses or conditions that made the incident worse
- **Trigger vs. underlying cause**: Distinguish between what triggered the incident (e.g., a deployment) and the underlying cause (e.g., a missing health check, a resource limit too low)

Every claim in the root cause analysis MUST reference specific evidence from the investigation. Do NOT introduce new analysis — this step synthesizes, it does not investigate.

If the root cause remains uncertain, state this honestly. Present the competing hypotheses with their confidence levels and what additional information would resolve the ambiguity.

#### 4. Assess Impact

Document the impact of the incident:

- **Duration**: From onset to resolution (or to current time if ongoing)
- **Scope**: Which services, endpoints, users, or environments were affected
- **User impact**: What users experienced (errors, slowness, unavailability)
- **Data impact**: Whether any data was lost, corrupted, or exposed (if applicable)
- **Business impact**: Revenue, SLA, reputation effects (if known or estimable)

Be factual about what is known and explicit about what is estimated.

#### 5. Formulate Remediation Suggestions

For each remediation action, provide:

- **Description**: What the action does
- **Specific command(s)**: The exact commands to execute (when applicable)
- **Risk level**: One of the following:
  - **Safe**: Read-only or additive change with no risk to running services. Can be executed immediately. Examples: adding a dashboard, updating documentation, adding a health check endpoint.
  - **Moderate**: Change affects running services but has a clear rollback path. Should be executed during a maintenance window or with monitoring. Examples: scaling a deployment, updating resource limits, rolling restart.
  - **High risk**: Change could cause additional disruption if it goes wrong. Requires explicit approval, a rollback plan, and someone watching during execution. Examples: database migration, certificate rotation, infrastructure provider change.
- **Rollback steps**: How to undo the action if it makes things worse
- **Verification**: How to confirm the action succeeded

Per conventions 1 and 2, the agent MUST NOT execute any remediation commands. Present them clearly so the user (or an operator) can review and execute them.

Group remediation into:
1. **Immediate**: Actions to resolve the current incident
2. **Short-term**: Follow-up work within the next sprint/week
3. **Long-term/Prevention**: Systemic improvements to prevent recurrence

#### 6. Write Prevention Recommendations (Full Report only)

For full reports, include prevention recommendations that address the underlying cause, not just the trigger:

- **Monitoring gaps**: What alerts or dashboards would have caught this earlier?
- **Process gaps**: What deployment or review practices would have prevented this?
- **Architecture gaps**: What design changes would make the system more resilient?
- **Testing gaps**: What tests would have caught this before deployment?

Each recommendation should be specific and actionable (e.g., "Add a readiness probe to the API deployment that checks database connectivity" rather than "improve monitoring").

#### 7. Write the Report

Write the report to `YYYY-MM-DD-<slug>.md` in the incident artifact directory (same directory as `triage.md` and `investigation_findings.md`).

Use the appropriate format (Quick Summary or Full Report) as determined in step 1.

## Output Format

### Quick Summary Format

Store as `YYYY-MM-DD-<slug>.md` in the incident artifact directory.

```markdown
# Incident Summary: <brief title>

**Date**: YYYY-MM-DD
**Environment**: <environment>
**Severity**: <minor / moderate>
**Status**: <resolved / ongoing / mitigated>

## What Happened

<2-3 paragraph narrative: what broke, why, and what the impact was>

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | <event> |
| HH:MM | <event> |
| ... | ... |

## Root Cause

<1-2 paragraph explanation of the root cause, referencing specific evidence>

**Confidence**: High / Medium / Low (per convention 5)

## Impact

- **Duration**: <time>
- **Affected**: <services/users>
- **User experience**: <what users saw>

## Remediation

### Immediate

| Action | Command | Risk | Rollback |
|--------|---------|------|----------|
| <action> | `<command>` | Safe / Moderate / High | `<rollback command>` |
| ... | ... | ... | ... |

### Follow-up

- [ ] <action item>
- [ ] <action item>

## Evidence References

- Triage: `<path to triage.md>`
- Investigation: `<path to investigation_findings.md>`
```

### Full Report Format

Store as `YYYY-MM-DD-<slug>.md` in the incident artifact directory.

```markdown
# Incident Report: <brief title>

**Date**: YYYY-MM-DD
**Environment**: <environment>
**Severity**: <significant / critical>
**Status**: <resolved / ongoing / mitigated>
**Report author**: AI Agent (platform_engineer job)
**Report date**: YYYY-MM-DD

---

## Executive Summary

<3-5 sentence summary for stakeholders who will not read the full report. Covers: what happened, how long it lasted, what the impact was, what the root cause was, and whether it is resolved.>

---

## Timeline

| Time (UTC) | Source | Event |
|------------|--------|-------|
| HH:MM | <source> | <event> |
| HH:MM | <source> | <event> |
| ... | ... | ... |

**Key moments**:
- **Onset**: HH:MM — <what triggered the incident>
- **Detection**: HH:MM — <how it was detected (alert, user report, monitoring)>
- **Investigation started**: HH:MM
- **Root cause identified**: HH:MM
- **Mitigated/Resolved**: HH:MM (or "ongoing")

---

## Root Cause Analysis

### Primary Root Cause

<Narrative explanation of what went wrong and why. Reference specific evidence.>

**Confidence**: High / Medium / Low (per convention 5)

### Contributing Factors

1. **<factor>**: <description and evidence>
2. **<factor>**: <description and evidence>

### Trigger vs. Underlying Cause

- **Trigger**: <the proximate cause, e.g., "a deployment at HH:MM">
- **Underlying cause**: <the systemic issue, e.g., "no readiness probe to catch database connectivity failures">

### Unresolved Questions

- <anything that remains uncertain, with what would resolve it>

---

## Impact Assessment

### Service Impact

| Service | Impact | Duration |
|---------|--------|----------|
| <service> | <description> | <time range> |
| ... | ... | ... |

### User Impact

- **Affected users**: <count or estimate, or "unknown">
- **User experience**: <what users saw — error pages, timeouts, degraded performance>

### Data Impact

- <whether any data was lost, corrupted, or exposed — or "No data impact identified">

---

## Evidence Summary

### Key Log Entries

```
<most important log lines from the investigation, with timestamps>
```

### Key Metrics

| Metric | Normal | During Incident | Anomaly |
|--------|--------|-----------------|---------|
| <metric> | <baseline> | <observed> | <description> |
| ... | ... | ... | ... |

### Negative Findings

Areas checked and found normal (narrowing the root cause):
- <area>: normal
- <area>: normal

---

## Remediation

### Immediate Actions (resolve the current incident)

#### Action 1: <description>

**Risk**: Safe / Moderate / High risk

```bash
<exact command(s) to execute>
```

**Rollback**:
```bash
<exact command(s) to undo>
```

**Verification**:
```bash
<exact command(s) to verify success>
```

---

#### Action 2: <description>
...

### Short-term Follow-up (next sprint/week)

- [ ] <action item with enough detail to create a ticket>
- [ ] <action item>

### Long-term Prevention (systemic improvements)

- [ ] <action item addressing the underlying cause>
- [ ] <action item>

---

## Prevention Recommendations

### Monitoring Improvements

- <specific monitoring gap and what to add>

### Process Improvements

- <specific process change to prevent recurrence>

### Architecture Improvements

- <specific design change to improve resilience>

### Testing Improvements

- <specific test to add that would catch this before deployment>

---

## References

- Triage document: `<path to triage.md>`
- Investigation findings: `<path to investigation_findings.md>`
- Platform context: `<path to context.md>`
- Related issues/PRs: <links if applicable>
```

## Quality Criteria

- **Accurate Timeline**: The incident timeline is clear with specific timestamps, ordered chronologically, and distinguishes between known facts and inferred events. No timeline gaps are left unexplained.
- **Supported Conclusions**: Root cause analysis is supported by evidence from the investigation, not speculation. Every claim references specific log lines, metric values, or events from the investigation findings. The confidence level honestly reflects the strength of the evidence per convention 5.
- **Actionable Remediation**: Remediation suggestions include specific commands with risk levels (Safe/Moderate/High risk) and rollback steps. Each action has a verification command. No commands are executed — they are presented for the user to review and run. Per convention 2, remediation is always suggested, never performed.
- **Appropriate Scope**: The report format matches the severity. Minor issues get a 1-2 page Quick Summary. Significant incidents get a comprehensive Full Report with Executive Summary, Prevention Recommendations, and detailed Evidence Summary. The format choice is justified.
- **No New Investigation**: This step synthesizes existing findings — it does not run new queries or introduce new evidence. All claims trace back to the triage and investigation documents.
- **Risk Levels Clear**: Every remediation action has an explicit risk level with rollback steps. High risk actions are clearly flagged and distinguished from safe actions.

## Context

This is the final step of the incident_investigation workflow. It takes the raw investigation findings and triage scope and transforms them into a document that serves multiple audiences:

- **Operators** need the remediation section to resolve the incident
- **Engineers** need the root cause analysis to understand what went wrong
- **Managers/stakeholders** need the executive summary and impact assessment
- **Future investigators** need the timeline and evidence references

Per conventions 1 and 2, the agent has not taken any actions during the investigation — this report is the first time remediation actions are proposed. The user decides which actions to execute and when.

The report is stored alongside the triage and investigation documents in the incident artifact directory, creating a complete record of the incident that can be referenced later. This supports convention 17 (documenting infrastructure decisions) and creates institutional knowledge about failure modes.

The Quick Summary vs. Full Report distinction prevents over-documentation of trivial issues while ensuring significant incidents get the thorough analysis they deserve.
