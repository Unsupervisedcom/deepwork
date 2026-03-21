# Develop Dashboard

## Objective

Create or update Grafana dashboard definitions to close the observability gaps identified in the dashboard assessment, ensuring every targeted service has coverage of the four golden signals (latency, traffic, errors, saturation).

## Task

Read the `dashboard_assessment.md` produced by the `inspect_dashboards` step and systematically address each gap by producing Grafana dashboard JSON files, Helm provisioning configs, or by creating dashboards directly via the Grafana MCP. Every dashboard produced must cover the four golden signals and follow the conventions for time ranges, alert references, and query best practices.

**Important**: Do not create dashboards speculatively. Only address gaps that are documented in `dashboard_assessment.md`. If the assessment is incomplete or unclear, use AskUserQuestion to clarify before proceeding.

### Process

1. **Read the dashboard assessment**
   - Read `dashboard_assessment.md` from the previous step.
   - Extract the list of recommendations, ordered by priority.
   - For each recommendation, note: the target service, which golden signals are missing, which data source to use, and whether this is a new dashboard or an update to an existing one.

2. **Determine available data sources**
   - Review `context.md` for detected monitoring infrastructure.
   - Identify which metric backends are available and what metric naming conventions they use:

     | Backend | Typical Metric Patterns |
     |---------|------------------------|
     | **Prometheus** | `http_request_duration_seconds`, `http_requests_total`, `process_cpu_seconds_total` |
     | **VictoriaMetrics** | Same as Prometheus (compatible query language) |
     | **CloudWatch** | `AWS/ELB/Latency`, `AWS/EC2/CPUUtilization` |
     | **Datadog** | `trace.http.request.duration`, `aws.ec2.cpuutilization` |
     | **Loki** | Log-derived metrics via LogQL `rate()`, `count_over_time()` |

   - If the data source is unclear or multiple options exist, ask the user which to target.
   - Note any custom metric naming conventions used in the project (e.g., application-specific prefixes).

3. **Design dashboard panels for each golden signal**

   For each dashboard to create or update, design panels covering all four golden signals:

   **Latency panels:**
   - Request duration histogram heatmap (shows distribution over time)
   - Percentile line chart: p50, p95, p99 request duration
   - Example Prometheus query: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="$service"}[$__rate_interval])) by (le))`
   - Consider splitting by endpoint/route if cardinality is manageable

   **Traffic panels:**
   - Request rate (RPS) -- total and per-endpoint
   - Throughput (bytes/sec for data-heavy services)
   - Example Prometheus query: `sum(rate(http_requests_total{service="$service"}[$__rate_interval]))`
   - Consider breakdown by HTTP method (GET, POST, etc.)

   **Error panels:**
   - Error rate (errors per second)
   - Error ratio (errors / total requests as a percentage)
   - HTTP status code distribution (stacked area or bar chart showing 2xx, 3xx, 4xx, 5xx)
   - Example Prometheus query: `sum(rate(http_requests_total{service="$service", status=~"5.."}[$__rate_interval])) / sum(rate(http_requests_total{service="$service"}[$__rate_interval])) * 100`

   **Saturation panels:**
   - CPU usage (percentage of limit for containerized, absolute for VMs)
   - Memory usage (working set vs. limit for containers)
   - Disk I/O (read/write bytes per second, if applicable)
   - Connection pool utilization (database connections used vs. max)
   - Example Prometheus query: `sum(container_cpu_usage_seconds_total{pod=~"$service.*"}) by (pod) / sum(kube_pod_container_resource_limits{resource="cpu", pod=~"$service.*"}) by (pod) * 100`

4. **Create or update dashboards**

   **If Grafana MCP is available:**
   - Use Grafana MCP tools to create new dashboards or update existing ones.
   - Set the dashboard folder to match the service's team or namespace.
   - Add appropriate tags for discoverability (service name, environment, team).
   - Verify the dashboard renders correctly by querying it back after creation.

   **If Grafana MCP is NOT available, produce dashboard definition files:**
   - Generate Grafana dashboard JSON files following the Grafana JSON model.
   - Place files in a discoverable location: `monitoring/dashboards/[service-name].json` or the project's existing dashboard directory.
   - If the project uses Helm for Grafana provisioning, produce the appropriate `values.yaml` additions or ConfigMap definitions.
   - If the project uses Terraform or Pulumi, produce the corresponding resource definitions.

5. **Configure time range and variables (convention 8)**
   - Set the default time range to **last 1 hour** (`from: "now-1h"`, `to: "now"`).
   - Enable the time range picker so users can adjust the window.
   - Set auto-refresh interval to a sensible default (e.g., 30 seconds for real-time dashboards, 5 minutes for overview dashboards).
   - Add template variables for common filtering dimensions:
     - `$namespace` -- Kubernetes namespace selector
     - `$service` -- service name selector
     - `$pod` -- pod name selector (for drill-down)
     - `$instance` -- instance selector (for VM-based services)
   - Variables should use label_values queries against the relevant data source.

6. **Add alert annotations and links (convention 9)**
   - If alert rules exist for the service, add annotation queries that overlay alert firing periods on relevant panels.
   - Add links to related dashboards (e.g., from a service overview to its detailed infrastructure dashboard).
   - If runbooks exist in the repository, add dashboard links pointing to the runbook URLs.
   - If no alert rules exist, note this as a follow-up action in a text panel or in the output documentation.

7. **Organize dashboard layout**
   - Group panels by golden signal using Grafana rows:
     - Row 1: Overview (single-stat panels for current error rate, p99 latency, RPS, CPU usage)
     - Row 2: Latency (detailed latency panels)
     - Row 3: Traffic (detailed traffic panels)
     - Row 4: Errors (detailed error panels)
     - Row 5: Saturation (detailed resource usage panels)
   - Use consistent panel sizes within each row.
   - Set meaningful panel titles and descriptions.
   - Use appropriate visualization types:
     - Histograms/heatmaps for latency distribution
     - Time series for rates and percentiles
     - Gauge or stat for current values
     - Table for top-N breakdowns

8. **Validate the dashboard definitions**
   - If producing JSON files, validate that the JSON is syntactically correct.
   - Verify that all PromQL/LogQL queries reference metrics that exist in the data source (based on context.md and assessment findings).
   - Check that template variable queries are valid.
   - If Grafana MCP is available, query the created dashboard to confirm panels load without errors.

## Output Format

### Dashboard JSON files or provisioning configs

The output depends on the deployment method detected in context.md:

**Option A: Grafana Dashboard JSON** (most common)

Place files at `monitoring/dashboards/[service-name]-overview.json` or the project's existing dashboard directory.

```json
{
  "dashboard": {
    "title": "[Service Name] Overview",
    "tags": ["[service]", "[team]", "golden-signals"],
    "timezone": "browser",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s",
    "templating": {
      "list": [
        {
          "name": "namespace",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(namespace)"
        }
      ]
    },
    "panels": [
      {
        "title": "Request Rate (RPS)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"$service\"}[$__rate_interval]))",
            "legendFormat": "{{method}}"
          }
        ]
      }
    ],
    "rows": []
  }
}
```

**Option B: Helm values for Grafana sidecar provisioning**

```yaml
grafana:
  dashboards:
    default:
      service-overview:
        file: dashboards/service-overview.json
```

**Option C: Kubernetes ConfigMap**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-[service]
  labels:
    grafana_dashboard: "1"
data:
  [service]-overview.json: |
    { ... dashboard JSON ... }
```

**For each dashboard produced, include a companion summary section in the output documentation:**

```markdown
## Dashboard: [Service Name] Overview

- **File**: monitoring/dashboards/[service]-overview.json
- **Folder**: [Grafana folder]
- **Signals Covered**: Latency (p50/p95/p99), Traffic (RPS), Errors (error rate + status distribution), Saturation (CPU + memory)
- **Variables**: namespace, service, pod
- **Default Time Range**: Last 1 hour
- **Auto Refresh**: 30 seconds
- **Alert References**: [Yes/No -- list linked alerts]
- **Gaps Addressed**: [references recommendations from dashboard_assessment.md]
```

## Quality Criteria

- Every dashboard includes panels for all four golden signals (latency, traffic, errors, saturation) per convention 7
- Latency panels show percentile breakdowns (at minimum p50, p95, p99), not just averages
- Error panels show both absolute error rate and error ratio (percentage of total requests)
- Saturation panels include at least CPU and memory usage relative to limits
- Time range defaults to last 1 hour with the picker enabled per convention 8
- Template variables are provided for namespace, service, and pod/instance filtering
- Dashboard layout is organized by golden signal with clear row grouping
- All PromQL/LogQL queries reference metric names consistent with the detected data source
- Alert annotations or links to runbooks are included where alert rules exist per convention 9
- Dashboard JSON is syntactically valid and follows the Grafana JSON model
- Each dashboard produced maps to a specific recommendation from `dashboard_assessment.md`

## Context

This is the second step in the `dashboard_management` workflow. It takes the gap analysis from `inspect_dashboards` and produces concrete dashboard definitions. The output should be ready to apply -- either via Grafana MCP or by committing the JSON files to the repository for provisioning.

The four golden signals framework ensures that every production service has the minimum observability needed to detect and diagnose issues. Latency tells you how slow things are; traffic tells you how busy things are; errors tell you how broken things are; saturation tells you how full things are. Together, these four signals cover the vast majority of operational questions that arise during incident investigation.

Dashboard quality directly impacts incident response time. A well-designed dashboard lets an on-call engineer assess service health within 30 seconds of opening it. Poor dashboards -- those missing key signals, using confusing layouts, or showing irrelevant metrics -- slow down investigations and lead to missed symptoms.
