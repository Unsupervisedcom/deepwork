# Implement Observability

## Objective

Create and apply the observability configurations specified in the observability plan, producing validated, ready-to-deploy monitoring infrastructure appropriate to the project's infrastructure type. Every configuration file MUST be validated before being considered complete.

## Task

Translate the observability plan into concrete configuration files, alert rules with runbook references, and dashboard definitions. Validate all configurations using dry-run or syntax-checking tools appropriate to the infrastructure type.

### Process

#### 1. Read the plan and context

- Load `observability_plan.md` from the previous step
- Load `context.md` from `gather_context`
- Extract:
  - The confirmed stack components (metrics, logs, visualization, alerting)
  - The implementation steps and their ordering
  - The infrastructure type (determines config format)
  - The dashboard plan (which services, which golden signals)
  - The alert rules to create
  - The retention policy settings

#### 2. Create configuration files based on infrastructure type

Work through the implementation steps defined in the plan, creating configuration files for each component. The exact format depends on the infrastructure type.

**Kubernetes configurations:**

*Helm values for kube-prometheus-stack (if selected):*
- Create a `values.yaml` (or `values-monitoring.yaml`) containing:
  - Prometheus retention and storage settings matching the plan's retention policy
  - Grafana admin credentials reference (from a Kubernetes Secret, never hardcoded)
  - Grafana dashboard provisioning sidecar configuration
  - Alertmanager configuration with routes and receivers from the plan's alert pipeline
  - Node-exporter and kube-state-metrics enabled
  - Resource requests and limits per convention 16
- Place in the repository's Helm values directory (e.g., `k8s/monitoring/`, `charts/monitoring/`, or as specified in context.md)

*ServiceMonitor and PodMonitor CRDs for application metrics:*
- For each application service listed in the dashboard plan, create a `ServiceMonitor` or `PodMonitor` CRD that:
  - Targets the service's metrics endpoint (typically `/metrics` on a named port)
  - Sets an appropriate scrape interval (15s for critical services, 30s for others)
  - Includes labels for Prometheus to select it (`release: <helm-release-name>`)
- File naming: `servicemonitor-<service-name>.yaml`

*PrometheusRule CRDs for alert rules:*
- Create PrometheusRule resources containing the alert rules defined in the plan
- Each alert rule MUST include:
  - `alert`: Descriptive name (e.g., `HighErrorRate_<service>`)
  - `expr`: PromQL expression for the condition
  - `for`: Duration the condition must hold (e.g., `5m` for warnings, `2m` for critical)
  - `labels.severity`: `critical`, `warning`, or `info`
  - `annotations.summary`: Human-readable description of what the alert means
  - `annotations.runbook_url`: Link to a runbook file in the repository (per convention 9)
- File naming: `prometheusrule-<category>.yaml` (e.g., `prometheusrule-error-rates.yaml`)

*Loki configuration (if selected):*
- Create Helm values for Loki deployment with:
  - Storage backend configuration (filesystem for single-node, S3/GCS for production)
  - Retention settings matching the plan
  - Resource limits
- Create Promtail Helm values or DaemonSet config for log collection

*Grafana dashboard provisioning:*
- Create dashboard JSON files for each service in the dashboard plan
- Each dashboard MUST include panels for the golden signals marked in the plan:
  - **Latency**: Histogram quantiles (p50, p90, p99) — typically `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`
  - **Traffic**: Request rate — typically `rate(http_requests_total[5m])`
  - **Errors**: Error rate or error ratio — typically `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`
  - **Saturation**: CPU and memory utilization — typically `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`
- Dashboard MUST include a time range selector defaulting to last 1 hour per convention 8
- Dashboard queries MUST specify explicit time ranges per convention 12
- Wrap each dashboard JSON in a ConfigMap for Grafana sidecar provisioning
- File naming: `dashboard-<service-name>.json`, wrapped in `configmap-dashboard-<service-name>.yaml`

**Nix/NixOS configurations:**

*Prometheus NixOS module:*
- Create or update the NixOS module configuration for `services.prometheus`:
  - `services.prometheus.enable = true;`
  - `services.prometheus.retentionTime` matching the plan's retention policy
  - `services.prometheus.scrapeConfigs` with entries for each service
  - `services.prometheus.rules` with alert rule definitions
  - Resource limits via systemd settings if applicable

*Loki NixOS module:*
- Configure `services.loki` with:
  - Storage path and retention settings
  - Schema configuration
  - Limits configuration
- Configure `services.promtail` with:
  - Log file paths or journal scraping
  - Label configuration for each service

*Grafana NixOS module:*
- Configure `services.grafana` with:
  - `services.grafana.enable = true;`
  - Data source provisioning (Prometheus, Loki)
  - Dashboard provisioning directory
  - Authentication settings

*Alertmanager NixOS module:*
- Configure `services.prometheus.alertmanager` with:
  - Route tree matching the plan's alert pipeline
  - Receivers for each notification channel (Slack webhook, email, PagerDuty)
  - Inhibition rules to prevent duplicate notifications

*Dashboard JSON files:*
- Create dashboard JSON files in the Grafana provisioning directory
- Follow the same golden signal coverage as described for Kubernetes above

**Cloud-managed configurations:**

*Terraform / CloudFormation / Pulumi resources:*
- Create IaC resources for the cloud provider's monitoring services
- AWS example:
  - `aws_prometheus_workspace` for managed Prometheus
  - `aws_grafana_workspace` for managed Grafana
  - `aws_cloudwatch_metric_alarm` for alert rules
  - `aws_sns_topic` and `aws_sns_topic_subscription` for notification routing
- GCP example:
  - `google_monitoring_alert_policy` for alert rules
  - `google_monitoring_dashboard` for dashboards
  - `google_monitoring_notification_channel` for routing
- Azure example:
  - `azurerm_monitor_metric_alert` for alert rules
  - `azurerm_dashboard` for dashboards
  - `azurerm_monitor_action_group` for routing

*Cloud-specific alert policies:*
- Create alert policies using the cloud provider's native syntax
- Each alert MUST still reference a runbook per convention 9

*Dashboard definitions:*
- Create dashboard definitions in the cloud provider's format (JSON for AWS/GCP, ARM template for Azure)
- Cover the same golden signals as above

#### 3. Create alert rules with runbook references

Regardless of infrastructure type, create the following baseline alert rules (adjusting thresholds per the plan):

**Error rate alerts:**
```
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 5m
  severity: warning
  runbook: docs/runbooks/high-error-rate.md

- alert: CriticalErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.10
  for: 2m
  severity: critical
  runbook: docs/runbooks/high-error-rate.md
```

**Latency alerts:**
```
- alert: HighLatencyP99
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > <threshold>
  for: 5m
  severity: warning
  runbook: docs/runbooks/high-latency.md
```

**Infrastructure alerts (Kubernetes):**
```
- alert: PodCrashLooping
  expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
  for: 5m
  severity: warning
  runbook: docs/runbooks/pod-crash-loop.md

- alert: PodNotReady
  expr: kube_pod_status_ready{condition="false"} == 1
  for: 10m
  severity: warning
  runbook: docs/runbooks/pod-not-ready.md
```

**Resource alerts:**
```
- alert: DiskUsageHigh
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.20
  for: 10m
  severity: warning
  runbook: docs/runbooks/disk-usage.md

- alert: DiskUsageCritical
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.10
  for: 5m
  severity: critical
  runbook: docs/runbooks/disk-usage.md

- alert: MemoryPressure
  expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.15
  for: 5m
  severity: warning
  runbook: docs/runbooks/memory-pressure.md
```

For each alert rule that references a runbook file, create a stub runbook file in the repository with the following structure:
```markdown
# Runbook: <Alert Name>

## Trigger Condition
<human-readable description of when this alert fires>

## Impact
<what is affected when this condition is true>

## Investigation Steps
1. <step>
2. <step>
...

## Remediation
<how to fix the issue>

## Escalation
<when and how to escalate>
```

#### 4. Validate configurations

Before considering any configuration complete, validate it using the appropriate tool:

**Kubernetes:**
- `helm template <release-name> <chart> -f values.yaml` — verify Helm values produce valid manifests
- `kubectl apply --dry-run=client -f <file>.yaml` — verify CRD manifests are valid YAML and have correct apiVersion/kind
- `promtool check rules <rules-file>.yaml` — verify PrometheusRule syntax if promtool is available
- Verify all dashboard JSON files are valid JSON (`python3 -c "import json; json.load(open('<file>'))"`  or `jq . <file> > /dev/null`)

**Nix/NixOS:**
- `nix eval .#nixosConfigurations.<hostname>.config.services.prometheus.enable` — verify the Nix expression evaluates without errors
- If a full NixOS configuration is available, `nix build .#nixosConfigurations.<hostname>.config.system.build.toplevel --dry-run` for a broader check
- For standalone module snippets, verify syntax with `nix-instantiate --parse <file>.nix`

**Cloud-managed:**
- `terraform plan` (or `terraform validate`) for Terraform configs
- `aws cloudformation validate-template --template-body file://<template>.yaml` for CloudFormation
- `pulumi preview` for Pulumi configs

**All:**
- Check that every alert rule has a `runbook_url` or `runbook` annotation pointing to an existing file
- Check that every dashboard JSON includes panels for the golden signals listed in the plan
- Check that retention values in configs match the plan's retention policy

Record validation results for each configuration file. If validation fails, fix the issue and re-validate before proceeding.

#### 5. Document how to apply the configs

Create an `APPLYING.md` section at the end of each major configuration file (as a comment) or as a separate document, explaining:

**Kubernetes:**
```bash
# Install or upgrade the monitoring stack
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f values-monitoring.yaml

# Apply ServiceMonitors
kubectl apply -f servicemonitors/

# Apply PrometheusRules
kubectl apply -f prometheusrules/

# Apply dashboard ConfigMaps
kubectl apply -f dashboards/
```

**NixOS:**
```bash
# Add the monitoring module to your NixOS configuration imports
# Then rebuild:
sudo nixos-rebuild switch --flake .#<hostname>
```

**Cloud-managed:**
```bash
# Plan and apply Terraform changes
cd terraform/monitoring/
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

Include any prerequisites (namespace creation, Helm repo addition, provider authentication) and post-apply verification steps.

## Output Format

All configuration files are written to the repository in locations appropriate to the project structure discovered in context.md. If no obvious location exists, create a `monitoring/` directory at the repository root.

A summary document MUST also be written listing all files created:

```markdown
# Observability Implementation Summary

**Date**: YYYY-MM-DD
**Infrastructure Type**: <type>
**Stack**: <components>

## Files Created

| File | Purpose | Validated |
|------|---------|-----------|
| `<path>` | <purpose> | Yes/No (reason if no) |
| ... | ... | ... |

## Alert Rules Created

| Alert Name | Severity | Condition Summary | Runbook |
|-----------|----------|-------------------|---------|
| <name> | critical/warning/info | <brief condition> | <runbook path> |
| ... | ... | ... | ... |

## Dashboards Created

| Dashboard | Service | Golden Signals | File |
|-----------|---------|---------------|------|
| <name> | <service> | L/T/E/S | <path> |
| ... | ... | ... | ... |

## How to Apply

<commands to deploy the full stack>

## Validation Results

| File | Tool | Result |
|------|------|--------|
| <path> | <validation tool> | PASS/FAIL (details) |
| ... | ... | ... |

## Next Steps

- [ ] Review alert thresholds with the team
- [ ] Configure notification channels (Slack webhook URL, PagerDuty key, etc.)
- [ ] Complete runbook content beyond stubs
- [ ] Test alerting pipeline end-to-end after deployment
```

## Quality Criteria

- **Configs Created**: All configuration files specified in the observability plan are created in the repository. No planned component is left without a configuration file.
- **Alert Rules Defined**: Alert rules are defined for at minimum: high error rate, high latency, disk usage, and memory pressure. Each alert rule includes a severity label and a runbook reference (annotation) pointing to a file in the repository per convention 9. Runbook stub files are created for each referenced runbook.
- **Golden Signals Covered**: Every dashboard created covers the golden signals (latency, traffic, errors, saturation) that were planned for that service per convention 7. Dashboard queries specify explicit time ranges per convention 12. Dashboards include time range selectors defaulting to last 1 hour per convention 8.
- **Validated**: Configurations are validated using the appropriate tool for the infrastructure type (Helm template, nix eval, terraform validate, JSON syntax check). Validation results are recorded. Any validation failure is fixed before the step is considered complete.
- **Declarative**: All configurations are declarative and version-controllable per convention 13. No manual console clicks or imperative commands are the primary configuration method.
- **Documented**: How to apply the configurations is documented with exact commands, prerequisites, and post-apply verification steps per convention 14.
- **Plan Adherence**: The implementation matches the architecture, retention policy, and component choices specified in `observability_plan.md`. Any deviations are documented with rationale.

## Context

This step is the second of two in the `observability_setup` workflow (`plan_observability` -> `implement_observability`). It receives the `observability_plan.md` from the planning step and the `context.md` from `gather_context`.

The step produces configuration files that are ready to be applied to the target environment. It does NOT apply them — that is left to the user or a subsequent deployment workflow. The step focuses on creating correct, validated, documented configurations.

Key conventions referenced:
- Convention 7: Every production service MUST have a dashboard covering the four golden signals
- Convention 8: Dashboards MUST include time range selectors defaulting to last 1 hour
- Convention 9: Alert rules MUST have associated runbooks or investigation steps
- Convention 10: Log-based alerts SHOULD complement metric-based alerts
- Convention 11: Loki queries MUST use label filters
- Convention 12: Dashboard queries MUST specify explicit time ranges
- Convention 13: Infrastructure changes MUST be declarative (IaC)
- Convention 14: Infrastructure configuration MUST be documented in a discoverable location
- Convention 16: Resource limits MUST be set for all containerized workloads
