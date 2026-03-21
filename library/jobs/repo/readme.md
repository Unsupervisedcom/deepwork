# Repo

Audit and configure repositories to follow team conventions across any git provider.

## Overview

This job ensures repositories have consistent labels, branch protection, milestones, and project boards. It detects the git provider automatically from the remote URL and uses provider-agnostic instructions — the agent's tool conventions handle CLI specifics.

Two workflows are provided:

1. **setup** — Make a repo ready for work: create missing labels, check branch protection, verify milestones and boards
2. **doctor** — Audit existing state and fix drift: find duplicates, enable missing protections, correct label drift, reconcile board items

## Provider Support

The job detects the provider from `git remote get-url origin`:

| Provider | Labels | Branch Protection | Milestones | Boards |
|----------|--------|-------------------|------------|--------|
| GitHub | Full | Full | Full | Full (Projects V2) |
| Forgejo/Gitea | Full | Full | Full | Manual (no board API) |
| GitLab | Full | Full | Full | Varies |

When the provider lacks a board API, board steps output manual web UI instructions instead of CLI automation.

## Prerequisites

- A git CLI (`git`) for remote URL detection
- The provider's CLI tool (e.g. `gh` for GitHub, `fj`/`tea` for Forgejo)
- Authenticated CLI session with sufficient scopes

## Workflows

### setup

Makes a repo ready for work by checking four concerns:

```
detect_platform → [ensure_labels, check_branch_protection] → check_milestones → check_boards → setup_report
```

Produces a pass/fail readiness report.

### doctor

Audits existing state and fixes drift:

```
detect_platform → [audit_labels, audit_branch_protection] → audit_milestones → audit_boards → doctor_report
```

Produces a health report with findings, fixes applied, and remaining manual actions.

## Standards Enforced

- **Labels**: `product`, `engineering`, `plan` must exist
- **Board Columns**: Backlog, To Do, In Progress, In Review, Done
- **Board Lifecycle**: One board per milestone
- **Branch Protection**: PR reviews, stale review dismissal, status checks, force push restriction, deletion restriction
