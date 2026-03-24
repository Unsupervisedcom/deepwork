# GitHub Actions Workflows

This directory contains CI/CD workflows for the DeepWork project. We use GitHub's merge queue for efficient testing.

## Workflow Overview

| Workflow | File | Purpose |
|----------|------|---------|
| **Validate** | `validate.yml` | Linting (ruff), type checking (mypy), and unit tests (pytest) |
| **Integration Tests** | `claude-code-test.yml` | Skill generation and e2e tests |
| **CLA Assistant** | `cla.yml` | Contributor License Agreement verification |
| **Copilot Setup** | `copilot-setup-steps.yml` | Environment setup for GitHub Copilot agents |
| **Prepare Release** | `prepare-release.yml` | Version bumping, changelog, release PR or pre-release tagging |
| **Publish Release** | `publish-release.yml` | Creates GitHub Release when a release PR is merged |
| **Release** | `release.yml` | PyPI publishing |

## Merge Queue Strategy

All workflows explicitly target the `main` branch for both `pull_request` and `merge_group` triggers to ensure proper execution in the merge queue.

We use a skip pattern so the same required checks pass in both PR and merge queue contexts:

| Workflow | On PRs | In Merge Queue | Manual Trigger |
|----------|--------|----------------|----------------|
| **Validate** | Runs | Runs | Runs |
| **Integration Tests** | Skipped (passes) | Runs | Runs |
| **E2E Tests** | Skipped unless workflow file changed | Runs | Runs |
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
- `Validate / lint`
- `Validate / test`
- `Claude Code Integration Test / validate-generation` (for merge queue)
- `Claude Code Integration Test / claude-code-e2e` (for merge queue)
- `CLA Assistant / cla-check` (for both PRs and merge queue)

All checks will pass in both PR and merge queue contexts (either by running or by being skipped).

## Workflow Details

### validate.yml
- **Triggers**: `pull_request` (main), `merge_group` (main), `workflow_dispatch`
- **Jobs**:
  - `lint`: Runs ruff format/lint checks and mypy type checking
  - `test`: Runs pytest unit tests
- Runs on every PR, in merge queue, and can be manually triggered

### claude-code-test.yml
- **Triggers**: `pull_request` (main), `merge_group` (main), `workflow_dispatch`
- **Jobs**:
  - `validate-generation`: Tests skill generation from fixtures (no API key needed)
  - `claude-code-e2e`: Full end-to-end test with Claude Code CLI (requires `ANTHROPIC_API_KEY`)
- `validate-generation` skips on PRs, runs in merge queue and manual dispatch
- `claude-code-e2e` skips on PRs unless the workflow file itself is changed (so CI fixes can be iterated in PRs)

### cla.yml
- **Triggers**: `pull_request_target`, `issue_comment`, `merge_group` (main), `workflow_dispatch`
- **Jobs**:
  - `cla-check`: Single job that verifies contributors have signed the CLA on PRs, and auto-passes in merge queue/manual dispatch
- CLA verification runs on PRs; in merge queue and manual dispatch, the step is skipped (check passes automatically)

### copilot-setup-steps.yml
- **Triggers**: `workflow_call`, `workflow_dispatch`, `pull_request` (only when this file changes)
- **Jobs**: Sets up the Python/uv development environment for GitHub Copilot agents

### prepare-release.yml
- **Triggers**: `workflow_dispatch` with inputs: `version`, `release_type` (stable/alpha/beta/rc), `prerelease_number`, `ref`
- **Stable releases**: Creates a `release/<version>` branch, bumps versions in pyproject.toml/plugin.json/marketplace.json, updates CHANGELOG.md, runs `uv sync`, and opens a PR with the `release` label
- **Pre-releases**: Checks out the specified `ref` branch, bumps versions (PEP 440 for PyPI, semver for plugin.json), pins `.mcp.json` to the pre-release PyPI package, force-pushes to the `pre-release` branch, tags, and creates a GitHub Release directly (no PR)

### publish-release.yml
- **Triggers**: `pull_request` (closed) — only when merged with the `release` label
- **Jobs**: Extracts version from PR title, creates a git tag, extracts release notes from CHANGELOG.md, and creates a GitHub Release
- Uses `RELEASE_TOKEN` (PAT) so the created release triggers `release.yml`

### prepare-release.yml
- **Triggers**: `workflow_dispatch` with inputs: `version`, `release_type` (stable/alpha/beta/rc), `prerelease_number`, `ref`
- **Stable releases**: Creates a `release/<version>` branch, bumps versions in pyproject.toml/plugin.json/marketplace.json, updates CHANGELOG.md, runs `uv sync`, and opens a PR with the `release` label
- **Pre-releases**: Checks out the specified `ref` branch, bumps versions (PEP 440 for PyPI, semver for plugin.json), pins `.mcp.json` to the pre-release PyPI package, force-pushes to the `pre-release` branch, tags, and creates a GitHub Release directly (no PR)

### publish-release.yml
- **Triggers**: `pull_request` (closed) — only when merged with the `release` label
- **Jobs**: Extracts version from PR title, creates a git tag, extracts release notes from CHANGELOG.md, and creates a GitHub Release
- Uses `RELEASE_TOKEN` (PAT) so the created release triggers `release.yml`

### release.yml
- **Triggers**: `release` (published), plus dry-run build on PRs that touch this file
- **Jobs**:
  - `build`: Runs tests and builds the package
  - `publish`: Publishes to PyPI via OIDC trusted publishing
