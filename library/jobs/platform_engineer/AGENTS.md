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

- `release_builder` should follow the repository's standard docs convention for the canonical release doc when one exists; otherwise use `docs/releases.md` or `docs/platform/releases.md`. Keep the root `AGENTS.md` concise by linking to that doc instead of duplicating release details.
- CI-provider-specific release behavior belongs in `.github/AGENTS.md` and/or `.forgejo/AGENTS.md`. Those files should explain workflow entrypoints, required secrets, and release-specific CI expectations, while the root `AGENTS.md` only points to them.
- `release_builder` must ask the user to define the release policy before wiring automation when cadence, version semantics, stabilization, backports, hotfixes, merge-back, publish targets, or stable-versus-unstable consumption are not already explicit in the repo. The job should implement the chosen policy, not infer one from tooling defaults.
