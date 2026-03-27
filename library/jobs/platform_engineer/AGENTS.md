# Platform Engineer Job

This folder contains the `platform_engineer` job — a comprehensive platform engineering toolkit.

## Recommended Workflows

- `incident_investigation` — Full incident investigation from triage to report
- `doctor` — Debug and fix local dev environment issues
- `dashboard_management` — Inspect and develop Grafana dashboards
- `cicd_optimization` — Review and optimize CI/CD pipelines
- `release_builder` — Set up release pipelines and automation
- `platform_issue` — Create a GitHub issue from current context

## Directory Structure

```
platform_engineer/
├── job.yml              # Job definition (23 steps, 14 workflows)
├── conventions.md       # RFC 2119 platform engineering standards
├── readme.md            # User-facing documentation
├── AGENTS.md            # This file — agent context and learnings
├── steps/               # Step instruction files
└── templates/           # Output templates
```

## Editing Guidelines

- `conventions.md` is the source of truth for standards — update it first, then update step instructions that reference the changed conventions
- Step instructions reference conventions by number (e.g., "per convention 7")
- The `gather_context` step is shared by all workflows except `platform_issue` — changes affect almost all workflows
- When adding a new workflow, ensure all steps appear in at least one workflow

## Learnings

### Artifact Storage
- **Requirement**: Workflow artifacts (context, assessments, plans) MUST be stored in `.deepwork/tmp/platform_engineer/` instead of `.deepwork/artifacts/`.
- **Reasoning**: The `.deepwork/tmp/` directory is globally gitignored in Keystone projects, ensuring temporary investigation artifacts don't clutter the main repository history. Canonical sources remain the repo JSON or GitHub issues.
- **Reference**: Updated in `job.yml` and all step instruction files.

### Grafana Integration
- **Key Insight**: Always prefer declarative dashboard provisioning in Nix modules over manual API pushes when possible.
- **Tooling**: The `ks` tool's `grafana dashboards apply` command is a useful iteration helper but should not be the primary provisioning method for production.
