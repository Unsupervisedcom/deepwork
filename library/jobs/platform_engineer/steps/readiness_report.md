# Readiness Report

## Objective

Produce two deliverables: (1) the SOC 2 compliance document that will be committed to the repository as the living record of controls and evidence, and (2) an executive readiness summary for stakeholders. The compliance document is platform-agnostic and designed to work with any compliance validator.

## Task

Synthesize the controls assessment and gap analysis into a compliance document that records the current state of SOC 2 controls, and a concise readiness summary for leadership.

### Process

#### 1. Review Prior Step Outputs

Read all three input files:
- `controls_assessment.md` — what controls exist and where evidence is
- `gap_analysis.md` — what is missing, remediation plan, priorities
- `evidence_checklist.md` — what manual evidence needs to be collected

#### 2. Create the Compliance Document

The compliance document is the primary deliverable. Per convention 60, it MUST be placed at `docs/compliance/soc2.md` (or `COMPLIANCE.md` at the repo root if no `docs/` directory exists). Create the parent directory if needed.

**Key design principles for the compliance document:**

- **Platform-agnostic** (convention 61): Record what controls exist and where evidence is found. Do NOT reference Vanta, Drata, Secureframe, or any specific compliance platform. The document describes the controls — any platform can consume this information.

- **Version-controlled** (convention 62): Structure the document so that changes produce meaningful git diffs. Use tables and consistent formatting. Avoid embedding timestamps that change on every run — use the git history for that.

- **TSC-mapped** (convention 69): Map every control to its specific TSC criteria so auditors can quickly find what they need.

- **Evidence-linked** (convention 65): Every implemented control points to where its evidence lives — a file path, a CI workflow, a configuration, or a note about where manual evidence is stored.

#### 3. Structure the Compliance Document

The compliance document should have these sections:

1. **Overview**: What this document is, what SOC 2 scope is covered, when it was last updated
2. **Scope**: Which Trust Service Criteria are in scope, which services/systems are covered
3. **Controls Matrix**: The core of the document — every control, its TSC mapping, status, and evidence reference
4. **Evidence Locations**: Index of where different types of evidence can be found
5. **Manual Evidence Tracking**: Reference to the evidence checklist (or embed it)
6. **Known Gaps**: Current gaps with remediation status (from gap analysis)
7. **Maintenance**: How and when this document should be updated

#### 4. Create the Executive Readiness Summary

A concise document for leadership that answers:
- Are we ready for a SOC 2 audit?
- What are the biggest risks?
- What needs to happen before we're ready?
- How long will remediation take?

This is NOT committed to the repo — it is a point-in-time briefing stored in the artifacts directory.

#### 5. Commit the Compliance Document

The compliance document should be placed at the correct repo location per convention 60. Use `AskUserQuestion` to confirm with the user:
- Where should the compliance document be placed? (`docs/compliance/soc2.md` recommended)
- Should it be committed now or reviewed first?

Do NOT commit without user approval. The document changes the repository's tracked files.

## Output Format

### compliance_doc.md

Place at `docs/compliance/soc2.md` (or as agreed with user).

```markdown
# SOC 2 Compliance Controls

> This document records the SOC 2 controls implemented in this repository and where
> evidence for each control can be found. It is platform-agnostic and designed to be
> consumed by any compliance management tool or auditor.
>
> **Last assessed**: YYYY-MM-DD
> **Scope**: [Trust Service Criteria in scope]
> **Systems covered**: [services, applications, infrastructure covered]

## Trust Service Criteria Scope

| TSC | In Scope | Notes |
|-----|----------|-------|
| Security (CC) | Yes | All common criteria |
| Availability (A) | Yes/No | [notes] |
| Processing Integrity (PI) | Yes/No | [notes] |
| Confidentiality (C) | Yes/No | [notes] |
| Privacy (P) | Yes/No | [notes] |

## Controls Matrix

### Security — Common Criteria

| TSC Ref | Control | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| CC1.1 | Security policies documented | Implemented | `SECURITY.md` | |
| CC1.2 | Code review required for changes | Implemented | Branch protection rules, `CODEOWNERS` | |
| CC1.3 | Background checks for personnel | Manual | See evidence checklist | HR responsibility |
| CC3.1 | Vulnerability scanning | Implemented | `.github/workflows/security.yml`, `dependabot.yml` | Weekly automated scans |
| CC6.1 | Access control mechanisms | Implemented | SSO configuration, IAM policies | |
| CC6.7 | Encryption at rest | Implemented | Database encryption config in `helm/values.yaml` | |
| CC6.8 | Encryption in transit | Implemented | TLS configuration, cert-manager | |
| CC7.1 | Monitoring and alerting | Partial | Grafana dashboards exist, alerting incomplete | See gaps |
| CC8.1 | Change management process | Implemented | PR templates, required reviews, CI gates | |
| ... | ... | ... | ... | ... |

### Availability

| TSC Ref | Control | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| A1.1 | Capacity planning | Partial | HPA configured, no capacity docs | |
| A1.2 | Disaster recovery | Missing | No DR plan documented | P1 gap |
| ... | ... | ... | ... | ... |

### Processing Integrity

| TSC Ref | Control | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| PI1.1 | Input validation | Implemented | Request validation middleware | |
| ... | ... | ... | ... | ... |

### Confidentiality

| TSC Ref | Control | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| C1.1 | Data classification | Missing | No classification policy | |
| ... | ... | ... | ... | ... |

### Privacy

| TSC Ref | Control | Status | Evidence | Notes |
|---------|---------|--------|----------|-------|
| P1.1 | Privacy notice | Implemented | `/privacy-policy` route | |
| ... | ... | ... | ... | ... |

## Evidence Locations

| Evidence Type | Location | Description |
|--------------|----------|-------------|
| CI/CD configs | `.github/workflows/` | Build, test, security scan workflows |
| Infrastructure | `helm/`, `terraform/`, `flake.nix` | Infrastructure as code |
| Security policy | `SECURITY.md` | Vulnerability reporting and response |
| Access controls | GitHub org settings, IAM policies | Authentication and authorization |
| Monitoring | Grafana dashboards, alert rules | System monitoring and alerting |
| Manual evidence | [compliance platform or shared drive] | HR records, pen tests, training |

## Manual Evidence Tracking

The following controls require evidence that is collected outside this repository.
See `evidence_checklist.md` for the full tracking sheet.

| Control | TSC Ref | Responsible | Cadence | Last Collected |
|---------|---------|-------------|---------|---------------|
| Security training records | CC1.4 | HR | Annual | [date or "pending"] |
| Background check records | CC1.3 | HR | Per hire | [date or "pending"] |
| Penetration test report | CC4.1 | Security | Annual | [date or "pending"] |
| BCP/DR test results | A1.2 | Engineering | Annual | [date or "pending"] |

## Known Gaps

| # | Gap | TSC Ref | Priority | Remediation Status |
|---|-----|---------|----------|-------------------|
| 1 | [gap description] | CC7.2 | P1 | Not started |
| 2 | [gap description] | A1.2 | P1 | Not started |
| ... | ... | ... | ... | ... |

See `gap_analysis.md` for detailed remediation plans.

## Maintenance

- This document SHOULD be updated quarterly via the `soc_audit` workflow (convention 67)
- Changes to controls should be committed with descriptive commit messages
- The evidence checklist should be reviewed and updated per each item's cadence
- When gaps are remediated, update the Controls Matrix status and add evidence references
```

### readiness_summary.md

Write to `.deepwork/tmp/platform_engineer/soc_audit/YYYY-MM-DD/readiness_summary.md`.

```markdown
# SOC 2 Readiness Summary

**Date**: YYYY-MM-DD
**Repository**: <owner/repo>
**Overall Assessment**: <Ready / Nearly Ready / Significant Gaps / Major Work Needed>

## Readiness Score

| TSC | Score | Status |
|-----|-------|--------|
| Security (CC) | X/Y controls | [status] |
| Availability (A) | X/Y controls | [status] |
| Processing Integrity (PI) | X/Y controls | [status] |
| Confidentiality (C) | X/Y controls | [status] |
| Privacy (P) | X/Y controls | [status] |

## Top Action Items

1. **[P1 gap]** — [brief remediation] — Est. [X days] — Owner: [team]
2. **[P1 gap]** — [brief remediation] — Est. [X days] — Owner: [team]
3. **[P2 gap]** — [brief remediation] — Est. [X days] — Owner: [team]
...

## Estimated Timeline to Audit-Ready

- **P1 gaps remediation**: [X weeks]
- **Evidence collection**: [X weeks]
- **Total estimated**: [X weeks] from start of remediation

## Strengths

- [What is already well-implemented]
- [Areas where the project exceeds requirements]

## Risks

- [Biggest compliance risks]
- [Areas that may require external help (pen testing, legal review)]

## Next Steps

1. [Immediate action]
2. [This week]
3. [This month]
```

## Quality Criteria

- The compliance document is platform-agnostic — it records controls and evidence without referencing any specific compliance platform per convention 61
- The document is structured for version control — changes to controls will produce meaningful diffs per convention 62
- Each control is mapped to the specific TSC criteria it satisfies per convention 69
- Evidence references point to actual locations (file paths, URLs, CI workflows) that an auditor or compliance platform can verify
- An overall readiness assessment is provided (ready, nearly ready, significant gaps)
- The top 5-10 gaps are listed with their remediation priority
- If a remediation timeline is suggested, it is realistic given the estimated effort

## Context

This is the final step of the `soc_audit` workflow. It produces the compliance document that lives in the repository as the long-term record of SOC 2 controls. The compliance document is designed to be updated over time — each run of the `soc_audit` workflow updates it with the latest assessment. The executive summary is a point-in-time snapshot for stakeholders.

The key value of the compliance document is that it creates a single source of truth for "what controls do we have and where is the evidence?" This makes the actual SOC 2 audit (or audit preparation via any platform) significantly smoother because the auditor or platform can follow the evidence references rather than asking the team to produce evidence on demand.
