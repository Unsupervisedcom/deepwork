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

All workflows explicitly target the `main` branch for both `pull_request` and `merge_group` triggers to ensure proper execution in the merge queue.

We use a skip pattern so the same required checks pass in both PR and merge queue contexts:

| Workflow | On PRs | In Merge Queue | Manual Trigger |
|----------|--------|----------------|----------------|
| **Validate** | Runs | Runs | Runs |
| **Integration Tests** | Skipped (passes) | Runs | Runs |
| **E2E Tests** | Skipped (passes) | Runs | Runs |
| **CLA Check** | Runs | Skipped (passes) | Skipped (passes) |

### How It Works

All workflows specify explicit branch targeting:

```yaml
on:
  pull_request:
    branches: [main]
  merge_group:
    branches: [main]
  workflow_dispatch:  # Enables manual triggering for testing
```

Jobs/steps use `if: github.event_name == 'merge_group'` conditions to control execution:

```yaml
# Job that only runs in merge queue and manual dispatch (skipped on PRs)
jobs:
  expensive-tests:
    if: github.event_name == 'merge_group' || github.event_name == 'workflow_dispatch'
    ...

# Job that skips in merge queue and manual dispatch (runs on PRs only)
jobs:
  cla-check:
    if: github.event_name != 'merge_group' && github.event_name != 'workflow_dispatch'
    ...
```

When a job is skipped due to an `if` condition, GitHub treats it as a successful check. This allows:

- **Fast PR feedback**: Only lint + unit tests run on every push
- **Thorough merge validation**: Expensive integration/e2e tests run in merge queue before merging
- **No duplicate CLA checks**: CLA is verified on PRs; no need to re-check in merge queue

### Required Checks Configuration

In GitHub branch protection rules, require these checks:
- `Validate / tests`
- `Claude Code Integration Test / pr-check` (for PRs)
- `Claude Code Integration Test / validate-generation` (for merge queue)
- `Claude Code Integration Test / claude-code-e2e` (for merge queue)
- `CLA Assistant / merge-queue-pass` (for merge queue)
- `CLA Assistant / cla-check` (for PRs)

All checks will pass in both PR and merge queue contexts (either by running or by being skipped).

**Note**: The explicit branch targeting in `merge_group` triggers is critical for workflows to run properly in the merge queue. Without this, GitHub may not trigger the workflows and they will remain in "expected" state.

## Workflow Details

### validate.yml
- **Triggers**: `pull_request` (main), `merge_group` (main), `workflow_dispatch`
- **Jobs**: `tests` - runs ruff format/lint checks and pytest unit tests
- Runs on every PR, in merge queue, and can be manually triggered

### claude-code-test.yml
- **Triggers**: `pull_request` (main), `merge_group` (main), `workflow_dispatch`
- **Jobs**:
  - `pr-check`: Runs on PRs only, always passes (lightweight check)
  - `validate-generation`: Tests command generation from fixtures (no API key needed)
  - `claude-code-e2e`: Full end-to-end test with Claude Code CLI (requires `ANTHROPIC_API_KEY`)
- `validate-generation` and `claude-code-e2e` skip on PRs, run in merge queue and manual dispatch

### cla.yml
- **Triggers**: `pull_request_target`, `issue_comment`, `merge_group` (main), `workflow_dispatch`
- **Jobs**: 
  - `merge-queue-pass`: Runs on merge queue and manual dispatch, always passes
  - `cla-check`: Verifies contributors have signed the CLA
- `cla-check` runs on PRs, skips in merge queue and manual dispatch (CLA already verified)

### release.yml
- **Triggers**: `release` (published)
- **Jobs**: Builds and publishes to PyPI
