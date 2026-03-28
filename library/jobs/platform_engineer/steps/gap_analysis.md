# Gap Analysis

## Objective

Compare the discovered controls against SOC 2 requirements, identify gaps and partial implementations, produce remediation recommendations with priority and effort estimates, and generate an evidence collection checklist for controls that require manual evidence.

## Task

Using the controls assessment, systematically identify what is missing or incomplete for SOC 2 readiness. Produce two outputs: a gap analysis with remediation plan, and an evidence checklist for items that require manual collection.

### Process

#### 1. Review the Controls Assessment

Read `controls_assessment.md` to understand:
- Which controls are implemented, partial, or missing
- Where evidence exists for implemented controls
- Which controls were verified automatically vs. flagged for manual review

Read `context.md` to understand the infrastructure type, which affects which controls are expected.

#### 2. Identify Gaps by TSC

For each Trust Service Criteria, compare the discovered controls against what SOC 2 auditors typically examine. Focus on:

**High-priority gaps** (auditors always check these):
- Access controls and authentication (CC6)
- Change management / code review (CC8)
- Monitoring and incident response (CC4, CC7)
- Encryption at rest and in transit (CC6, C1)
- Vulnerability management (CC3)
- Backup and recovery (A1, CC7)
- Logging and audit trails (CC4)

**Medium-priority gaps** (commonly examined):
- Data retention policies (C1, P1)
- Vendor/third-party management (CC9)
- Capacity planning and availability (A1)
- Input validation and processing integrity (PI1)
- Privacy controls (P1)

**Lower-priority gaps** (depends on scope):
- Physical security (typically handled by cloud provider)
- HR-related controls (onboarding, background checks)
- Training and awareness programs

#### 3. Map Gaps to TSC Criteria

Each gap MUST reference the specific TSC criteria it violates (per convention 69). Use the standard SOC 2 criteria numbering:

- **CC1.1-CC1.5**: Control environment
- **CC2.1-CC2.3**: Communication and information
- **CC3.1-CC3.4**: Risk assessment
- **CC4.1-CC4.2**: Monitoring activities
- **CC5.1-CC5.3**: Control activities
- **CC6.1-CC6.8**: Logical and physical access
- **CC7.1-CC7.5**: System operations
- **CC8.1**: Change management
- **CC9.1-CC9.2**: Risk mitigation
- **A1.1-A1.3**: Availability
- **PI1.1-PI1.5**: Processing integrity
- **C1.1-C1.2**: Confidentiality
- **P1.1-P1.2**: Privacy (if in scope)

#### 4. Produce Remediation Recommendations

For each gap, provide (per convention 70):

- **What is missing**: Specific control or evidence that is absent
- **Why it matters**: Which TSC criteria it violates and what risk it represents
- **Remediation**: Specific steps to implement the control or gather the evidence
- **Estimated effort**: Small (< 1 day), Medium (1-5 days), Large (1-2 weeks), XL (> 2 weeks)
- **Priority**: P1 (auditors always check), P2 (commonly examined), P3 (depends on scope)

#### 5. Generate Evidence Collection Checklist

Separate controls into two categories:

**Automated evidence** (can be verified from repo/infra):
- These should NOT appear in the manual checklist — they are already documented in the controls assessment
- Examples: CI workflows, branch protection, encryption configs, vulnerability scans

**Manual evidence** (requires human collection):
- Per convention 66, list each with responsible party and collection cadence
- Examples:
  - HR onboarding documentation with security training records
  - Background check policy and completion records
  - Annual security awareness training completion
  - Business continuity plan testing results
  - Vendor risk assessment documentation
  - Board/management meeting minutes discussing security
  - Penetration test reports
  - Insurance policy documentation
  - Physical security documentation (if applicable)
  - Data processing agreements with sub-processors

For each manual evidence item:
- **Control**: What SOC 2 control this satisfies
- **Evidence needed**: Specific document or record
- **Responsible party**: Who should collect this (e.g., "Engineering Lead", "HR", "Security Team")
- **Cadence**: How often this needs to be updated (annual, quarterly, per-incident, per-hire)
- **Last collected**: "Unknown — needs initial collection" or a date if known
- **Storage location**: Where the evidence should be stored (the compliance doc will reference this)

#### 6. Assess Overall Readiness

Based on the gap analysis, provide an overall readiness assessment:

- **Ready**: No P1 gaps, few P2 gaps, mostly evidence collection remaining
- **Nearly Ready**: A few P1 gaps with known remediations, most controls in place
- **Significant Gaps**: Multiple P1 gaps requiring implementation work
- **Major Work Needed**: Fundamental controls are missing across multiple TSCs

## Output Format

### gap_analysis.md

Write to `.deepwork/tmp/platform_engineer/soc_audit/YYYY-MM-DD/gap_analysis.md`.

```markdown
# SOC 2 Gap Analysis

**Date**: YYYY-MM-DD
**Repository**: <owner/repo>
**Overall Readiness**: <Ready / Nearly Ready / Significant Gaps / Major Work Needed>

## Summary

| Priority | Count | Estimated Total Effort |
|----------|-------|----------------------|
| P1 (must fix) | X | X days |
| P2 (should fix) | X | X days |
| P3 (nice to have) | X | X days |
| **Total** | **X** | **X days** |

## Gaps by Trust Service Criteria

### Security (CC)

#### GAP: [Short description]
- **TSC Criteria**: CC6.1, CC6.3
- **Status**: Missing / Partial
- **What is missing**: [Specific description]
- **Risk**: [What could go wrong without this control]
- **Remediation**:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
- **Effort**: Medium (3 days)
- **Priority**: P1

#### GAP: [Short description]
...

### Availability (A)
...

### Processing Integrity (PI)
...

### Confidentiality (C)
...

### Privacy (P)
...

## Remediation Roadmap

### Immediate (P1 — do first)
| # | Gap | TSC | Effort | Owner |
|---|-----|-----|--------|-------|
| 1 | [gap] | CC6.1 | Medium | Engineering |
| 2 | [gap] | CC7.2 | Small | DevOps |

### Soon (P2 — plan for this quarter)
| # | Gap | TSC | Effort | Owner |
|---|-----|-----|--------|-------|
| ... | ... | ... | ... | ... |

### Later (P3 — backlog)
| # | Gap | TSC | Effort | Owner |
|---|-----|-----|--------|-------|
| ... | ... | ... | ... | ... |
```

### evidence_checklist.md

Write to `.deepwork/tmp/platform_engineer/soc_audit/YYYY-MM-DD/evidence_checklist.md`.

```markdown
# SOC 2 Evidence Collection Checklist

**Date**: YYYY-MM-DD
**Repository**: <owner/repo>
**Purpose**: Track collection of evidence that requires manual gathering.
Automated evidence (CI configs, code, infrastructure) is documented in controls_assessment.md.

## Instructions

This checklist covers controls where evidence must be collected from people, processes,
or systems outside the repository. Assign each item to the responsible party and track
completion. This checklist should be reviewed and updated per the cadence column.

## Checklist

| # | Control | TSC Ref | Evidence Needed | Responsible | Cadence | Status | Location |
|---|---------|---------|----------------|-------------|---------|--------|----------|
| 1 | Security training | CC1.4 | Training completion records | HR | Annual | [ ] Not collected | |
| 2 | Background checks | CC1.3 | Background check policy + records | HR | Per hire | [ ] Not collected | |
| 3 | Pen test | CC4.1 | Penetration test report | Security | Annual | [ ] Not collected | |
| 4 | BCP test | A1.2 | BCP/DR test results | Engineering | Annual | [ ] Not collected | |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Notes

- [ ] Items marked "Not collected" need initial evidence gathering
- [ ] Store evidence in a location accessible to auditors (shared drive, compliance platform, or repo)
- [ ] Update the compliance document (`docs/compliance/soc2.md`) with evidence locations once collected
```

## Quality Criteria

- Each gap references the specific TSC criteria it violates (e.g., CC6.1, A1.2) per convention 69
- Each gap includes a remediation recommendation with estimated effort and priority per convention 70
- Gaps are prioritized by audit risk — controls that auditors always check are flagged as P1
- All controls requiring manual evidence are listed with responsible party and collection cadence per convention 66
- Controls that can be verified automatically are not in the manual checklist
- The overall readiness assessment is realistic given the number and severity of gaps

## Context

This step bridges the raw assessment and the final compliance document. The gap analysis tells the team what to fix, in what order. The evidence checklist tells them what manual evidence to collect. Both outputs feed into the readiness report, which produces the compliance document that lives in the repository. The gap analysis should be actionable enough that an engineering team can turn it into a sprint plan.
