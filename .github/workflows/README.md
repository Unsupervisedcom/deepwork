# GitHub Actions Workflows

This directory contains CI/CD workflows for the DeepWork project. We use GitHub's merge queue for efficient testing.

## Workflow Overview

| Workflow | File | Purpose |
|----------|------|---------|
| **Validate** | `validate.yml` | Linting (ruff) and unit tests |
| **Integration Tests** | `claude-code-test.yml` | Command generation and e2e tests |
| **CLA Assistant** | `cla.yml` | Contributor License Agreement verification |
| **Release** | `release.yml` | PyPI publishing on tags |

## Merge Queue Strategy

We use a skip pattern so the same required checks pass in both PR and merge queue contexts:

| Workflow | On PRs | In Merge Queue |
|----------|--------|----------------|
| **Validate** | Runs | Runs |
| **Integration Tests** | Skipped (passes) | Runs |
| **E2E Tests** | Skipped (passes) | Runs |
| **CLA Check** | Runs | Skipped (passes) |

### How It Works

Jobs/steps use `if: github.event_name == 'merge_group'` conditions to control execution:

```yaml
# Job that only runs in merge queue (skipped on PRs)
jobs:
  expensive-tests:
    if: github.event_name == 'merge_group' || github.event_name == 'workflow_dispatch'
    ...

# Step that skips in merge queue (runs on PRs only)
steps:
  - name: CLA Check
    if: github.event_name != 'merge_group'
    ...
```

When a job/step is skipped due to an `if` condition, GitHub treats it as a successful check. This allows:

- **Fast PR feedback**: Only lint + unit tests run on every push
- **Thorough merge validation**: Expensive integration/e2e tests run in merge queue before merging
- **No duplicate CLA checks**: CLA is verified on PRs; no need to re-check in merge queue

### Required Checks Configuration

In GitHub branch protection rules, require these checks:
- `Validate / tests`
- `Claude Code Integration Test / validate-generation`
- `Claude Code Integration Test / claude-code-e2e`
- `CLA Assistant / cla-check`

All checks will pass in both PR and merge queue contexts (either by running or by being skipped).

## Workflow Details

### validate.yml
- **Triggers**: `pull_request`, `merge_group`
- **Jobs**: `tests` - runs ruff format/lint checks and pytest unit tests
- Runs on every PR and in merge queue

### claude-code-test.yml
- **Triggers**: `pull_request`, `merge_group`, `workflow_dispatch`
- **Jobs**:
  - `validate-generation`: Tests command generation from fixtures (no API key needed)
  - `claude-code-e2e`: Full end-to-end test with Claude Code CLI (requires `ANTHROPIC_API_KEY`)
- Both jobs skip on PRs, run in merge queue and manual dispatch

### cla.yml
- **Triggers**: `pull_request_target`, `issue_comment`, `merge_group`
- **Jobs**: `cla-check` - verifies contributors have signed the CLA
- Runs on PRs, skips in merge queue (CLA already verified)

### release.yml
- **Triggers**: Tags matching `v*`
- **Jobs**: Builds and publishes to PyPI
