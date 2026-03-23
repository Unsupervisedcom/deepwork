# Plan Infrastructure Migration

## Objective

Analyze the current infrastructure state, design a migration strategy with validation gates and rollback procedures, and create a GitHub issue with a detailed checklist to track execution. The migration plan MUST be thorough enough that the `execute_migration` step can follow it mechanically, and the rollback plan MUST be documented before any migration steps are defined (per convention 40).

## Task

Document the current state of the component being migrated, design a migration strategy appropriate to the risk level, create a step-by-step plan with validation gates, and publish a GitHub issue to track the migration.

### Process

#### 1. Read context.md and migration_description

- Load `context.md` from `gather_context` to understand the infrastructure type, available tools, and repo structure
- Read the `migration_description` input — this is the user's description of what is being migrated (e.g., "migrate from Zalando Postgres operator to CNPG", "move from Docker Compose to Kubernetes", "migrate from EC2 to ECS Fargate")
- Identify the scope: is this a data migration, a control plane migration, a deployment method change, or a combination?

#### 2. Document current state in detail

Investigate and record the current state of the component being migrated. This is critical because the migration plan depends on an accurate understanding of what exists today.

**What is currently deployed and how:**
- For Kubernetes: `kubectl get <resource-type> -A` to list relevant resources, check CRD definitions, Helm releases (`helm list -A`), operator deployments
- For Nix/NixOS: read the relevant NixOS module configuration, check `systemctl status` for running services, check Nix generations
- For cloud-managed: query the cloud provider API (e.g., `aws rds describe-db-instances`, `gcloud sql instances list`)
- For Docker Compose: read `docker-compose.yml`, check `docker compose ps`
- Document versions, configurations, and any customizations

**Data schemas, volumes, persistent state:**
- Identify all persistent data: databases, PVCs, mounted volumes, S3 buckets, local data directories
- Document data sizes where possible (`kubectl exec` to check disk usage, cloud console, `du -sh`)
- Note data schemas if relevant (database schemas, config file formats)
- Identify any data that would be difficult or impossible to recreate if lost

**Dependencies and consumers:**
- What services depend on the component being migrated?
- What services does the component depend on?
- Are there external consumers (other teams, third-party integrations, DNS records, load balancers)?
- Are there cron jobs, scheduled tasks, or background workers that interact with this component?
- Document connection strings, endpoints, and ports that consumers currently use

**Current backup and recovery procedures:**
- How is the component currently backed up? (automated snapshots, manual dumps, replication, none)
- What is the recovery time objective (RTO) and recovery point objective (RPO)?
- Has a recovery ever been tested?
- If no backup exists, flag this as a pre-migration prerequisite

#### 3. Design migration strategy

Choose a migration approach based on the risk level, downtime tolerance, and complexity.

**Migration approaches:**

| Approach | Best For | Downtime | Complexity | Rollback |
|----------|----------|----------|------------|----------|
| **Big-bang** | Simple, low-risk, short migration | Minutes to hours | Low | Full rollback or none |
| **Blue-green** | Stateless services, infra swaps | Near-zero | Medium | Switch back to blue |
| **Canary** | User-facing services, gradual rollout | None | High | Route traffic back |
| **Rolling** | Stateless replicas, config changes | None | Medium | Roll back replicas |
| **Parallel-run** | Data systems, critical services | None during migration | High | Keep old system |

Use `AskUserQuestion` to discuss the approach with the user. Present:
- The recommended approach and why
- Downtime implications
- Rollback complexity
- Whether a maintenance window is needed
- Ask about downtime tolerance and any scheduling constraints

**For operator migrations (e.g., Zalando to CNPG, Flux to ArgoCD):**
- Map CRD fields from the old operator to the new operator
- Identify feature gaps: capabilities the old operator has that the new one does not
- Determine data migration path: can data be preserved in place, or must it be exported and imported?
- Plan for the transition period when both operators might need to coexist

**For imperative-to-declarative migrations (e.g., manual setup to IaC):**
- Audit all current manual steps (interview the user if needed via AskUserQuestion)
- For each manual step, design the IaC equivalent
- Use import/adopt features if available (e.g., `terraform import`, `pulumi import`) to bring existing resources under management without recreation
- Plan for drift detection after migration

#### 4. Create rollback plan first (per convention 40)

The rollback plan MUST be documented before defining detailed migration steps. See section 6 below for the full rollback plan structure. Write the rollback plan first, then return here to define the migration steps.

#### 5. Create detailed migration plan with validation gates

Structure the migration as an ordered sequence of phases, each containing steps with validation gates (per convention 44).

**Pre-migration phase:**
1. **Backup**: Create a full backup of the component's data and configuration
   - Validation gate: backup exists and is verified (checksum, restore test to a separate location)
2. **Freeze**: Stop or pause any automated changes (disable CI deployments, pause cron jobs)
   - Validation gate: no automated processes will modify the component during migration
3. **Health check**: Verify the current system is healthy before starting
   - Validation gate: all health endpoints return 200, no active alerts, no error spikes
4. **Communication**: Notify stakeholders of the migration window
   - Validation gate: stakeholders acknowledged (or AskUserQuestion to confirm notification was sent)
5. **Dependencies ready**: Verify the target environment is prepared (new operator installed, new cloud resources provisioned, etc.)
   - Validation gate: target environment passes smoke test

**Migration phase:**
Each step MUST include:
- **Step number and title**: e.g., "Step 3: Migrate database schema"
- **Description**: What this step does, in plain language
- **Commands**: Exact commands to execute (with placeholder values clearly marked as `<PLACEHOLDER>`)
- **Validation gate**: A specific check that confirms the step succeeded. Examples:
  - `kubectl get pods -l app=<service> | grep Running` — verify pods are running
  - `curl -f http://<endpoint>/health` — verify health endpoint responds
  - `psql -c "SELECT count(*) FROM <table>"` — verify data row counts match
  - Compare checksums of exported/imported data
- **Estimated duration**: How long this step should take
- **Rollback for this step**: How to undo just this step if it fails

**Post-migration phase:**
1. **Verification**: Run comprehensive health checks on the new system
   - Compare key metrics (request rate, error rate, latency) between old and new
   - Verify data integrity (row counts, checksums, sample queries)
2. **Monitoring**: Watch dashboards and alerts for a defined soak period
   - Define the soak period duration (e.g., 1 hour for low-risk, 24 hours for high-risk)
3. **Cleanup**: Remove old resources (only after soak period passes)
   - List exactly what will be removed
   - Note any resources that should be kept for a grace period
4. **Documentation update**: Update infrastructure documentation per convention 14

#### 6. Rollback plan structure (per convention 40)

The rollback plan MUST answer:

**Rollback feasibility:**
- At what point during the migration is rollback still possible?
- Is there a "point of no return" after which rollback is not feasible? If so, identify it explicitly.
- What is the maximum acceptable rollback time?

**Data implications:**
- What data might be lost if rollback is triggered after step N?
- For data systems: can writes that occurred after migration be replayed or are they lost?
- For stateless services: rollback is typically clean — document this explicitly

**Rollback procedure:**
- Step-by-step commands to revert to the pre-migration state
- How to verify the rollback succeeded (same validation gates as the pre-migration health check)
- How to restore from the backup created in the pre-migration phase

**Communication:**
- Who needs to be notified if rollback is triggered?
- What is the rollback decision authority? (who decides to rollback)

#### 7. Create GitHub issue with detailed checklist (per convention 41)

Create a GitHub issue using `gh issue create` that serves as the live tracking document for the migration.

**Issue title**: `platform: migrate <component> from <old> to <new>`

**Issue body structure:**
```markdown
## Migration: <brief description>

**Migration Plan**: <link to migration_plan.md in the repo or artifact directory>
**Target Date**: <date or TBD>
**Estimated Duration**: <from the plan>
**Risk Level**: Low / Medium / High
**Downtime Expected**: None / <duration>

## Pre-Migration

- [ ] Full backup created and verified
- [ ] Automated processes paused (CI deploys, crons)
- [ ] Current system health verified
- [ ] Stakeholders notified
- [ ] Target environment prepared and smoke-tested

## Migration Steps

- [ ] Step 1: <title> — Validation: <gate description>
- [ ] Step 2: <title> — Validation: <gate description>
- [ ] Step 3: <title> — Validation: <gate description>
...

## Post-Migration

- [ ] Comprehensive health check passed
- [ ] Key metrics compared (old vs new)
- [ ] Data integrity verified
- [ ] Monitoring soak period completed (<duration>)
- [ ] Old resources cleaned up
- [ ] Infrastructure documentation updated

## Rollback

If rollback is needed, see the rollback section of the migration plan.
Point of no return: <step number or "none — rollback is always possible">
```

**Labels**: `platform`, `migration`, and a priority label (`P1` for critical systems, `P2` for important, `P3` for low-risk)

Record the created issue URL in `github_issue_url.md`.

## Output Format

Write two output files:

### migration_plan.md

```markdown
# Migration Plan: <brief description>

**Date**: YYYY-MM-DD
**Migration**: <what is being migrated, from what to what>
**Approach**: <big-bang / blue-green / canary / rolling / parallel-run>
**Risk Level**: Low / Medium / High
**Estimated Duration**: <total duration>
**Downtime Expected**: None / <duration>

## Current State

### Component Overview
<description of what is deployed, how, and where>

### Data and Persistent State
| Resource | Type | Size | Backup Status |
|----------|------|------|---------------|
| <resource> | PVC / RDS / volume / etc. | <size> | backed up / not backed up |

### Dependencies
| Consumer | Connection Method | Impact if Unavailable |
|----------|------------------|----------------------|
| <service> | <endpoint/port/DNS> | <impact> |

### Current Backup Procedures
<description of existing backup and recovery>

## Migration Strategy

### Approach: <chosen approach>
**Rationale**: <why this approach was chosen>

### Operator/CRD Mapping (if applicable)
| Old Resource Field | New Resource Field | Notes |
|-------------------|-------------------|-------|
| <old.field> | <new.field> | <differences or caveats> |

### Feature Gap Analysis (if applicable)
| Feature | Old System | New System | Mitigation |
|---------|-----------|-----------|------------|
| <feature> | supported | supported / unsupported | <mitigation if unsupported> |

## Rollback Plan

**Point of No Return**: Step <N> / None — rollback is always possible
**Maximum Rollback Time**: <duration>

### Data Loss on Rollback
| After Step | Data at Risk | Acceptable? |
|-----------|-------------|-------------|
| Step <N> | <description> | Yes / No — <mitigation> |

### Rollback Procedure
1. <step with exact commands>
2. <step with exact commands>
...

### Rollback Verification
<how to confirm rollback succeeded>

## Pre-Migration Phase

### Step P1: Create Backup
- **Action**: <exact commands>
- **Validation Gate**: <check that confirms backup exists and is valid>
- **Estimated Duration**: <time>

### Step P2: Freeze Automated Changes
...

### Step P3: Health Check
...

### Step P4: Notify Stakeholders
...

### Step P5: Prepare Target Environment
...

## Migration Phase

### Step M1: <title>
- **Action**: <exact commands with <PLACEHOLDER> values marked>
- **Validation Gate**: <specific check>
- **Estimated Duration**: <time>
- **Step Rollback**: <how to undo just this step>

### Step M2: <title>
...

## Post-Migration Phase

### Step V1: Health Check
...

### Step V2: Metrics Comparison
...

### Step V3: Data Integrity Verification
...

### Step V4: Monitoring Soak Period
- **Duration**: <time>
- **Watch For**: <specific metrics/alerts>

### Step V5: Cleanup
- **Resources to Remove**: <list>
- **Grace Period**: <time before removal>

### Step V6: Documentation Update
...

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| <risk> | Low/Med/High | Low/Med/High | <mitigation> |

## GitHub Issue
Created: <issue URL>
```

### github_issue_url.md

```markdown
<URL of the created GitHub issue>
```

## Quality Criteria

- **Current State Documented**: The current infrastructure state is fully documented including deployed components, data/persistent state with sizes, dependencies with connection methods, and existing backup procedures. The documentation is based on actual investigation (commands run, configs read), not assumptions.
- **Rollback Plan**: A rollback plan is documented before any migration steps per convention 40. The plan includes the point of no return, data loss implications for each step, step-by-step rollback commands, and rollback verification checks.
- **Validation Gates**: Each migration step has a specific, executable validation gate per convention 44. Validation gates are concrete (exact commands to run and expected output), not vague ("verify it works").
- **GitHub Issue Created**: A GitHub issue with a detailed checklist is created via `gh issue create` per convention 41. Each checklist item maps to a migration step and includes a brief description of the validation gate. The issue is labeled appropriately.
- **Risk Assessment**: Risks are identified with likelihood and impact ratings, and each risk has a documented mitigation strategy. High-risk items are flagged clearly.
- **User Confirmed**: The migration strategy was discussed with the user via AskUserQuestion, including downtime implications and scheduling constraints. The user's constraints and preferences are reflected in the plan.
- **Approach Justified**: The chosen migration approach (big-bang, blue-green, canary, rolling, parallel-run) is justified with rationale tied to the specific migration's risk profile and the user's downtime tolerance.

## Context

This step is the first of two in the `infrastructure_migration` workflow (`plan_migration` -> `execute_migration`). It runs after `gather_context`, which provides the `context.md` file describing the project's infrastructure type, available tools, and repo structure.

The migration plan produced here is the primary input to the `execute_migration` step, which will follow the plan step by step, running validation gates at each stage. Therefore, every step in the plan MUST include exact commands (or clearly marked placeholders) and a concrete validation gate.

The GitHub issue created here serves as the live tracking document during execution. The `execute_migration` step will check off items as they are completed (per convention 45).

Key conventions referenced:
- Convention 13: Infrastructure changes MUST be declarative
- Convention 14: Infrastructure configuration MUST be documented
- Convention 40: Migrations MUST have a documented rollback plan before execution begins
- Convention 41: Migration plans MUST be documented in a GitHub issue with a detailed checklist
- Convention 42: Data migrations MUST be tested against a copy of production data before production execution
- Convention 43: Blue-green or canary deployment SHOULD be used for critical service migrations
- Convention 44: Each migration step MUST have a validation gate
- Convention 45: Migration state MUST be tracked in the GitHub issue
