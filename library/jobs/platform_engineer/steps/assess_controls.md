# Assess Controls

## Objective

Auto-discover existing controls across all five SOC 2 Trust Service Criteria by examining the repository's code, CI/CD configuration, infrastructure setup, documentation, and tooling. Produce an inventory of controls with evidence references and classification status.

## Task

Systematically examine the project to identify which SOC 2 controls are already in place, which are partially implemented, and which are missing. The assessment must be based on actual configuration and code — not just the existence of documentation claiming a control exists.

### Process

#### 1. Read Context and Plan Assessment

Read `context.md` to understand:
- Infrastructure type (k8s, nix, cloud-managed, hybrid)
- Available tools and CI provider
- Repository structure and existing configurations

This determines which controls can be verified automatically and which require manual evidence.

#### 2. Assess Security Controls (Common Criteria — CC)

Check for controls across the CC categories:

**CC1 — Control Environment:**
- Check for `SECURITY.md`, security policies, or `docs/security/` directory
- Check for CODEOWNERS file (code review requirements)
- Check for branch protection rules: `gh api repos/{owner}/{repo}/branches/main/protection` or equivalent

**CC2 — Communication and Information:**
- Check for incident response documentation
- Check for onboarding docs or `docs/onboarding/`
- Check for architecture documentation or ADRs

**CC3 — Risk Assessment:**
- Check for vulnerability scanning in CI (Dependabot, Renovate, Snyk, Trivy)
- Check for `dependabot.yml` or `renovate.json`
- Check for security scanning workflows

**CC4 — Monitoring:**
- Check for monitoring/alerting configuration (Grafana, PagerDuty, OpsGenie)
- Check for audit logging configuration
- Check for error tracking (Sentry, Honeybadger)

**CC5 — Control Activities:**
- Check for CI/CD pipeline enforcing tests before merge
- Check for required code review (branch protection, CODEOWNERS)
- Check for linting and static analysis in CI
- Check for environment separation (prod/staging/dev)

**CC6 — Logical and Physical Access Controls:**
- Check for authentication configuration (SSO, MFA references)
- Check for RBAC / IAM configuration files
- Check for secrets management (vault, sealed-secrets, SOPS, env vars in CI secrets)
- Check for `.env.example` (documenting required env vars without values)
- Check for network policies (k8s NetworkPolicy, security groups, firewall rules)
- Check encryption at rest configuration (database encryption, disk encryption)
- Check encryption in transit (TLS configuration, cert-manager, HTTPS enforcement)

**CC7 — System Operations:**
- Check for backup configuration
- Check for disaster recovery documentation
- Check for change management process (PR templates, commit conventions)
- Check for deployment automation (CI/CD deploy workflows)

**CC8 — Change Management:**
- Check for PR templates or contribution guidelines
- Check for required reviews before merge
- Check for staging/pre-production environments
- Check for rollback procedures documented

**CC9 — Risk Mitigation:**
- Check for vendor management documentation
- Check for third-party dependency inventory (SBOMs, license checks)

#### 3. Assess Availability Controls (A Series)

**A1 — System Availability:**
- Check for uptime monitoring (health check endpoints, synthetic monitoring)
- Check for SLA documentation
- Check for auto-scaling configuration (HPA, Karpenter, cloud auto-scaling)
- Check for load balancing configuration
- Check for redundancy (multi-AZ, replicas, failover)
- Check for capacity planning documentation
- Check for disaster recovery / business continuity plans

#### 4. Assess Processing Integrity Controls (PI Series)

**PI1 — Processing Integrity:**
- Check for input validation patterns in code (request validation, schema validation)
- Check for data validation in database (constraints, migrations)
- Check for QA/testing processes (test suites, integration tests, e2e tests)
- Check for data processing pipelines with idempotency guarantees
- Check for error handling patterns (retry logic, dead letter queues)

#### 5. Assess Confidentiality Controls (C Series)

**C1 — Confidentiality:**
- Check for data classification documentation
- Check for encryption at rest (database, file storage, backups)
- Check for encryption in transit (TLS, mTLS between services)
- Check for access control on data stores (IAM policies, network restrictions)
- Check for data retention policies
- Check for secure deletion procedures
- Check `.gitignore` for sensitive file patterns

#### 6. Assess Privacy Controls (P Series)

**P1 — Privacy:**
- Check for privacy policy documentation
- Check for cookie consent or consent management code
- Check for PII handling patterns (anonymization, pseudonymization)
- Check for data subject access request (DSAR) procedures
- Check for data processing agreements documentation
- Check for breach notification procedures
- Check for data minimization patterns in code

#### 7. Classify Each Control

For each control discovered (or not), classify it per convention 64:

- **Implemented**: The control exists and evidence is verifiable. Reference the specific file, config, or system where evidence lives.
- **Partial**: The control is partially implemented or evidence is incomplete. Note what exists and what is missing.
- **Missing**: The control is not implemented. No evidence found.

For automated controls (encryption, scanning, access controls), verify by checking the actual configuration — not just by confirming a document says it exists (per convention 68).

#### 8. Create Artifact Directory

```bash
mkdir -p .deepwork/tmp/platform_engineer/soc_audit/$(date +%Y-%m-%d)/
```

## Output Format

### controls_assessment.md

Write to `.deepwork/tmp/platform_engineer/soc_audit/YYYY-MM-DD/controls_assessment.md`.

```markdown
# SOC 2 Controls Assessment

**Date**: YYYY-MM-DD
**Repository**: <owner/repo>
**Infrastructure Type**: <from context.md>
**Assessment Method**: Automated discovery + manual review flags

## Summary

| Trust Service Criteria | Implemented | Partial | Missing | Total |
|----------------------|------------|---------|---------|-------|
| Security (CC) | X | X | X | X |
| Availability (A) | X | X | X | X |
| Processing Integrity (PI) | X | X | X | X |
| Confidentiality (C) | X | X | X | X |
| Privacy (P) | X | X | X | X |
| **Total** | **X** | **X** | **X** | **X** |

## Security Controls (Common Criteria)

### CC1 — Control Environment

| Control | TSC Ref | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| Security policy documented | CC1.1 | implemented / partial / missing | `SECURITY.md` | |
| Code review required | CC1.2 | implemented / partial / missing | `.github/CODEOWNERS`, branch protection | |
| ... | ... | ... | ... | ... |

### CC2 — Communication and Information
...

### CC3 — Risk Assessment
...

[Continue for all CC categories and all 5 TSCs]

## Automated Controls Verification

| Control | Expected Config | Actual Config | Verified |
|---------|----------------|---------------|----------|
| Encryption at rest | <expected> | <what was found> | yes/no |
| Vulnerability scanning | <expected> | <what was found> | yes/no |
| Access logging | <expected> | <what was found> | yes/no |
| ... | ... | ... | ... |

## Evidence Index

| Evidence Type | Location | Controls Covered |
|--------------|----------|-----------------|
| CI workflow | `.github/workflows/security.yml` | CC3.1, CC7.2 |
| Branch protection | GitHub branch protection rules | CC5.1, CC8.1 |
| Encryption config | `helm/values.yaml` (database.ssl) | CC6.7, C1.1 |
| ... | ... | ... |
```

## Quality Criteria

- Controls are assessed across all five Trust Service Criteria: Security (CC), Availability, Processing Integrity, Confidentiality, and Privacy
- Each implemented control references where the evidence can be found (file path, CI workflow, config, policy) per convention 65
- Every control is classified as implemented, partial, or missing per convention 64
- Automated controls are verified by checking actual infrastructure configuration, not just documentation per convention 68
- The assessment is based on what was actually discovered in the repository, not a generic checklist

## Context

This is the first working step in the `soc_audit` workflow. The quality of the gap analysis and readiness report depends entirely on how thorough this assessment is. Focus on automated discovery — examine actual code, configs, and CI workflows rather than relying on documentation claims. When a control cannot be verified automatically (e.g., HR processes, physical security), flag it for manual verification in the next step's evidence checklist.
