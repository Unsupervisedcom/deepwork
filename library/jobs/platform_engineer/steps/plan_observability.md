# Plan Observability Setup

## Objective

Design a monitoring stack tailored to the project's infrastructure type, ensuring coverage of the four golden signals (latency, traffic, errors, saturation) for all production services. The plan MUST be concrete enough that the `implement_observability` step can execute it without ambiguity.

## Task

Assess the current observability posture, recommend a monitoring stack appropriate to the infrastructure type, confirm the choice with the user, and produce a detailed architecture and implementation plan.

### Process

#### 1. Read context.md for infrastructure type and existing monitoring

- Load the `context.md` file produced by `gather_context`
- Extract the infrastructure type (kubernetes, nix, cloud-managed, hybrid, none)
- Note which observability tools are already available (Grafana MCP, promtool, logcli, amtool)
- Note existing monitoring configurations (dashboard files, alert rules, Prometheus configs, Loki configs)
- Note existing CI/CD provider and deployment tooling (Helm, Terraform, Nix modules) as this determines the configuration format

#### 2. Assess current state

Evaluate the existing monitoring against conventions 7-12. For each area, record the current state as one of: **covered**, **partial**, **missing**.

**Metrics collection:**
- Is there a metrics collector deployed (Prometheus, VictoriaMetrics, CloudWatch agent)?
- Are application-level metrics being scraped (custom endpoints, SDK instrumentation)?
- Are infrastructure-level metrics being collected (node exporter, kube-state-metrics, cloud provider metrics)?

**Log aggregation:**
- Is there a centralized log system (Loki, CloudWatch Logs, Elasticsearch)?
- Are logs structured (JSON) or unstructured?
- Are log retention policies defined?

**Visualization:**
- Is Grafana (or equivalent) deployed?
- Which services have dashboards? Which do not?
- Do existing dashboards cover all four golden signals per convention 7?

**Alerting:**
- Are alert rules defined? Where do they live (PrometheusRule CRDs, Nix config, cloud console)?
- Do alert rules have associated runbooks or investigation steps per convention 9?
- Is there an on-call rotation or notification channel configured?

**Gaps summary:**
- List each gap explicitly: "Service X has no dashboard", "No log aggregation exists", "Alert rules exist but have no runbooks"

#### 3. Recommend a monitoring stack based on infrastructure type

Based on the infrastructure type from context.md, recommend one of the following stacks. If the infrastructure type is hybrid, recommend the stack that covers the most components and note any gaps.

**Kubernetes:**
- **Metrics**: Prometheus Operator via `kube-prometheus-stack` Helm chart (includes Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics) OR VictoriaMetrics Operator (for high-cardinality or long-term retention scenarios)
- **Logs**: Loki via the `loki-stack` Helm chart or Grafana Loki Operator, with Promtail or Grafana Agent for log collection
- **Visualization**: Grafana (bundled with kube-prometheus-stack, or standalone for VictoriaMetrics setups)
- **Alerting**: Alertmanager (bundled with kube-prometheus-stack) routed to Slack, PagerDuty, or email
- **When to recommend VictoriaMetrics over Prometheus**: cardinality > 1M active series, need for long-term storage (> 30 days), or multi-cluster federation

**Nix/NixOS:**
- **Metrics**: Prometheus via NixOS module (`services.prometheus`) with scrape configs defined in Nix, OR VictoriaMetrics via NixOS module (`services.victoriametrics`)
- **Logs**: Loki via NixOS module (`services.loki`) with Promtail via NixOS module (`services.promtail`)
- **Visualization**: Grafana via NixOS module (`services.grafana`) with dashboard provisioning
- **Alerting**: Alertmanager via NixOS module (`services.prometheus.alertmanager`) with route config in Nix
- **Advantage**: All config is declarative and version-controlled as Nix expressions

**Cloud-managed:**
- **AWS**: CloudWatch Metrics + CloudWatch Logs + AWS Managed Prometheus (AMP) + AWS Managed Grafana (AMG) + CloudWatch Alarms or SNS
- **GCP**: Cloud Monitoring + Cloud Logging + Managed Prometheus (GMP) + Cloud Alerting Policies
- **Azure**: Azure Monitor + Log Analytics Workspace + Azure Managed Grafana + Azure Monitor Alerts
- **Advantage**: No infrastructure to manage; pay-per-use; native integration with cloud services
- **Tradeoff**: Vendor lock-in; potentially higher cost at scale

**Hybrid:**
- Combine approaches as appropriate. For example, Kubernetes workloads use kube-prometheus-stack while NixOS hosts use NixOS Prometheus modules, all pointing to a shared Grafana instance.

For each recommendation, state:
- What it replaces or supplements in the current setup
- Why it is preferred over alternatives for this specific context
- Any prerequisites (Helm installed, NixOS version, cloud permissions)

#### 4. Confirm stack choice with the user

Use `AskUserQuestion` to present the recommendation and get confirmation. The question MUST include:
- The recommended stack components (one line per component)
- Key tradeoffs the user should be aware of
- Any alternative the user might prefer
- Whether the user has specific constraints (budget, vendor restrictions, existing contracts)

If the user requests a different stack, adjust the plan accordingly. Record the final decision and rationale.

#### 5. Design the architecture

With the stack confirmed, design the full architecture:

**Data flow:**
- Draw an ASCII diagram showing: metric sources -> collector -> storage -> query layer -> visualization
- Draw a separate flow for logs: log sources -> shipper -> aggregator -> query layer -> visualization
- Identify the protocol at each hop (Prometheus remote write, HTTP push, syslog, etc.)

**Retention policies:**
- **Hot storage**: High-resolution data retained for 15-30 days (fast queries)
- **Cold storage**: Downsampled data retained for 6-12 months (trend analysis)
- Recommend specific retention values based on infrastructure scale
- Note storage cost implications

**Alerting pipeline:**
- Define alert severity levels: critical (page), warning (ticket), info (log)
- Define notification routing: which team/channel receives which severity
- Define silencing and inhibition rules to prevent alert storms
- Reference convention 9: every alert rule MUST have a runbook reference

**Dashboard plan:**
- List every production service that needs a dashboard (per convention 7)
- For each service, note which golden signals apply and what metrics/queries to use
- Define a dashboard naming convention (e.g., `<team>/<service>/overview`)
- Plan a "platform overview" dashboard showing cross-service health

#### 6. Define implementation steps

Break the architecture into ordered implementation steps. Each step MUST include:
- What to create or configure
- Which tool/format to use (Helm values, Nix module, Terraform resource)
- Dependencies (what must exist before this step)
- Validation: how to verify this step succeeded

Order the steps so that foundational components (metrics storage, log storage) come before consumers (dashboards, alerts).

Example ordering for Kubernetes:
1. Deploy kube-prometheus-stack (Prometheus, Grafana, Alertmanager, node-exporter)
2. Configure ServiceMonitor CRDs for application metrics endpoints
3. Deploy Loki stack (Loki + Promtail)
4. Create PrometheusRule CRDs for alert rules with runbook annotations
5. Configure Alertmanager routes and receivers
6. Provision Grafana dashboards via ConfigMaps
7. Verify end-to-end: trigger a test alert, confirm it reaches the notification channel

Example ordering for NixOS:
1. Enable and configure `services.prometheus` with scrape targets
2. Enable and configure `services.loki` and `services.promtail`
3. Enable and configure `services.grafana` with provisioning
4. Define alert rules in Prometheus config
5. Configure `services.prometheus.alertmanager` with routes
6. Deploy with `nixos-rebuild switch`
7. Verify end-to-end

## Output Format

Write the plan to `observability_plan.md` in the workflow artifact directory.

```markdown
# Observability Plan

**Date**: YYYY-MM-DD
**Infrastructure Type**: <from context.md>
**Decision**: <final stack choice and brief rationale>

## Current State Assessment

### Metrics Collection
- **Status**: covered / partial / missing
- **Details**: <what exists, what is missing>

### Log Aggregation
- **Status**: covered / partial / missing
- **Details**: <what exists, what is missing>

### Visualization
- **Status**: covered / partial / missing
- **Details**: <which services have dashboards, which do not>

### Alerting
- **Status**: covered / partial / missing
- **Details**: <what alerts exist, whether runbooks are present>

### Gaps Summary
1. <gap description>
2. <gap description>
...

## Recommended Stack

### Components
| Component | Tool | Purpose | Replaces/Supplements |
|-----------|------|---------|---------------------|
| Metrics collector | <tool> | <purpose> | <what it replaces> |
| Log aggregator | <tool> | <purpose> | <what it replaces> |
| Visualization | <tool> | <purpose> | <what it replaces> |
| Alerting | <tool> | <purpose> | <what it replaces> |

### Rationale
<Why this stack was chosen for this infrastructure type>

### Alternatives Considered
<What was not chosen and why>

## Architecture

### Data Flow
```
<ASCII diagram for metrics>
```

```
<ASCII diagram for logs>
```

### Retention Policy

| Tier | Resolution | Duration | Storage Type | Estimated Size |
|------|-----------|----------|--------------|----------------|
| Hot | Full resolution | <days> | <type> | <estimate> |
| Cold | Downsampled | <months> | <type> | <estimate> |

### Alert Pipeline

| Severity | Action | Routing | Response Time |
|----------|--------|---------|---------------|
| Critical | Page on-call | <channel> | < 15 min |
| Warning | Create ticket | <channel> | < 4 hours |
| Info | Log only | <channel> | Best effort |

### Dashboard Plan

| Service | Golden Signals Covered | Dashboard Name | Priority |
|---------|----------------------|----------------|----------|
| <service> | latency, traffic, errors, saturation | <name> | P1/P2/P3 |
| ... | ... | ... | ... |

## Implementation Steps

### Step 1: <title>
- **Action**: <what to do>
- **Format**: <Helm values / Nix module / Terraform / etc.>
- **Dependencies**: <what must exist first>
- **Validation**: <how to verify success>

### Step 2: <title>
...

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| <risk> | Low/Med/High | Low/Med/High | <mitigation> |
```

## Quality Criteria

- **Stack Selected**: A monitoring stack is selected with rationale based on the infrastructure type from context.md. The rationale explains why this stack is preferred over alternatives for the specific environment.
- **Architecture Defined**: The monitoring architecture is defined including data flow (with ASCII diagram), retention policies with concrete durations, and alerting pipeline with severity-to-routing mappings.
- **Implementation Steps**: Clear, ordered implementation steps are provided appropriate to the infrastructure type (Helm charts for k8s, NixOS modules for Nix, Terraform/cloud configs for cloud-managed). Each step includes dependencies and a validation check.
- **Golden Signals Planned**: The dashboard plan ensures all production services will have golden signal coverage per convention 7. Every service is listed with the signals to be covered.
- **User Confirmed**: The stack choice was confirmed with the user via AskUserQuestion before finalizing the plan. Any user constraints or preferences are recorded.
- **Current State Accurate**: The current state assessment reflects what was actually found in context.md and the repository, not assumptions. Gaps are specific and actionable.

## Context

This step is the first of two in the `observability_setup` workflow (`plan_observability` -> `implement_observability`). It runs after `gather_context`, which provides the `context.md` file describing the project's infrastructure type, available tools, and existing monitoring configurations.

The plan produced here is the sole input to the `implement_observability` step, which will create the actual configuration files. Therefore, the plan MUST be specific enough that the implementation step can translate each implementation step into concrete configuration without needing to make architectural decisions.

Key conventions referenced:
- Convention 7: Every production service MUST have a dashboard covering the four golden signals
- Convention 8: Dashboards MUST include time range selectors and SHOULD default to the last 1 hour
- Convention 9: Alert rules MUST have associated runbooks or investigation steps
- Convention 10: Log-based alerts SHOULD complement metric-based alerts
- Convention 11: Loki queries MUST use label filters
- Convention 12: Dashboard queries MUST specify explicit time ranges
- Convention 13: Infrastructure changes MUST be declarative (IaC)
- Convention 14: Infrastructure configuration MUST be documented in a discoverable location
