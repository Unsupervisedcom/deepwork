# Deep Investigation

## Objective

Execute the investigation plan from the triage step by querying logs, metrics, events, and service state to build an evidence-based understanding of the incident. Correlate findings across sources and produce root cause hypotheses with calibrated confidence levels.

## Task

Systematically work through each priority area from the triage document, using the tools identified in `context.md`. Record all findings — including negative results (per convention 6) — and correlate evidence across sources to build root cause hypotheses.

### Process

#### 1. Review Triage Plan and Adapt

Read both `triage.md` and `context.md` before starting any queries.

- Confirm the investigation plan priorities are still valid (the situation may have changed since triage)
- Note which tools are available for each planned check
- If the environment connectivity was blocked at triage, re-verify before proceeding
- If connectivity is still blocked, document this and proceed with repo/code analysis only

Announce the investigation plan to the user:

```
Beginning investigation based on triage plan.

Priority areas:
1. <area> — using <tool>
2. <area> — using <tool>
...

I'll work through these in order and report findings as I go.
```

#### 2. Kubernetes Investigation (if kubectl available)

Execute these checks in priority order. Skip sections that are not relevant to the incident based on triage.

**Cluster-level health:**
```bash
# Node status
kubectl get nodes -o wide

# Cluster events (last 1 hour, sorted by time)
kubectl get events --all-namespaces --sort-by='.lastTimestamp' --field-selector type!=Normal

# Resource pressure
kubectl top nodes 2>/dev/null
```

**Pod-level investigation (for affected namespaces/services):**
```bash
# Pod status in affected namespace
kubectl get pods -n <namespace> -o wide

# Pods not in Running state
kubectl get pods -n <namespace> --field-selector status.phase!=Running

# Recent pod events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Describe problematic pods (captures restart counts, conditions, events)
kubectl describe pod <pod-name> -n <namespace>

# Resource usage for affected pods
kubectl top pods -n <namespace> 2>/dev/null
```

**Log analysis (for affected pods):**
```bash
# Recent logs from affected pod
kubectl logs <pod-name> -n <namespace> --tail=200

# Previous container logs (if pod restarted)
kubectl logs <pod-name> -n <namespace> --previous --tail=200

# Logs since incident onset time
kubectl logs <pod-name> -n <namespace> --since-time=<RFC3339 timestamp>
```

**Deployment and rollout state:**
```bash
# Deployment status
kubectl get deployments -n <namespace>

# Rollout history
kubectl rollout history deployment/<name> -n <namespace>

# Current rollout status
kubectl rollout status deployment/<name> -n <namespace>
```

**Network and ingress:**
```bash
# Services and endpoints
kubectl get svc,endpoints -n <namespace>

# Ingress resources
kubectl get ingress -n <namespace>
```

Record every check with its output, even if the result is "no anomalies found." Note timestamps for all findings.

#### 3. Grafana MCP Investigation (if available)

Use Grafana MCP tools per conventions 55-59. All queries MUST specify explicit time ranges (convention 57).

**Check active alerts first (convention 59):**
- Query AlertManager for any currently firing or recently resolved alerts
- Record alert names, severity, and timing

**Dashboard queries:**
- Query the primary dashboard for affected services
- Focus on the four golden signals per convention 7:
  - **Latency**: Request duration percentiles (p50, p95, p99)
  - **Traffic**: Request rate (RPS)
  - **Errors**: Error rate and error ratio
  - **Saturation**: CPU, memory, disk, connection pool usage

**Loki log queries (conventions 11, 58):**
- MUST use label filters — never scan all streams
- SHOULD limit result counts to avoid timeouts
- Example patterns:
  ```
  {namespace="<ns>", app="<service>"} |= "error" | logfmt
  {namespace="<ns>", app="<service>"} | json | level="error"
  ```
- Search for:
  - Error messages matching the reported symptom
  - Stack traces or panics
  - Connection errors to downstream services
  - OOM or resource exhaustion messages

Record dashboard panel values with timestamps and Loki query results with matching log lines.

#### 4. Cloud CLI Investigation (if available)

Adapt these checks to the specific cloud provider available in `context.md`.

**Recent deployments and changes:**
- Check deployment history for the affected service
- Look for recent infrastructure changes (scaling events, config updates, certificate renewals)

**Service health:**
- Query managed service health (RDS, ElastiCache, Cloud SQL, managed Kubernetes status, etc.)
- Check for ongoing provider incidents (note: this may require web access)

**Resource utilization:**
- Check instance/container CPU and memory trends
- Check storage utilization
- Check network metrics (packet drops, connection limits)

#### 5. CI/CD Correlation

If a CI provider was detected in `context.md`, check for recent deployments that correlate with the incident onset:

```bash
# GitHub Actions — list recent workflow runs
gh run list --limit 10 --json databaseId,conclusion,createdAt,headBranch,name

# Check if a deployment happened near incident onset
gh run list --workflow deploy --limit 5
```

Correlate deployment times with incident onset. If a deployment preceded the incident by minutes, flag this as a strong correlation.

#### 6. Error Tracking Correlation (if available)

If sentry-cli or equivalent is available:

- Check for error spikes matching the incident timeframe
- Look for new error types that appeared around incident onset
- Note any error patterns that match the reported symptom

#### 7. Service-Specific Deep Checks

Based on the affected services identified in triage, perform targeted deep checks. These vary by service type:

**Database services:**
- Connection pool exhaustion
- Slow query logs
- Replication lag
- Lock contention
- Storage capacity

**Application services:**
- Health check endpoint responses
- Dependency connectivity (can the service reach its database, cache, external APIs?)
- Configuration correctness (environment variables, mounted secrets, feature flags)

**Networking/Ingress:**
- DNS resolution from inside the cluster
- Certificate validity and expiry
- Rate limiting or WAF blocks
- Load balancer health checks

**Queue/Worker services:**
- Queue depth and consumer lag
- Dead letter queue size
- Worker process health

For each service-specific check, record:
- What was checked
- The actual value or output
- Whether this is normal or anomalous
- How it relates to the reported symptom

#### 8. Correlate Findings

After completing all checks, correlate findings across sources:

1. **Build a timeline**: Order all findings chronologically to identify causal sequences
2. **Cross-reference**: Do log errors match metric spikes? Do deployment times align with symptom onset?
3. **Identify patterns**: Are multiple services affected, suggesting a shared dependency? Or is the issue isolated?
4. **Check for cascading failures**: Did one failure trigger others?

Per convention 4, cross-referencing between data sources MUST be performed before assigning high confidence to any hypothesis.

#### 9. Build Root Cause Hypotheses

Formulate root cause hypotheses based on correlated evidence. Each hypothesis MUST include:

- **Description**: What went wrong and why
- **Supporting evidence**: Specific log lines, metric values, events, and timestamps
- **Contradicting evidence**: Anything that weakens this hypothesis
- **Confidence level** per convention 5:
  - **High**: Verified with actual runtime data (checked real values, tested connections)
  - **Medium**: Supported by multiple indirect evidence points but not directly verified
  - **Low**: Plausible based on architecture/code analysis, but no direct evidence
- **Verification steps**: What additional checks would confirm or rule out this hypothesis

Rank hypotheses by confidence level, with the highest-confidence hypothesis first.

#### 10. Document Unresolved Questions

List anything that could not be determined during investigation:

- Tools that were unavailable and what they could have revealed
- Data that was inaccessible (e.g., logs already rotated, metrics retention expired)
- Hypotheses that could not be verified without additional access or expertise
- Areas that need human judgment or domain knowledge

## Output Format

Write the investigation findings to `investigation_findings.md` in the incident artifact directory (same directory as `triage.md`).

```markdown
# Investigation Findings

**Date**: YYYY-MM-DD HH:MM
**Incident**: <brief description from triage>
**Environment**: <environment from triage>
**Duration**: <how long the investigation took>

## Timeline

Chronological ordering of all events and findings relevant to the incident.

| Time (UTC) | Source | Event |
|------------|--------|-------|
| HH:MM | <source> | <what happened> |
| HH:MM | <source> | <what happened> |
| ... | ... | ... |

## Investigation Details

### Priority 1: <area from triage plan>

**Tool used**: <tool>
**Commands/queries run**: <specific commands>

**Findings**:
<what was discovered — include specific log lines, metric values, event details>

**Assessment**: <normal / anomalous / inconclusive>

---

### Priority 2: <area from triage plan>
...

(Repeat for each investigation area)

---

## Log Analysis

### Key Log Entries

```
<relevant log lines with timestamps>
```

**Interpretation**: <what these logs indicate>

### Log Patterns

- <pattern 1>: Observed N times between HH:MM and HH:MM
- <pattern 2>: ...

## Metrics Analysis

### <Metric Name>
- **Normal range**: <baseline value>
- **During incident**: <observed value>
- **Anomaly**: yes/no — <description>

(Repeat for each relevant metric)

## Root Cause Analysis

### Hypothesis 1: <description> — Confidence: High/Medium/Low

**What happened**: <narrative explanation>

**Supporting evidence**:
1. <evidence point with source and timestamp>
2. <evidence point with source and timestamp>
3. ...

**Contradicting evidence**:
- <anything that weakens this hypothesis, or "None identified">

**Verification steps**:
- <what would confirm this hypothesis>
- <what would rule it out>

---

### Hypothesis 2: <description> — Confidence: High/Medium/Low
...

(Repeat for each hypothesis, ordered by confidence)

## Cross-Reference Summary

| Finding | Log Evidence | Metric Evidence | Event Evidence |
|---------|-------------|-----------------|----------------|
| <finding> | <log ref> | <metric ref> | <event ref> |
| ... | ... | ... | ... |

## Negative Findings

The following areas were checked and found normal (per convention 6):
- <area checked>: <result — normal>
- <area checked>: <result — normal>

## Unresolved Questions

1. <question> — Blocked because: <reason>
2. <question> — Would need: <what access/tool/info is missing>
```

## Quality Criteria

- **Root Cause Hypothesis**: At least one root cause hypothesis is proposed and supported by evidence from logs and/or metrics. The hypothesis explains the reported symptom.
- **Evidence Trail**: Each finding includes specific evidence — log lines, metric values, timestamps — not just conclusions. The reader can trace every claim back to a data source.
- **Cross-Reference**: Findings from different sources (logs, metrics, events, deployment history) are cross-referenced to corroborate or rule out hypotheses per convention 4. High confidence is only assigned when multiple sources agree.
- **Honest Confidence**: Confidence levels accurately reflect verification status per convention 5. High confidence is reserved for findings verified with actual runtime data. Medium is for multiple indirect evidence points. Low is for architecture-based reasoning without direct evidence.
- **Negative Findings Documented**: Areas that were checked and found normal are documented per convention 6, narrowing the scope for follow-up investigation.
- **No Destructive Actions**: Per conventions 1 and 2, no destructive actions were taken. No services were restarted, no pods were deleted, no config was changed.
- **Triage Plan Followed**: Each priority area from the triage document is addressed in the investigation findings, even if the result was "not applicable" or "tool unavailable."

## Context

This step is the investigative core of the incident_investigation and quick_investigate workflows. It takes the structured plan from triage and executes it against live systems (or code/config analysis when live access is unavailable).

The key discipline is systematic execution: follow the plan priorities, record everything, and cross-reference before drawing conclusions. Per convention 4, high confidence requires corroboration across data sources — a single log line or metric spike is not sufficient for a High confidence rating.

Per conventions 1 and 2, this step is strictly read-only. The agent MUST NOT take any remediation actions during investigation — no pod restarts, no config changes, no deployments. Remediation suggestions are produced in the incident_report step.

When tools are unavailable, the agent MUST note what could not be checked and what the missing data might have revealed (per convention 56). This prevents false confidence from an incomplete investigation.
