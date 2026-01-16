# Log Investigation

## Objective

Query Loki for relevant log entries to identify errors, patterns, and root causes. This step uses a specialized subagent to prevent log data from bloating the main context.

## Task

**CRITICAL**: Do NOT query Grafana MCP tools directly in this step. Instead, delegate all log queries to an isolated subagent. Logs are the highest risk for context bloat.

### For Claude Code Users (Recommended)

Use the Task tool with the `loki-analyst` subagent:

```
Use the Task tool to spawn the loki-analyst subagent with this prompt:

"Query Loki for logs related to the investigation:
- Time range: [from triage.md]
- Services: [from triage.md]
- Focus on timestamps from: [anomaly times from metrics.md]
- Keywords: [error codes, service names from alerts.md]

Return a YAML summary with:
- Total log entries found
- Log patterns identified (e.g., error types, frequency)
- Max 5 representative log lines (not full logs)
- Each log line must be truncated to 200 chars max
- Error categories and counts
- Timeline of key events

Format:
  patterns:
    - pattern: [description]
      count: [number]
      sample: [truncated log line]
  
  timeline:
    - timestamp: [time]
      event: [brief description]
      source: [service]
  
  representative_logs:
    - [truncated log 1, max 200 chars]
    - [truncated log 2, max 200 chars]
    - ... (max 5 total)

Max 5 log lines in output. Summarize patterns instead of listing every log."

Wait for the subagent to complete and return its YAML summary.
```

The `loki-analyst` subagent is defined in `.claude/agents/loki-analyst.md` and has access to the `mcp__grafana__query_loki` tool. It will return a structured summary with patterns, NOT raw log dumps.

### For Gemini CLI Users (Fallback)

Since Gemini CLI does not support isolated subagents, you MUST manually apply STRICT output limits:

1. Read `triage.md`, `alerts.md`, and `metrics.md` to understand scope and focus
2. Query Loki using `mcp__grafana__query_loki` with appropriate LogQL queries
3. **CRITICAL OUTPUT LIMITS**:
   - Return max 5 log lines total
   - Truncate each log line to 200 characters max
   - Focus on error patterns and counts, not individual logs
   - Describe patterns instead of listing many similar logs
   - Use timestamp sampling (start, anomaly times, end)
4. Do NOT include full log dumps, stack traces, or verbose logs

### Step-by-Step Process

1. **Read Context**
   - Read `triage.md` for time range and affected services
   - Read `alerts.md` for error indicators
   - Read `metrics.md` for anomaly timestamps to focus on

2. **Identify Log Query Focus**
   - Service names from triage
   - Error keywords from alerts
   - Timestamp windows around metric anomalies
   - Specific error codes or patterns mentioned in investigation

3. **Delegate to Subagent (Claude Code) OR Apply Limits (Gemini)**
   - **Claude Code**: Use Task tool with `loki-analyst` subagent
   - **Gemini CLI**: Query directly with STRICT output limits

4. **Review Log Summary**
   - Verify max 5 log lines are included
   - Check that logs are truncated to 200 chars
   - Ensure patterns are summarized, not listed exhaustively

5. **Create Logs Document**

Create `logs.md` with this structure:

```markdown
# Loki Log Analysis

**Investigation**: [from triage.md]
**Time Range**: [from triage.md]
**Query Time**: [current timestamp]

## Summary

- **Total Log Entries**: [approximate count]
- **Services Queried**: [list]
- **Primary Focus**: [error types, time windows, etc.]

## Log Patterns

| Pattern | Count | Severity | First Seen | Last Seen |
|---------|-------|----------|------------|-----------|
| [e.g., "Connection timeout to DB"] | [count] | [ERROR/WARN] | [timestamp] | [timestamp] |
| [e.g., "OOM killer invoked"] | [count] | [CRITICAL] | [timestamp] | [timestamp] |
...

## Timeline of Key Events

| Timestamp | Event | Service | Severity |
|-----------|-------|---------|----------|
| [time] | [brief event description] | [service] | [level] |
| [time] | [brief event description] | [service] | [level] |
...

## Representative Log Entries (Max 5)

### 1. [Brief description]
**Timestamp**: [time]
**Service**: [name]
**Level**: [ERROR/WARN/INFO]
```
[Truncated log line, max 200 chars]...
```

### 2. [Brief description]
**Timestamp**: [time]
**Service**: [name]
**Level**: [ERROR/WARN/INFO]
```
[Truncated log line, max 200 chars]...
```

[Repeat for max 5 total]

## Error Categories

### [Category 1: e.g., Database Errors]
- **Count**: [number]
- **Pattern**: [description]
- **Impact**: [brief note]

### [Category 2: e.g., Network Errors]
- **Count**: [number]
- **Pattern**: [description]
- **Impact**: [brief note]

...

## Cross-Reference with Metrics

- **Correlation 1**: [e.g., "Error spike at 14:23 matches CPU spike"]
- **Correlation 2**: [e.g., "No logs between 14:20-14:22 suggests service crash"]
...

## Insights

[1-2 paragraph analysis of what the logs reveal]

Key findings:
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

## Next Steps

- Synthesize findings into root cause analysis (root_cause step)
- Create timeline of incident progression
```

## Quality Criteria

Before completing this step, verify:

1. **Subagent Used (Claude) OR Limits Applied (Gemini)**: Log queries were delegated or STRICTLY limited
2. **Max 5 Logs**: No more than 5 log lines are included in detail
3. **Truncated Logs**: Each log line is truncated to 200 characters max
4. **Patterns Summarized**: Similar logs are grouped and counted, not listed individually
5. **Timeline Created**: Key events are organized chronologically
6. **Cross-Referenced**: Logs are correlated with alerts and metrics
7. **No Context Bloat**: Main context does not contain log dumps or stack traces
8. **Document Created**: `logs.md` file exists and is well-formatted

## Output

- `logs.md` - Structured summary of Loki logs with patterns and representative samples (max 5 logs, 200 chars each)

## Platform Notes

- **Claude Code**: The `loki-analyst` subagent will be automatically available in `.claude/agents/` after `deepwork sync`
- **Gemini CLI**: No subagent support; instructions include inline summarization rules
- **Warning**: Loki logs are the highest risk for context bloat. Strict limits are essential.
