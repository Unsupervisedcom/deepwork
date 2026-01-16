# Metrics Analysis

## Objective

Query Prometheus for relevant metrics to identify trends, anomalies, and correlations. This step uses a specialized subagent to prevent metric data from bloating the main context.

## Task

**CRITICAL**: Do NOT query Grafana MCP tools directly in this step. Instead, delegate all metric queries to an isolated subagent.

### For Claude Code Users (Recommended)

Use the Task tool with the `prometheus-analyst` subagent:

```
Use the Task tool to spawn the prometheus-analyst subagent with this prompt:

"Query Prometheus for metrics related to the investigation:
- Time range: [from triage.md]
- Services: [from triage.md]
- Focus areas: [from alerts.md - metrics mentioned in alerts]

Return a YAML summary with:
- Key metrics queried (with PromQL)
- Trend summaries (increasing/decreasing/stable)
- Max 10 data points per metric (start, middle, end values)
- Notable anomalies or spikes
- Correlations between metrics

Format each metric section as:
  metric_name:
    query: [PromQL]
    trend: [increasing/decreasing/stable/spike]
    values: [max 10 sample points]
    analysis: [brief interpretation]

Max 10 metrics total. If more are relevant, prioritize by importance."

Wait for the subagent to complete and return its YAML summary.
```

The `prometheus-analyst` subagent is defined in `.claude/agents/prometheus-analyst.md` and has access to the `mcp__grafana__query_prometheus` tool. It will return a structured summary with trends, NOT raw time series data.

### For Gemini CLI Users (Fallback)

Since Gemini CLI does not support isolated subagents, you MUST manually apply strict output limits:

1. Read `triage.md` and `alerts.md` to understand scope and focus areas
2. Query Prometheus using `mcp__grafana__query_prometheus` with appropriate PromQL queries
3. **CRITICAL OUTPUT LIMITS**:
   - Query max 10 metrics total
   - Return max 10 data points per metric (sample key points, not every value)
   - Describe trends (increasing/decreasing/stable/spike) instead of listing all values
   - Focus on anomalies and changes, not steady-state data
4. Do NOT include full time series in your response

### Step-by-Step Process

1. **Read Context**
   - Read `triage.md` for time range and affected services
   - Read `alerts.md` for metrics mentioned in alerts

2. **Identify Key Metrics**
   - Determine which metrics to query based on:
     - Services mentioned in triage
     - Metrics referenced in alerts
     - Common metrics: CPU, memory, request rate, error rate, latency
   - Prioritize metrics most likely to reveal root cause

3. **Delegate to Subagent (Claude Code) OR Apply Limits (Gemini)**
   - **Claude Code**: Use Task tool with `prometheus-analyst` subagent
   - **Gemini CLI**: Query directly with strict output limits

4. **Review Metrics Summary**
   - Verify the summary includes trends and anomalies
   - Check that data points are sampled (not exhaustive)
   - Ensure no raw time series data is present

5. **Create Metrics Document**

Create `metrics.md` with this structure:

```markdown
# Prometheus Metrics Analysis

**Investigation**: [from triage.md]
**Time Range**: [from triage.md]
**Query Time**: [current timestamp]

## Key Metrics Overview

| Metric | Trend | Anomaly | Correlation with Issue |
|--------|-------|---------|------------------------|
| [name] | [increasing/decreasing/stable/spike] | [yes/no] | [brief note] |
...

## Detailed Metrics

### [Metric 1: e.g., CPU Usage]

**PromQL**: `[query]`

**Trend**: [increasing/decreasing/stable/spike]

**Sample Values** (max 10 points):
- [timestamp]: [value]
- [timestamp]: [value]
- ...

**Analysis**: [Brief interpretation - what does this tell us?]

---

### [Metric 2: e.g., Request Error Rate]

**PromQL**: `[query]`

**Trend**: [increasing/decreasing/stable/spike]

**Sample Values** (max 10 points):
- [timestamp]: [value]
- [timestamp]: [value]
- ...

**Analysis**: [Brief interpretation]

---

[Repeat for up to 10 metrics total]

## Anomalies & Correlations

### Identified Anomalies
1. [Anomaly 1: e.g., "CPU spiked to 95% at 14:23:15"]
2. [Anomaly 2: e.g., "Error rate jumped 10x starting at 14:22:30"]
...

### Cross-Metric Correlations
- [Correlation 1: e.g., "CPU spike coincides with error rate increase"]
- [Correlation 2: e.g., "Memory usage flat despite CPU spike"]
...

## Insights

[1-2 paragraph analysis of what the metrics reveal about the issue]

## Next Steps

- Investigate logs around anomaly timestamps (log_investigation step)
- Cross-reference metrics with alert timing
```

## Quality Criteria

Before completing this step, verify:

1. **Subagent Used (Claude) OR Limits Applied (Gemini)**: Metric queries were delegated or strictly limited
2. **Sampled Data**: Max 10 data points per metric (not full time series)
3. **Trend Summaries**: Each metric has a trend description (increasing/decreasing/stable/spike)
4. **Max 10 Metrics**: No more than 10 metrics are analyzed in detail
5. **Anomalies Highlighted**: Notable spikes, drops, or changes are called out
6. **Correlations Noted**: Relationships between metrics are identified
7. **No Context Bloat**: Main context does not contain raw time series data
8. **Document Created**: `metrics.md` file exists and is well-formatted

## Output

- `metrics.md` - Structured summary of Prometheus metrics with trends and anomalies (max 10 metrics, 10 points each)

## Platform Notes

- **Claude Code**: The `prometheus-analyst` subagent will be automatically available in `.claude/agents/` after `deepwork sync`
- **Gemini CLI**: No subagent support; instructions include inline summarization rules
