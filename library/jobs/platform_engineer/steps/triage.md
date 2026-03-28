# Triage & Scope

## Objective

Parse the incident description, determine the target environment, verify connectivity, identify likely affected services, and produce a prioritized investigation plan. This step transforms a vague symptom report into a structured, actionable scope for investigation.

## Task

Take the incident description and environment inputs, validate them, confirm access to the target environment, and create a triage document that will guide the investigate step.

### Process

#### 1. Parse the Incident Description

Read the `incident_description` input. Extract or infer the following fields:

- **Symptom**: What is actually observed? (e.g., "500 errors on /api/login", "pods in CrashLoopBackOff", "deployment stuck")
- **Onset**: When did the problem start? If not stated, ask the user.
- **Scope**: Is it affecting all users, some users, one environment, or one service?
- **Severity**: Is the service fully down, degraded, or intermittently failing?
- **Recent changes**: Were there recent deployments, config changes, or infrastructure updates?

If the incident description is vague (e.g., "the site is down" or "something broke"), ask the user structured clarifying questions:

```
I need a few more details to scope this investigation:

1. What specific symptom are you seeing? (error message, HTTP status code, timeout, crash)
2. When did this start? (approximate time, or "I just noticed")
3. Which environment is affected? (production, staging, dev, or specific cluster name)
4. Has anything changed recently? (deployment, config change, infrastructure update)
```

Do NOT proceed with an unclear scope — a vague triage leads to a scattered investigation.

#### 2. Determine Target Environment

Read the `environment` input. If it is not provided or is ambiguous:

- Check `context.md` for available environments (kubernetes contexts, cloud profiles, etc.)
- Present the discovered environments and ask the user to confirm:

```
I found the following environments in your context:

1. <context-name-1> (kubernetes)
2. <cloud-profile-1> (AWS)
3. <other>

Which environment is affected?
```

Record the environment identifier that will be used in subsequent commands (e.g., kubectl context name, cloud profile, SSH target).

#### 3. Verify Connectivity

Based on the infrastructure type from `context.md`, verify that the agent can reach the target environment. This step MUST complete before creating the investigation plan — there is no point planning kubectl queries if the cluster is unreachable.

**If kubernetes:**
```bash
kubectl cluster-info --context <context-name> 2>/dev/null
```
If this fails, note the failure and suggest remediation (e.g., VPN, kubeconfig refresh, credential renewal).

**If cloud-managed:**
```bash
# AWS
aws sts get-caller-identity --profile <profile> 2>/dev/null

# GCP
gcloud auth list --filter="status:ACTIVE" 2>/dev/null

# Azure
az account show 2>/dev/null

# DigitalOcean
doctl account get 2>/dev/null
```

**If nix/local:**
- Verify the target service is accessible (e.g., `curl -s -o /dev/null -w '%{http_code}' http://localhost:<port>`)

**If connectivity fails:**
- Record the failure in the triage document
- Suggest specific remediation steps
- Ask the user if they want to proceed with a limited investigation (repo/code analysis only) or fix connectivity first

#### 4. Identify Likely Affected Services

Map the reported symptom to likely affected service categories. Use both the symptom keywords and the repository structure from `context.md`.

**General symptom-to-service mapping:**

| Symptom Pattern | Likely Service Categories |
|-----------------|--------------------------|
| HTTP 5xx errors | Application servers, reverse proxy, load balancer |
| HTTP 4xx spike | Auth service, API gateway, DNS/routing |
| Connection refused / timeout | Network layer, service mesh, firewall, DNS |
| Pod CrashLoopBackOff | Application crash, OOM, config error, missing secrets |
| Pod Pending | Resource constraints (CPU/memory), node issues, PVC binding |
| High latency | Database, external API dependency, resource saturation |
| OOMKilled | Memory leak, insufficient resource limits |
| Disk pressure / PVC full | Storage, log rotation, database growth |
| SSL/TLS errors | Certificate expiry, cert-manager, ingress config |
| DNS resolution failures | CoreDNS, external DNS provider, network policy |
| Deployment stuck / rollout stalled | Image pull errors, readiness probes, resource quotas |
| Build failures | CI pipeline, dependency resolution, build cache |
| Metrics gaps / no data | Monitoring stack, scrape targets, network connectivity |

**Correlate with repo structure:**
- If `context.md` lists specific services (from Kubernetes namespaces, docker-compose services, or directory structure), map the symptom to those concrete services
- If the user mentioned a specific service name, validate it exists in the environment

Generate a list of **affected services (hypotheses)** — ordered from most likely to least likely, with a brief rationale for each.

#### 5. Detect Available Investigation Tools

Cross-reference the tools from `context.md` with what is useful for this specific incident:

- **If Grafana MCP is available**: Plan to query dashboards and Loki logs per conventions 55-59
- **If kubectl is available**: Plan pod inspection, event queries, log retrieval
- **If cloud CLI is available**: Plan service health checks, recent deployment history
- **If CI provider is detected**: Plan to check recent CI runs for deployment correlation
- **If sentry-cli is available**: Plan to check for correlated error spikes

Record which tools will be used and which are unavailable (per convention 56, note fallback strategies for unavailable tools).

#### 6. Create Prioritized Investigation Plan

Build an ordered list of investigation areas. Prioritize by:

1. **Impact**: Areas that could confirm or rule out the most likely root cause
2. **Speed**: Quick checks before deep dives
3. **Breadth**: Cover multiple hypotheses early before narrowing

Each investigation area MUST specify:
- What to check
- Which tool to use
- What a positive finding would mean
- What a negative finding would rule out
- Estimated effort (quick check / moderate / deep dive)

#### 7. Create Artifact Directory

Create the incident artifact directory:

```
.deepwork/tmp/platform_engineer/incident_investigation/YYYY-MM-DD-<slug>/
```

Where `<slug>` is a short, URL-safe description derived from the incident (e.g., `api-500-errors`, `pod-crashloop`, `deploy-stuck`). Use lowercase, hyphens only, no spaces.

Write the triage document to `triage.md` within this directory.

## Output Format

Write the triage document to `.deepwork/tmp/platform_engineer/incident_investigation/YYYY-MM-DD-<slug>/triage.md`.

```markdown
# Incident Triage

**Date**: YYYY-MM-DD HH:MM
**Reported by**: <user or alert source>
**Environment**: <environment identifier>

## Incident Summary

**Symptom**: <specific observed behavior>
**Onset**: <when the problem started or was first noticed>
**Scope**: <who/what is affected — all users, specific endpoints, specific pods, etc.>
**Severity**: <full outage / degraded / intermittent>
**Recent changes**: <deployments, config changes, or "none known">

## Environment

**Type**: <kubernetes / cloud-managed / nix / hybrid / local>
**Identifier**: <context name, profile, cluster, etc.>
**Connectivity**: confirmed / failed (details: <error message if failed>)

## Available Investigation Tools

| Tool | Available | Use For |
|------|-----------|---------|
| kubectl | yes/no | Pod status, events, logs |
| Grafana MCP | yes/no | Dashboards, Loki queries, alerts |
| <cloud CLI> | yes/no | Service health, deployment history |
| sentry-cli | yes/no | Error tracking correlation |
| gh CLI | yes/no | Recent CI runs, deployment PRs |

**Fallback notes**: <what alternatives exist if primary tools are unavailable>

## Affected Services (Hypothesis)

| Priority | Service | Rationale | Confidence |
|----------|---------|-----------|------------|
| 1 | <service name or category> | <why this is suspected> | Low/Medium |
| 2 | <service name or category> | <why this is suspected> | Low/Medium |
| ... | ... | ... | ... |

Note: These are hypotheses, not confirmed root causes. Confidence follows convention 5 — all are Low or Medium at triage stage because no runtime data has been checked yet.

## Investigation Plan

### Priority 1: <area> (quick check)
- **Check**: <what to look at>
- **Tool**: <which tool to use>
- **Positive finding means**: <interpretation>
- **Negative finding rules out**: <what gets eliminated>

### Priority 2: <area> (quick check)
- **Check**: <what to look at>
- **Tool**: <which tool to use>
- **Positive finding means**: <interpretation>
- **Negative finding rules out**: <what gets eliminated>

### Priority 3: <area> (moderate)
- **Check**: <what to look at>
- **Tool**: <which tool to use>
- **Positive finding means**: <interpretation>
- **Negative finding rules out**: <what gets eliminated>

### Priority 4: <area> (deep dive — only if earlier checks are inconclusive)
- **Check**: <what to look at>
- **Tool**: <which tool to use>
- **Positive finding means**: <interpretation>
- **Negative finding rules out**: <what gets eliminated>

## Artifact Directory

All investigation artifacts for this incident will be stored in:
`<artifact directory path>`
```

## Quality Criteria

- **Clear Scope**: The incident is clearly scoped with specific symptoms, timeframe, and affected environment identified. Vague descriptions have been clarified through user questions.
- **Investigation Plan**: A prioritized list of investigation areas is defined, each with specific checks, tools, and interpretations of findings. The plan is ordered by impact and speed.
- **Environment Confirmed**: The target environment is explicitly identified and connectivity is confirmed or noted as blocked with remediation suggestions.
- **Hypotheses Grounded**: Affected service hypotheses are based on symptom-to-service mapping and repository structure, not speculation. Confidence levels follow convention 5 (Low or Medium at triage stage).
- **Tool Awareness**: The investigation plan uses only tools confirmed available in `context.md`. Fallback strategies are noted for unavailable tools per convention 56.
- **No Premature Investigation**: This step scopes the investigation but does NOT begin querying logs, metrics, or events. That work belongs to the investigate step.

## Context

This step sits between `gather_context` (which discovers the environment) and `investigate` (which queries live systems). Its job is to translate a human-reported symptom into a structured plan that the investigate step can execute methodically.

The triage document serves as the contract between triage and investigation — the investigate step will follow the plan priorities in order and report findings against each area.

Per convention 1, no destructive actions are taken during triage. Per convention 3, all findings include timestamps and confidence levels. Confidence at triage is necessarily Low or Medium because no runtime data has been examined yet — the investigate step will raise confidence levels as evidence is gathered.

The artifact directory created here will be reused by the investigate and incident_report steps to store all investigation-related files in one place.
