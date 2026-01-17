# Project Context for env_investigate

This is the source of truth for the `env_investigate` standard job - a production debugging workflow using Grafana MCP with isolated observability subagents.

## Codebase Structure

- Source location: `src/deepwork/standard_jobs/env_investigate/`
- Working copy: `.deepwork/jobs/env_investigate/`
- Templates: `templates/` directory within each location
- Subagent definitions: `src/deepwork/templates/claude/agents/`

## Dual Location Maintenance

**Important**: This job exists in two locations that must be kept in sync:

1. **Source of truth**: `src/deepwork/standard_jobs/env_investigate/`
   - This is where changes should be made first
   - Tracked in version control

2. **Working copy**: `.deepwork/jobs/env_investigate/`
   - Must be updated after changes to source
   - Used by `deepwork sync` to generate commands

After making changes to the source, copy files to the working copy:
```bash
cp src/deepwork/standard_jobs/env_investigate/job.yml .deepwork/jobs/env_investigate/
cp src/deepwork/standard_jobs/env_investigate/steps/*.md .deepwork/jobs/env_investigate/steps/
cp -r src/deepwork/standard_jobs/env_investigate/templates/* .deepwork/jobs/env_investigate/templates/ 2>/dev/null || true
```

## File Organization

```
env_investigate/
├── AGENTS.md              # This file
├── job.yml                # Job definition
├── make_new_job.sh        # Script to create investigation structure
├── steps/
│   ├── triage.md          # Define investigation scope
│   ├── alert_check.md     # Query Alertmanager via subagent
│   ├── metrics_analysis.md    # Query Prometheus via subagent
│   ├── log_investigation.md   # Query Loki via subagent
│   ├── root_cause.md      # Synthesize findings
│   └── remediation.md     # Create action plan
└── templates/
    ├── triage.md.template         # Investigation scope template
    ├── alerts.md.template         # Alerts summary template
    ├── metrics.md.template        # Metrics summary template
    ├── logs.md.template           # Logs summary template
    ├── root_cause.md.template     # Root cause template
    ├── timeline.md.template       # Timeline template
    └── remediation.md.template    # Remediation plan template
```

## Observability Subagent Meta-Framework

This job demonstrates a **meta-framework pattern** for working with observability tools that return large amounts of data. The pattern prevents context bloat by delegating all raw data queries to isolated subagents.

### The Problem

Observability queries (especially logs) can return massive amounts of data:
- Prometheus: 1000+ data points per metric
- Alertmanager: 50+ alerts with full payloads
- Loki: 10,000+ log lines with stack traces

This data quickly overwhelms the agent's context window, making iterative investigation impossible.

### The Solution: Isolated Subagents

**Key Principle**: Raw observability data never enters the main investigation context.

Instead, specialized analyst subagents:
1. Receive specific query requirements from main agent
2. Query observability tools directly (Grafana MCP)
3. Apply strict output contracts (max data points, truncation)
4. Return only structured YAML summaries

### Subagent Definitions

Three analyst subagents for Claude Code (in `src/deepwork/templates/claude/agents/`):

| Subagent | Tool | Output Contract | Files |
|----------|------|-----------------|-------|
| `alertmanager-analyst` | `mcp__grafana__get_alerts` | Max 10 alerts, grouped by severity | `.claude/agents/alertmanager-analyst.md` |
| `prometheus-analyst` | `mcp__grafana__query_prometheus` | Max 10 data points per metric, trend summaries | `.claude/agents/prometheus-analyst.md` |
| `loki-analyst` | `mcp__grafana__query_loki` | Max 5 log lines, 200 char truncation | `.claude/agents/loki-analyst.md` |

**Platform Support**:
- **Claude Code**: Full support via Task tool + `.claude/agents/*.md` definitions
- **Gemini CLI**: Inline summarization rules (no isolated subagents available)

### How Subagents Work (Claude Code)

Step instructions delegate queries to subagents:

```markdown
### For Claude Code Users (Recommended)

Use the Task tool with the `alertmanager-analyst` subagent:

\`\`\`
Use the Task tool to spawn the alertmanager-analyst subagent with this prompt:

"Query Alertmanager for alerts related to the investigation in triage.md.
Focus on:
- Time range: [from triage.md]
- Services: [from triage.md]

Return a YAML summary with:
- Total alert count
- Alerts grouped by severity
- Top 10 most relevant alerts
- Notable patterns

Max 10 alerts in output."

Wait for the subagent to complete and return its YAML summary.
\`\`\`
```

The subagent returns structured YAML (never raw data):
```yaml
summary:
  total_alerts: 23
  critical: 5
alerts:
  - name: HighErrorRate
    severity: critical
    started_at: 2026-01-16T14:23:15Z
    # ... max 10 total
patterns:
  - pattern: "Multiple services showing error spikes"
    count: 18
```

### Adapting This Pattern

To adapt this meta-framework for other observability tools:

1. **Identify high-volume data sources** (e.g., traces, events, databases)
2. **Create subagent templates** in `src/deepwork/templates/claude/agents/`
3. **Define strict output contracts** (max items, truncation rules)
4. **Update step instructions** to delegate queries
5. **Add fallback rules** for platforms without subagent support

Example subagent template structure:
```markdown
# [Tool Name] Analyst

**Role**: Query [tool] and return structured summaries

**Tools**: `mcp__[tool]__[method]`

**Output Contract**: Max [N] items, [format], [truncation rules]

**Critical Rules**:
1. Max [N] items in output
2. Truncate to [X] chars
3. Group similar items
4. Return YAML only
```

## Workflow Pattern

The 6-step investigation workflow follows a structured pattern:

1. **Triage** (manual) - Define scope, no external queries
2. **Alert Check** (subagent) - Delegate to alertmanager-analyst
3. **Metrics Analysis** (subagent) - Delegate to prometheus-analyst
4. **Log Investigation** (subagent) - Delegate to loki-analyst
5. **Root Cause** (synthesis) - Use summaries from steps 1-4
6. **Remediation** (planning) - Create action plan with monitoring improvements

**Key Characteristics**:
- Each step produces a markdown artifact
- Steps 2-4 use subagents (or inline limits for Gemini)
- Steps 5-6 synthesize without additional queries
- All artifacts stay in main context (summaries only)

## Version Management

- Version is tracked in `job.yml`
- Bump patch version (1.0.x) for instruction improvements
- Bump minor version (1.x.0) for new steps or subagent changes
- Bump major version (2.0.0) for breaking workflow changes
- Always update changelog when bumping version

## Subagent Template Updates

When updating subagent templates in `src/deepwork/templates/claude/agents/`:
1. Modify the `.j2` template file
2. Run `deepwork sync` to regenerate `.claude/agents/*.md`
3. Test with a sample investigation
4. Update this AGENTS.md if output contracts change

## Dependencies

- **Required**: Grafana MCP server configured with datasources
  - Prometheus (metrics)
  - Alertmanager (alerts)
  - Loki (logs)
- **Recommended**: Claude Code for full subagent support
- **Alternative**: Gemini CLI with inline summarization

## Known Issues and Workarounds

- **Issue**: Gemini CLI doesn't support isolated subagents
  - **Workaround**: Step instructions include inline output limits and manual summarization rules

- **Issue**: Very large time ranges can still return too much data
  - **Workaround**: Triage step instructs users to narrow time ranges to 1-24 hours

- **Issue**: Stack traces in logs can exceed 200 char limit
  - **Workaround**: loki-analyst truncates and summarizes (e.g., "Java NPE in Handler.process:234")

## Example Investigation Flow

```bash
# 1. Start investigation
/env_investigate.triage
# Creates: triage.md (scope, time range, services)

# 2. Check alerts (spawns alertmanager-analyst subagent)
/env_investigate.alert_check
# Creates: alerts.md (max 10 alerts, patterns)

# 3. Analyze metrics (spawns prometheus-analyst subagent)
/env_investigate.metrics_analysis
# Creates: metrics.md (max 10 metrics, trends)

# 4. Investigate logs (spawns loki-analyst subagent)
/env_investigate.log_investigation
# Creates: logs.md (max 5 logs, patterns)

# 5. Determine root cause (synthesis)
/env_investigate.root_cause
# Creates: root_cause.md, timeline.md

# 6. Plan remediation
/env_investigate.remediation
# Creates: remediation.md (actions, monitoring improvements)
```

## Last Updated

- Date: 2026-01-17
- From conversation about: Restructuring to follow standard job pattern with AGENTS.md explaining the subagent meta-framework
