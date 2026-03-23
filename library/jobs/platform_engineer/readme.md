# Platform Engineer

A comprehensive platform engineering job for discovering gaps, setting up infrastructure, and maintaining production systems. Technology-agnostic — adapts to Kubernetes, Nix, cloud-managed, or hybrid environments.

## Overview

This job covers the full lifecycle of platform engineering work:

- **Incident response**: Investigate production incidents from triage to report
- **Developer experience**: Debug local dev environments and unblock developers
- **Observability**: Set up and manage monitoring stacks and Grafana dashboards
- **CI/CD**: Audit and optimize build pipelines
- **Releases**: Set up release pipelines, branching strategies, and release notes
- **Security**: Vulnerability scanning and remediation planning
- **Cost management**: Cloud spend analysis and waste identification
- **Infrastructure**: Audit documentation, plan migrations, convert imperative to declarative
- **Error tracking**: Set up exception monitoring (Sentry, etc.)

## Quick Start

Natural language is matched to the `platform_engineer` job's `incident_investigation` workflow. Triages the incident, gathers logs and metrics, and produces a structured incident report.

```
/deepwork the staging deploy is returning 502s, investigate
```

## Workflows

| Workflow | When to Use |
|----------|-------------|
| `incident_investigation` | Production incident needs full investigation and report |
| `quick_investigate` | Quick triage without formal report |
| `doctor` | Local dev environment is broken |
| `error_tracking` | Setting up exception monitoring for a project |
| `dashboard_management` | Creating or auditing Grafana dashboards |
| `cicd_optimization` | Build times are slow or CI costs are high |
| `release_builder` | Setting up release automation for a repo |
| `infrastructure_audit` | Documenting or assessing infrastructure setup |
| `cloud_spend` | Reviewing cloud costs for waste |
| `vulnerability_scan` | Running or reviewing security scans |
| `observability_setup` | Setting up Prometheus/Loki/VictoriaMetrics |
| `infrastructure_migration` | Migrating between infrastructure providers or operators |
| `platform_issue` | Creating a GitHub issue for platform work (maps to `/platform.issue`) |

## Conventions

This job carries its own RFC 2119 conventions in `conventions.md`. All workflows reference these standards. Key areas: investigation principles, observability, infrastructure, CI/CD, releases, security, cloud costs, migrations, developer experience, and error tracking.

## Artifacts

Workflow outputs are stored in `.deepwork/artifacts/platform_engineer/<workflow>/<date-slug>/`.

## Usage

1. Copy this job folder to your project's `.deepwork/jobs/` directory
2. Run `/deepwork` and select the `platform_engineer` job
3. Choose the appropriate workflow for your task

## Customization

- Edit `conventions.md` to adjust standards for your organization
- Modify step instructions to add project-specific tooling or processes
- The `common_job_info_provided_to_all_steps_at_runtime` field in `job.yml` can be extended with project-specific context
