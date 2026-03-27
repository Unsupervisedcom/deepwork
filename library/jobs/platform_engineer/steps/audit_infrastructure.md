# Audit Infrastructure

## Objective

Document the project's infrastructure setup comprehensively and assess it against the platform engineering conventions. Produce an inventory of all infrastructure components, a convention compliance matrix, and a prioritized gap analysis with specific remediation recommendations. This is a read-only audit — no infrastructure changes are made.

## Task

Systematically examine every infrastructure area — monitoring, CI/CD, deployment, secrets, networking, data stores, and backup — and compare findings against the relevant conventions. The output is a single document that gives a complete picture of the project's infrastructure health.

### Process

#### 1. Read Context

Read `context.md` to understand:
- Infrastructure type (Kubernetes, Nix, cloud-managed, hybrid, none)
- Available tools and CLIs
- Repository structure — where infrastructure configs live
- CI provider and deployment tooling detected

The infrastructure type determines which conventions apply and what to look for. For example, convention 16 (resource limits) applies only to containerized workloads.

#### 2. Document Each Infrastructure Area

For each area below, document what exists, how it is configured, and any observations about quality or completeness. Use the available tools from `context.md` to query live state where possible, but MUST NOT make changes.

**Monitoring & Observability:**
- What observability stack is deployed? (Prometheus, Grafana, Loki, VictoriaMetrics, Datadog, New Relic, CloudWatch, none)
- Are there dashboards? Where are they defined? (Grafana JSON, Terraform, Helm values, cloud console)
- If Grafana MCP is available, list dashboards using the MCP tool
- Are alert rules defined? Where? (PrometheusRule CRDs, Alertmanager config, cloud provider alerts)
- Is log aggregation configured? (Loki, ELK, CloudWatch Logs, etc.)
- Are there runbooks linked to alerts? (convention 9)
- Do dashboards cover the four golden signals for production services? (convention 7)
- Check for monitoring configuration files in the repo: `monitoring/`, `observability/`, `dashboards/`, `alerts/`, `grafana/`

**CI/CD:**
- List all CI pipeline files found (paths and a one-line summary of each pipeline's purpose)
- What stages do the pipelines cover? (lint, test, build, deploy, release)
- Is build caching enabled? (convention 19)
- Are dependencies cached? (convention 20)
- Is the CI config validated/linted? (convention 21)
- Are secrets managed via the CI provider? (convention 22)
- Do test stages run in parallel? (convention 23)
- Estimate pipeline completion time if recent run data is available (convention 18 — under 10 minutes target)

**Deployment:**
- How is the application deployed? Document the deployment mechanism:
  - Kubernetes: Helm charts, Kustomize, raw manifests, ArgoCD, FluxCD
  - Nix: NixOS modules, deploy-rs, colmena
  - Cloud-managed: Terraform, Pulumi, CDK, CloudFormation, serverless framework
  - Containers: Docker Compose, ECS, Cloud Run, App Engine
  - Traditional: systemd units, PM2, manual SSH deploy
- Is deployment declarative? (convention 13)
- Is infrastructure documented in a discoverable location? (convention 14)
- Are resource limits set for containerized workloads? (convention 16)
- Are infrastructure decisions recorded as ADRs? (convention 17)

**Secrets Management:**
- How are secrets handled?
  - Environment variables (`.env` files — note existence but NEVER read contents)
  - Kubernetes Secrets (plain or encrypted: sealed-secrets, SOPS, external-secrets)
  - Cloud provider secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
  - HashiCorp Vault
  - Doppler, 1Password, Bitwarden
  - CI provider secrets
- Are secrets stored in plain text in the repo? (convention 15 — MUST NOT)
- Check `.gitignore` for `.env*` patterns
- Check for `.env.example` or `.env.template` files (good practice indicator)
- Are there any `.env` files tracked in git? Run `git ls-files | grep -i '\.env'` to check

**Networking:**
- Load balancers: type and provider (cloud LB, nginx, Traefik, HAProxy, Caddy)
- DNS management: where are DNS records managed? (Cloudflare, Route53, manual, Terraform)
- TLS certificates: how are they provisioned? (Let's Encrypt/cert-manager, cloud provider, manual)
- Ingress configuration: Kubernetes Ingress, cloud load balancer rules, reverse proxy config
- Network policies: are there Kubernetes NetworkPolicies or cloud firewall rules?

**Data Stores:**
- List all databases, caches, and message queues used by the project
- How are they provisioned? (managed cloud service, Kubernetes operator, Docker Compose, Nix module, manual)
- Are connection strings/credentials managed securely?
- Are there database migration files? Where?
- Backup configuration — see next section

**Backup & Recovery:**
- Is there a backup strategy for databases and persistent data?
- Are backups automated? How frequently?
- Has restore been tested? When was the last test?
- Where are backups stored? (cloud storage, separate region, local)
- Are there disaster recovery runbooks?

#### 3. Check Against Conventions

For each relevant convention, assess the project's compliance. Not all conventions apply to every project — mark inapplicable conventions as N/A with a brief reason.

**Infrastructure standards (conventions 13-17):**
- 13: Infrastructure changes are declarative (IaC)
- 14: Infrastructure configuration is documented in a discoverable location
- 15: Secrets are not stored in plain text
- 16: Resource limits are set for containerized workloads
- 17: Infrastructure decisions are recorded as ADRs

**Observability standards (conventions 7-12):**
- 7: Production services have golden signal dashboards
- 8: Dashboards include time range selectors
- 9: Alert rules have runbooks
- 10: Log-based alerts complement metric-based alerts
- 11: Loki queries use label filters
- 12: Dashboard queries specify explicit time ranges

**CI/CD standards (conventions 18-23):**
- 18: CI pipelines complete in under 10 minutes
- 19: Build caching is enabled
- 20: Dependency installation is cached
- 21: Pipeline configs are linted/validated
- 22: No hardcoded secrets in CI configs
- 23: Test stages run in parallel

**Security standards (conventions 30-34):**
- 30: Vulnerability scans run weekly
- 31: Critical/High CVEs addressed within policy timeframe
- 32: Container base images up to date, minimal
- 33: Dependency updates automated (Dependabot/Renovate)
- 34: Security scans triaged with severity assessments

**Developer environment standards (conventions 46-49):**
- 46: Local dev setup instructions documented
- 47: Dev environments are reproducible (Nix, Docker Compose)
- 48: Troubleshooting guide exists
- 49: Doctor workflow available for broken environments

#### 4. Produce Compliance Summary

For each convention, assign one of four statuses:
- **Pass**: Fully compliant. Evidence supports compliance.
- **Fail**: Non-compliant. The convention is applicable but not met.
- **Partial**: Some elements are in place but incomplete.
- **N/A**: The convention does not apply to this project (with reason).

#### 5. Identify Gaps with Recommendations

For each failing or partial convention, provide:
- A specific description of what is missing
- A concrete recommendation for remediation (not just "add this" but how)
- Estimated effort (small/medium/large)
- Priority (high/medium/low) based on risk and impact

## Output Format

Write the audit to `.deepwork/tmp/platform_engineer/infrastructure_audit/infrastructure_audit.md`. Create parent directories if they do not exist.

```markdown
# Infrastructure Audit

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name>
**Infrastructure Type**: <from context.md>

## Infrastructure Inventory

### Monitoring & Observability
- **Stack**: <Prometheus + Grafana / Datadog / CloudWatch / none / etc.>
- **Dashboards**: <count, location, coverage summary>
- **Alerts**: <count, location, runbook status>
- **Log aggregation**: <tool, configuration location>
- **Notes**: <observations>

### CI/CD
- **Provider**: <GitHub Actions / Forgejo / GitLab CI / etc.>
- **Pipelines**:
  | File | Purpose | Stages | Est. Duration |
  |------|---------|--------|---------------|
  | <path> | <purpose> | <lint, test, build, etc.> | <time or unknown> |
- **Caching**: <enabled / not enabled — details>
- **Secrets management**: <CI provider secrets / hardcoded / mixed>
- **Notes**: <observations>

### Deployment
- **Mechanism**: <Helm / Kustomize / Terraform / Docker Compose / etc.>
- **Declarative**: yes / no / partial
- **Documentation**: <path or "not found">
- **Resource limits**: <set / not set / N/A>
- **ADRs**: <path or "not found">
- **Notes**: <observations>

### Secrets Management
- **Approach**: <description>
- **Plain text secrets in repo**: yes / no
- **.env files tracked in git**: yes / no
- **.env.example exists**: yes / no
- **Notes**: <observations>

### Networking
- **Load balancer**: <type or "none">
- **DNS management**: <provider or "unknown">
- **TLS certificates**: <provisioning method or "unknown">
- **Ingress**: <type or "N/A">
- **Network policies**: <yes / no / N/A>
- **Notes**: <observations>

### Data Stores
| Store | Type | Provisioning | Backup | Migration Files |
|-------|------|-------------|--------|-----------------|
| <name> | <postgres/redis/etc.> | <managed/operator/compose> | <yes/no/unknown> | <path or N/A> |

### Backup & Recovery
- **Strategy**: <description or "none documented">
- **Automated**: yes / no / unknown
- **Frequency**: <daily/weekly/etc. or "unknown">
- **Last restore test**: <date or "never/unknown">
- **Notes**: <observations>

## Convention Compliance Matrix

### Infrastructure Standards
| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 13 | Declarative infrastructure (IaC) | pass / fail / partial / N/A | <details> |
| 14 | Infrastructure documented | pass / fail / partial / N/A | <details> |
| 15 | No plain text secrets | pass / fail / partial / N/A | <details> |
| 16 | Resource limits set | pass / fail / partial / N/A | <details> |
| 17 | ADRs for infra decisions | pass / fail / partial / N/A | <details> |

### Observability Standards
| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 7 | Golden signal dashboards | pass / fail / partial / N/A | <details> |
| 8 | Time range selectors | pass / fail / partial / N/A | <details> |
| 9 | Alert runbooks | pass / fail / partial / N/A | <details> |
| 10 | Log-based alerts | pass / fail / partial / N/A | <details> |
| 11 | Loki label filters | pass / fail / partial / N/A | <details> |
| 12 | Explicit time ranges | pass / fail / partial / N/A | <details> |

### CI/CD Standards
| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 18 | CI < 10 minutes | pass / fail / partial / N/A | <details> |
| 19 | Build caching enabled | pass / fail / partial / N/A | <details> |
| 20 | Dependency caching | pass / fail / partial / N/A | <details> |
| 21 | CI config linted | pass / fail / partial / N/A | <details> |
| 22 | No hardcoded CI secrets | pass / fail / partial / N/A | <details> |
| 23 | Parallel test stages | pass / fail / partial / N/A | <details> |

### Security Standards
| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 30 | Weekly vulnerability scans | pass / fail / partial / N/A | <details> |
| 31 | CVE response timeframe | pass / fail / partial / N/A | <details> |
| 32 | Base images current/minimal | pass / fail / partial / N/A | <details> |
| 33 | Automated dependency updates | pass / fail / partial / N/A | <details> |
| 34 | Scan results triaged | pass / fail / partial / N/A | <details> |

### Developer Environment Standards
| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 46 | Dev setup docs | pass / fail / partial / N/A | <details> |
| 47 | Reproducible dev env | pass / fail / partial / N/A | <details> |
| 48 | Troubleshooting guide | pass / fail / partial / N/A | <details> |
| 49 | Doctor workflow available | pass / fail / partial / N/A | <details> |

### Summary
- **Pass**: <count> / <total applicable>
- **Fail**: <count>
- **Partial**: <count>
- **N/A**: <count>

## Gap Analysis

| # | Gap Description | Convention | Recommendation | Effort | Priority |
|---|----------------|-----------|----------------|--------|----------|
| 1 | <what is missing> | <#> | <specific remediation steps> | S/M/L | high/med/low |
| 2 | ... | ... | ... | ... | ... |

### Priority Guide
- **High**: Security risk, data loss risk, or blocks core development workflows
- **Medium**: Operational inefficiency, missing documentation, or non-compliance with standards
- **Low**: Best practice improvements, nice-to-have automation, polish

### Effort Guide
- **Small**: < 1 hour, single file change or config update
- **Medium**: 1-4 hours, multiple files, may require testing
- **Large**: > 4 hours, significant infrastructure work, may require coordination
```

## Quality Criteria

- **Comprehensive Coverage**: All seven infrastructure areas (monitoring, CI/CD, deployment, secrets, networking, data stores, backup) are documented. No area is skipped — if nothing was found, it is documented as "none" or "not applicable" with explanation.
- **Convention Compliance Assessed**: Every applicable convention from the five standard groups (infrastructure 13-17, observability 7-12, CI/CD 18-23, security 30-34, developer environment 46-49) has a pass/fail/partial/N/A status with supporting evidence.
- **Gaps Are Actionable**: Each identified gap includes a specific remediation recommendation that tells the reader what to do, not just what is wrong. Recommendations include enough detail to act on (tool names, file paths, configuration snippets where helpful).
- **Evidence-Based**: Compliance assessments reference specific files, configurations, or tool outputs as evidence. A "pass" status without evidence is not acceptable.
- **No Changes Made**: This is a read-only audit. No infrastructure files are created, modified, or deleted. Only the output artifact is written.
- **Sensitive Data Excluded**: No secret values, tokens, passwords, or API keys appear in the output. Only secret management approaches and file existence are documented.

## Context

This step is the sole working step in the `infrastructure_audit` workflow (after `gather_context`). It produces a comprehensive snapshot of the project's infrastructure health that can be used to:

1. Prioritize platform engineering work (which gaps matter most)
2. Onboard new team members (understanding the current setup)
3. Track compliance over time (re-running the audit periodically)
4. Feed into other workflows (e.g., `observability_setup` can use the monitoring section, `vulnerability_scan` can use the security section)

The convention compliance matrix covers 26 conventions across 5 groups. Not all will apply to every project — a pure Nix project will not have Kubernetes resource limits (convention 16), and a project without Loki will mark conventions 11 as N/A. The audit MUST handle these cases gracefully by marking them N/A with a brief reason rather than failing them.

The gap analysis should be prioritized pragmatically. Security gaps (plain text secrets, no vulnerability scanning) are almost always high priority. Missing documentation is important but lower priority than active security risks. The priority assignments help the user decide what to tackle first.
