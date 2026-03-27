# Inspect Dashboards

## Objective

Catalog all existing Grafana dashboards for a target service or organization, assess coverage of the four golden signals (latency, traffic, errors, saturation), and identify observability gaps that need to be addressed.

## Task

Use the Grafana MCP (when available) or fall-back discovery methods to build a comprehensive picture of the current dashboard landscape. The goal is to produce a gap analysis that drives the next step (`develop_dashboard`), so thoroughness matters more than speed.

**Important**: Use the AskUserQuestion tool to confirm the target service or organization before querying dashboards. Do not assume -- the user may want to scope the inspection to a single service, a namespace, or an entire organization's folder.

### Process

1. **Read context.md and confirm tooling**
   - Read the `context.md` file produced by `gather_context`.
   - Confirm whether Grafana MCP tools are available in this session. Look for explicit mention of Grafana MCP under the detected tools section.
   - Note which data sources are available (Prometheus, Loki, CloudWatch, Datadog, VictoriaMetrics, etc.) -- this affects what golden signal queries are feasible.

2. **Confirm scope with the user**
   - Use AskUserQuestion to ask which service, namespace, team, or Grafana folder to inspect.
   - If the user provides a broad scope (e.g., "all services"), clarify whether they want a summary-level pass or deep per-service analysis.
   - Record the agreed scope in the output.

3. **Enumerate existing dashboards**

   **If Grafana MCP is available:**
   - Use the Grafana MCP `search_dashboards` tool (or equivalent) to list all dashboards matching the scope.
   - For each dashboard returned, retrieve its metadata: title, UID, folder, tags, last modified date, and panel count.
   - If the Grafana MCP supports reading panel definitions, fetch panel details to understand what metrics each dashboard queries.

   **If Grafana MCP is NOT available, use fall-back methods in order of preference:**
   - Search the repository for Grafana dashboard JSON files: `**/*dashboard*.json`, `**/grafana/**/*.json`, `**/dashboards/**/*.json`.
   - Check Helm chart values for Grafana sidecar provisioning: look for `grafana.dashboards` or `grafana.dashboardProviders` keys in `values.yaml` or `values/*.yaml`.
   - Check for Kubernetes ConfigMaps that provision dashboards: search for ConfigMaps with the label `grafana_dashboard: "1"` or equivalent annotation.
   - Check for Terraform/Pulumi resources that create Grafana dashboards.
   - Note that fall-back methods may not capture dashboards created manually through the Grafana UI.

4. **Assess golden signal coverage for each dashboard**

   For every dashboard found, evaluate whether it covers each of the four golden signals defined in convention 7:

   | Golden Signal | What to look for |
   |---------------|-----------------|
   | **Latency** | Request duration histograms, p50/p95/p99 panels, response time graphs, `histogram_quantile` queries, `_duration_seconds` metrics |
   | **Traffic** | Request rate (RPS) panels, throughput graphs, `rate()` on request counters, `_requests_total` metrics |
   | **Errors** | Error rate panels, HTTP 5xx/4xx status code distribution, error ratio (`errors / total`), `_errors_total` metrics |
   | **Saturation** | CPU usage, memory usage, disk I/O, connection pool utilization, queue depth, `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` |

   Mark each signal as:
   - **Covered** -- at least one panel meaningfully tracks this signal
   - **Partial** -- a related metric exists but does not give actionable insight (e.g., total requests but no rate)
   - **Missing** -- no panel addresses this signal

5. **Check dashboard best practices per conventions 8-9**
   - **Time range selectors (convention 8)**: Does the dashboard allow the user to change the time range? Does it default to a reasonable window (ideally last 1 hour)?
   - **Alert rule references (convention 9)**: Are any alert rules linked to or referenced from the dashboard? Are there annotations showing alert firing history? If alerts exist elsewhere (AlertManager, Grafana Alerting), note whether dashboards reference them.
   - **Label filters (convention 11)**: Do Loki-based panels use label filters, or do they scan all streams?
   - **Explicit time ranges (convention 12)**: Do dashboard queries use explicit `$__range` or time window variables, or rely on implicit defaults?

6. **Identify gaps**

   Synthesize findings into clear gap categories:

   - **Services without dashboards**: List any services mentioned in context.md or discovered in the infrastructure that have no corresponding dashboard.
   - **Missing golden signals**: For each dashboard, list which of the four signals are missing or only partially covered.
   - **Stale dashboards**: Flag dashboards that have not been modified in over 90 days, especially if the service they monitor has changed significantly.
   - **Missing alert integration**: Dashboards that monitor critical services but have no associated alert rules.
   - **Data source gaps**: Services that emit metrics but are not connected to any dashboard data source.

7. **Formulate recommendations**

   For each gap, provide a concrete recommendation:
   - Which dashboard to create or update
   - Which golden signals to add
   - Which data source to use
   - Priority level (Critical / High / Medium / Low) based on the service's importance and the severity of the gap

## Output Format

### dashboard_assessment.md

A structured assessment document that serves as the input to the `develop_dashboard` step.

**Structure**:
```markdown
# Dashboard Assessment

## Scope
- **Target**: [service/org/namespace inspected]
- **Date**: [assessment date]
- **Method**: [Grafana MCP / Repository JSON / Helm values / manual]

## Existing Dashboards

| # | Dashboard Name | Folder/Location | Latency | Traffic | Errors | Saturation | Last Modified | Alert Rules |
|---|---------------|-----------------|---------|---------|--------|------------|---------------|-------------|
| 1 | [name]        | [folder]        | [Y/P/N] | [Y/P/N] | [Y/P/N]| [Y/P/N]    | [date]        | [Y/N]       |
| 2 | ...           | ...             | ...     | ...     | ...    | ...        | ...           | ...         |

**Legend**: Y = Covered, P = Partial, N = Missing

### Dashboard Details

#### [Dashboard Name]
- **UID**: [uid if available]
- **Purpose**: [what this dashboard monitors]
- **Data Sources**: [Prometheus, Loki, etc.]
- **Panel Count**: [number]
- **Time Range Default**: [default time range]
- **Golden Signal Notes**: [details on what is covered/missing]

[Repeat for each dashboard]

## Gap Analysis

### Services Without Dashboards
| Service | Environment | Priority | Notes |
|---------|-------------|----------|-------|
| [name]  | [env]       | [level]  | [why] |

### Missing Golden Signals
| Dashboard | Missing Signals | Impact | Priority |
|-----------|----------------|--------|----------|
| [name]    | [signals]      | [impact]| [level] |

### Stale Dashboards
| Dashboard | Last Modified | Service Changed Since? | Action |
|-----------|---------------|----------------------|--------|
| [name]    | [date]        | [Y/N/Unknown]        | [action]|

### Missing Alert Integration
| Dashboard | Service Criticality | Recommendation |
|-----------|-------------------|----------------|
| [name]    | [level]           | [action]       |

## Recommendations

| # | Recommendation | Dashboard | Signals to Add | Data Source | Priority | Effort |
|---|---------------|-----------|----------------|-------------|----------|--------|
| 1 | [action]      | [name]    | [signals]      | [source]    | [level]  | [est]  |

## Limitations
- [Any limitations of the inspection method used]
- [Dashboards that may exist but could not be discovered]
- [Data sources that were not accessible]
```

## Quality Criteria

- All existing dashboards for the target scope are cataloged with their purpose and data sources
- Each dashboard is assessed against all four golden signals with clear Y/P/N ratings
- Convention compliance (conventions 7-9, 11-12) is explicitly checked for each dashboard
- Services without dashboards are identified by cross-referencing against context.md infrastructure inventory
- Gaps are prioritized by service criticality and signal importance
- Recommendations are specific and actionable -- each one identifies the exact dashboard, signals, and data source
- The assessment method (Grafana MCP vs. fall-back) is documented so the reader understands coverage confidence
- Stale dashboards are flagged with a clear threshold (90+ days without modification)

## Context

This step is the first of two in the `dashboard_management` workflow. It produces the assessment that drives the `develop_dashboard` step, where identified gaps are addressed by creating or updating dashboard definitions. A thorough inspection here prevents blind spots in the development phase -- missing a service or signal at this stage means it will not be addressed later.

The four golden signals (latency, traffic, errors, saturation) come from Google's SRE handbook and are codified in convention 7 as the minimum observability standard for every production service. The purpose of this step is not just to list dashboards, but to measure how well the current dashboard estate covers these signals and to produce a prioritized remediation plan.
