# Check Alerts

## Objective

Query Alertmanager for active and recent alerts related to the investigation scope. This step uses a specialized subagent to prevent alert data from bloating the main context.

## Task

**CRITICAL**: Do NOT query Grafana MCP tools directly in this step. Instead, delegate all alert queries to an isolated subagent.

### For Claude Code Users (Recommended)

Use the Task tool with the `alertmanager-analyst` subagent:

```
Use the Task tool to spawn the alertmanager-analyst subagent with this prompt:

"Query Alertmanager for alerts related to the investigation in triage.md. 
Focus on:
- Time range: [from triage.md]
- Services: [from triage.md]

Return a YAML summary with:
- Total alert count
- Alerts grouped by severity (critical, warning, info)
- Top 10 most relevant alerts with: name, severity, status, start time, labels
- Notable patterns or correlations

Max 10 alerts in output. If more exist, summarize the patterns."

Wait for the subagent to complete and return its YAML summary.
```

The `alertmanager-analyst` subagent is defined in `.claude/agents/alertmanager-analyst.md` and has access to the `mcp__grafana__get_alerts` tool. It will return a structured summary, NOT raw alert data.

### For Gemini CLI Users (Fallback)

Since Gemini CLI does not support isolated subagents, you MUST manually apply strict output limits:

1. Read `triage.md` to understand the scope
2. Query Alertmanager using `mcp__grafana__get_alerts` with appropriate filters
3. **CRITICAL OUTPUT LIMITS**:
   - Return max 10 alerts total
   - Group by severity (critical, warning, info)
   - Summarize patterns rather than listing every alert
   - Truncate long alert messages to 100 characters
4. Do NOT include full alert payloads in your response

### Step-by-Step Process

1. **Read Triage Context**
   - Read `triage.md` to understand time range, affected services, and investigation scope

2. **Delegate to Subagent (Claude Code) OR Apply Limits (Gemini)**
   - **Claude Code**: Use Task tool with `alertmanager-analyst` subagent
   - **Gemini CLI**: Query directly with strict output limits

3. **Review Alert Summary**
   - Verify the summary is structured and concise
   - Check that it answers: Are there active alerts? What patterns exist?
   - Ensure no raw alert JSON is present

4. **Create Alerts Document**

Create `alerts.md` with this structure:

```markdown
# Alertmanager Analysis

**Investigation**: [from triage.md]
**Time Range**: [from triage.md]
**Query Time**: [current timestamp]

## Summary

- **Total Alerts**: [count]
- **Critical**: [count]
- **Warning**: [count]
- **Info**: [count]

## Critical Alerts (Top Priority)

| Alert Name | Status | Started | Labels | Description |
|------------|--------|---------|--------|-------------|
| [name] | [firing/resolved] | [timestamp] | [key=value] | [brief description] |
...

## Warning Alerts

| Alert Name | Status | Started | Labels | Description |
|------------|--------|---------|--------|-------------|
| [name] | [firing/resolved] | [timestamp] | [key=value] | [brief description] |
...

## Patterns & Insights

- [Pattern 1: e.g., "All critical alerts are for service-x"]
- [Pattern 2: e.g., "Alerts started at same time as incident"]
- [Pattern 3: e.g., "No alerts for service-y despite issue"]

## Correlation with Issue

[Brief analysis of how alerts relate to the reported issue]

## Next Steps

- Investigate metrics for alerted components (metrics_analysis step)
- Cross-reference alert timing with log patterns (log_investigation step)
```

## Quality Criteria

Before completing this step, verify:

1. **Subagent Used (Claude) OR Limits Applied (Gemini)**: Alert queries were delegated or strictly limited
2. **Structured Output**: Alerts are in a table format, not raw JSON
3. **Max 10 Alerts**: No more than 10 alerts are detailed (others are summarized)
4. **Severity Grouped**: Alerts are grouped by severity level
5. **Patterns Identified**: Summary includes notable patterns or correlations
6. **No Context Bloat**: Main context does not contain raw alert payloads
7. **Document Created**: `alerts.md` file exists and is well-formatted

## Output

- `alerts.md` - Structured summary of Alertmanager alerts (max 10 detailed, rest summarized)

## Platform Notes

- **Claude Code**: The `alertmanager-analyst` subagent will be automatically available in `.claude/agents/` after `deepwork sync`
- **Gemini CLI**: No subagent support; instructions include inline summarization rules
