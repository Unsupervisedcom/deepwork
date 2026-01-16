# Root Cause Analysis

## Objective

Synthesize findings from alerts, metrics, and logs to identify the root cause of the production issue. This step operates entirely within the main context using the structured summaries from previous steps.

## Task

Analyze the investigation artifacts to determine the root cause and create a comprehensive timeline of the incident.

### Step-by-Step Process

1. **Review All Artifacts**
   - Read `triage.md` for the original issue description
   - Read `alerts.md` for alert patterns and timing
   - Read `metrics.md` for metric trends and anomalies
   - Read `logs.md` for error patterns and representative samples

2. **Identify the Root Cause**

Answer these questions:

- **What failed?** (component, service, resource)
- **Why did it fail?** (trigger, underlying condition)
- **When did it start?** (precise timestamp if possible)
- **What was the propagation?** (how did the failure spread)
- **What was the user impact?** (symptoms, scope)

Use evidence from the investigation:
- Alerts that fired
- Metric anomalies and trends
- Log patterns and errors
- Correlations between data sources

3. **Build Incident Timeline**

Create a chronological sequence of events:

1. **Pre-incident state** (what was normal)
2. **Trigger event** (what initiated the problem)
3. **Cascading effects** (how the problem propagated)
4. **Detection** (when alerts fired, when users noticed)
5. **Current state** (ongoing or resolved)

For each event, include:
- Precise timestamp
- What happened (from logs, metrics, alerts)
- Evidence source (which artifact)

4. **Assess Confidence Level**

Rate your confidence in the root cause:
- **High**: Strong evidence from multiple sources
- **Medium**: Evidence from one source, or circumstantial from multiple
- **Low**: Hypothesis based on limited evidence

Identify any gaps in evidence or alternative explanations.

5. **Create Root Cause Document**

Create `root_cause.md` with this structure:

```markdown
# Root Cause Analysis

**Investigation**: [from triage.md]
**Completed**: [current timestamp]
**Confidence**: [High/Medium/Low]

## Executive Summary

[1-2 paragraph summary of the root cause suitable for stakeholders]

## Root Cause

### What Failed
[Component, service, or resource that failed]

### Why It Failed
[Underlying cause - configuration error, resource exhaustion, bug, external dependency, etc.]

### Evidence
- **Alerts**: [specific alerts that support this conclusion]
- **Metrics**: [specific metrics that support this conclusion]
- **Logs**: [specific log patterns that support this conclusion]

### Trigger Event
[What initiated the failure - deployment, traffic spike, infrastructure change, etc.]

**Timestamp**: [when trigger occurred]

**Evidence**: [how we know this was the trigger]

## Impact Analysis

### User Impact
- **Scope**: [percentage of users, specific user segments, all users]
- **Symptoms**: [what users experienced]
- **Duration**: [how long impact lasted]

### System Impact
- **Services Affected**: [list]
- **Services Degraded**: [list]
- **Dependencies Broken**: [list]

## Alternative Hypotheses Considered

### Hypothesis 1: [Description]
**Ruled Out Because**: [Evidence that contradicts this]

### Hypothesis 2: [Description]
**Ruled Out Because**: [Evidence that contradicts this]

## Evidence Gaps

[Areas where evidence is incomplete or missing]

Recommendations for better observability:
1. [Recommendation 1]
2. [Recommendation 2]

## Confidence Assessment

**Confidence Level**: [High/Medium/Low]

**Strong Evidence**:
- [Evidence point 1]
- [Evidence point 2]

**Weak/Missing Evidence**:
- [Gap 1]
- [Gap 2]

## Prevention

[Initial thoughts on how to prevent recurrence - will be expanded in remediation step]
```

6. **Create Timeline Document**

Create `timeline.md` with this structure:

```markdown
# Incident Timeline

**Investigation**: [from triage.md]

## Timeline Overview

**Incident Duration**: [start time] to [end time] ([duration])

**Time to Detection**: [duration from start to first alert]

**Time to User Impact**: [duration from start to user-visible symptoms]

## Detailed Timeline

### [Timestamp] - Pre-Incident State
**State**: Normal operation
**Evidence**: [metrics showing normal state from metrics.md]

---

### [Timestamp] - Trigger Event
**Event**: [what happened]
**Source**: [where this came from - deployment, external event, etc.]
**Evidence**: [logs, metrics, or alerts showing this event]

---

### [Timestamp] - Initial Failure
**Event**: [first component that failed]
**Symptoms**: [what broke]
**Evidence**:
- Metrics: [specific metric change]
- Logs: [specific log pattern]

---

### [Timestamp] - Alert Fired
**Alert**: [alert name from alerts.md]
**Severity**: [level]
**Evidence**: [from alerts.md]

---

### [Timestamp] - Cascading Effect 1
**Event**: [how failure propagated]
**Impact**: [what else broke]
**Evidence**:
- Metrics: [specific metric change]
- Logs: [specific log pattern]

---

[Continue for each significant event]

---

### [Timestamp] - User Impact Began
**Symptoms**: [what users experienced]
**Scope**: [how many affected]
**Evidence**: [logs, metrics showing user impact]

---

### [Timestamp] - Resolution (if applicable)
**Event**: [what resolved the issue - rollback, restart, scale up, etc.]
**Evidence**: [metrics returning to normal, alerts clearing]

---

### [Timestamp] - Current State
**State**: [Ongoing / Resolved]
**Status**: [description of current state]

## Timeline Summary

**Key Observations**:
1. [Observation 1 - e.g., "5 minute gap between trigger and first alert"]
2. [Observation 2 - e.g., "Cascading failure took 10 minutes to propagate"]
3. [Observation 3 - e.g., "No logs during critical 2-minute window"]

**Critical Timestamps**:
- **Trigger**: [time]
- **First Failure**: [time]
- **First Alert**: [time]
- **User Impact**: [time]
- **Resolution**: [time]
```

## Quality Criteria

Before completing this step, verify:

1. **Root Cause Identified**: Clear statement of what failed and why
2. **Evidence-Based**: Conclusions supported by alerts, metrics, and logs
3. **Timeline Complete**: All significant events are documented chronologically
4. **Precise Timestamps**: Events have specific times (not just "around 14:00")
5. **Confidence Assessed**: Honest evaluation of evidence strength
6. **Alternatives Considered**: Other hypotheses were evaluated and ruled out
7. **Impact Quantified**: User and system impact are clearly stated
8. **Documents Created**: Both `root_cause.md` and `timeline.md` exist and are well-formatted

## Outputs

- `root_cause.md` - Comprehensive root cause analysis with evidence and confidence assessment
- `timeline.md` - Chronological timeline of the incident with precise timestamps

## Next Steps

- Create remediation plan (remediation step)
- Share findings with team
- Update runbooks based on learnings
