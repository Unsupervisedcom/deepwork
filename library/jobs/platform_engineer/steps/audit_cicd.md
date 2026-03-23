# Audit CI/CD Pipeline

## Objective

Analyze all CI/CD pipeline configurations in the repository, measure their performance characteristics, assess compliance with CI/CD conventions 18-23, and identify bottlenecks that are slowing down the development feedback loop.

## Task

Find and read every CI/CD configuration file in the repository, assess each pipeline's structure, caching strategy, parallelism, security posture, and estimated run time, and produce a comprehensive audit report that will drive the `cicd_recommendations` step.

**Important**: This step is analysis-only. Do not modify any CI/CD configuration files. The purpose is to understand the current state and identify opportunities for improvement.

### Process

1. **Read context.md for CI provider detection**
   - Read `context.md` from the `gather_context` step.
   - Identify which CI/CD provider(s) are in use (GitHub Actions, Forgejo Actions, GitLab CI, CircleCI, Jenkins, etc.).
   - Note the repository hosting platform, as this constrains which CI features are available.
   - Check for any CI-adjacent tools mentioned: Docker, Nix, Make, Bazel, Turborepo, Nx, etc.

2. **Find and read all CI configuration files**

   Search for CI config files in order of prevalence. Read every file found:

   | CI Provider | Config Locations |
   |-------------|-----------------|
   | **GitHub Actions** | `.github/workflows/*.yml`, `.github/workflows/*.yaml` |
   | **Forgejo Actions** | `.forgejo/workflows/*.yml`, `.forgejo/workflows/*.yaml` |
   | **GitLab CI** | `.gitlab-ci.yml`, `.gitlab-ci/*.yml` (includes) |
   | **CircleCI** | `.circleci/config.yml` |
   | **Jenkins** | `Jenkinsfile`, `Jenkinsfile.*` |
   | **Travis CI** | `.travis.yml` |
   | **Azure DevOps** | `azure-pipelines.yml`, `.azure-pipelines/*.yml` |

   Also search for supporting build configuration files that pipelines reference:
   - `Makefile`, `Taskfile.yml`, `justfile` -- task runners
   - `Dockerfile`, `Dockerfile.*` -- container builds
   - `docker-compose.yml`, `docker-compose.*.yml` -- service composition
   - `flake.nix` -- Nix-based builds
   - `turbo.json`, `nx.json` -- monorepo build orchestration
   - `.tool-versions`, `.node-version`, `.python-version` -- version pinning

3. **Analyze each pipeline**

   For every pipeline/workflow file found, document the following:

   **a. Pipeline overview:**
   - Trigger events (push, pull_request, schedule, manual)
   - Branch filters (which branches trigger this pipeline)
   - Path filters (does it only run when certain files change)
   - Concurrency settings (does it cancel redundant runs)

   **b. Job structure:**
   - Number of jobs
   - Job dependency graph (which jobs depend on which)
   - Which jobs run in parallel vs. sequentially
   - Runner/executor type and size (e.g., `ubuntu-latest`, self-hosted, medium/large)

   **c. Step-by-step analysis for each job:**
   - Checkout step (shallow vs. full clone)
   - Dependency installation method and duration estimate
   - Build steps and their estimated duration
   - Test steps (unit, integration, e2e) and their estimated duration
   - Artifact upload/download steps
   - Deploy steps (if present)
   - Post-run cleanup

   **d. Caching strategy:**
   - Is dependency caching configured? (npm cache, pip cache, cargo cache, nix store cache)
   - Is build caching configured? (Docker layer cache, build output cache, Turborepo cache)
   - Cache key strategy (hash of lockfile? branch-based? fixed key?)
   - Cache restore strategy (exact match? prefix match? fallback keys?)
   - Estimated cache hit rate (examine key strategy for staleness risk)

   **e. Estimated total run time:**
   - Sum the estimated duration of the critical path (longest sequential chain of jobs)
   - Note which jobs are on the critical path vs. off it
   - Flag any pipeline where the critical path exceeds 10 minutes (convention 18)

4. **Check against CI/CD conventions 18-23**

   Evaluate each pipeline against the six CI/CD conventions:

   | Convention | Requirement | How to Check |
   |-----------|-------------|--------------|
   | **18** | PR pipelines SHOULD complete in under 10 minutes | Estimate critical path duration; check recent run times if available |
   | **19** | Build caching MUST be enabled where supported | Look for `actions/cache`, Docker layer caching, Nix binary cache, Turborepo remote cache |
   | **20** | Dependency installation SHOULD be cached | Check for cached dependency directories (node_modules, .pip, target/, .cargo) |
   | **21** | Pipeline configs SHOULD be linted/validated | Look for `actionlint`, `yamllint`, `gitlab-ci-lint`, or equivalent in the pipeline itself |
   | **22** | No hardcoded secrets in CI configs | Grep for patterns: API keys, tokens, passwords, base64-encoded strings, AWS access keys |
   | **23** | Test stages SHOULD run in parallel | Check if independent test suites (unit, integration, e2e) run as separate parallel jobs |

   For each convention, record:
   - **Pass**: Convention is fully satisfied
   - **Partial**: Some but not all pipelines satisfy the convention
   - **Fail**: Convention is not satisfied
   - **N/A**: Convention does not apply (e.g., no build step, so build caching is irrelevant)

5. **Gather actual metrics (if available)**

   Attempt to gather real performance data from the CI provider:

   **GitHub Actions:**
   ```bash
   # List recent workflow runs with timing
   gh run list --limit 20 --json databaseId,name,status,conclusion,createdAt,updatedAt

   # Get detailed timing for a specific run
   gh run view <run-id> --json jobs
   ```

   **Forgejo Actions:**
   ```bash
   # Use the Forgejo API to get action runs
   tea api /repos/{owner}/{repo}/actions/runs
   ```

   If metrics are available, compute:
   - Average run time for PR pipelines (last 20 runs)
   - P90 run time for PR pipelines
   - Failure rate (failed / total runs)
   - Most common failure reasons
   - Slowest job in the pipeline

   If metrics are not available (e.g., new repository, no API access), note this limitation and rely on estimates from the configuration analysis.

6. **Identify bottlenecks**

   Based on the analysis, identify the top bottlenecks slowing down CI/CD:

   - **Slow dependency installation**: No caching, or cache misses due to poor key strategy
   - **Sequential jobs that could be parallel**: Independent test suites running one after another
   - **Large Docker images**: Base images that take minutes to pull, no layer caching
   - **Redundant work**: Full builds triggered on every push regardless of which files changed
   - **Missing concurrency controls**: Multiple runs queued for the same branch without cancellation
   - **Oversized runners**: Using large runners when small ones would suffice, or vice versa
   - **Unnecessary full checkouts**: Deep git history fetched when shallow clone would work
   - **No path filtering**: Pipelines run for all changes even when only docs or unrelated files change
   - **Monorepo without selective builds**: All packages rebuild when only one changed

7. **Security assessment**

   Review CI/CD security posture:
   - Are secrets managed through the CI provider's secret store?
   - Are pipeline permissions scoped (e.g., `permissions:` block in GitHub Actions)?
   - Are third-party actions pinned to commit SHAs (not mutable tags)?
   - Are there any write permissions that could be reduced to read-only?
   - Is there a `pull_request_target` trigger without adequate security controls?

## Output Format

### cicd_audit.md

A structured audit report that provides the evidence base for the `cicd_recommendations` step.

**Structure**:
```markdown
# CI/CD Pipeline Audit

## Overview
- **Repository**: [repo name]
- **CI Provider(s)**: [provider(s)]
- **Date**: [audit date]
- **Method**: [API metrics + config analysis / config analysis only]

## Pipeline Inventory

| # | Pipeline/Workflow | File | Trigger | Jobs | Est. Duration | Critical Path |
|---|------------------|------|---------|------|---------------|---------------|
| 1 | [name]           | [path] | [triggers] | [count] | [minutes] | [job chain] |
| 2 | ...              | ...  | ...     | ...  | ...           | ...           |

## Detailed Pipeline Analysis

### [Pipeline Name] (`[file path]`)

**Triggers**: [push, pull_request, schedule, etc.]
**Branch Filters**: [branches]
**Path Filters**: [paths or "none"]
**Concurrency**: [cancel-in-progress settings or "none"]

#### Job Dependency Graph
```
[job1] --> [job2] --> [job4]
              \--> [job3] --/
```

#### Job Details

| Job | Runner | Steps | Est. Duration | Caching | Notes |
|-----|--------|-------|---------------|---------|-------|
| [name] | [runner] | [count] | [minutes] | [Y/N] | [notes] |

#### Caching Analysis
- **Dependency Cache**: [configured? key strategy? estimated hit rate?]
- **Build Cache**: [configured? type? key strategy?]
- **Docker Cache**: [layer caching? registry cache?]

[Repeat for each pipeline]

## Convention Compliance

| # | Convention | Requirement | Status | Evidence |
|---|-----------|-------------|--------|----------|
| 18 | PR pipeline < 10 min | SHOULD | [Pass/Partial/Fail] | [evidence] |
| 19 | Build caching enabled | MUST | [Pass/Partial/Fail] | [evidence] |
| 20 | Dependency caching | SHOULD | [Pass/Partial/Fail] | [evidence] |
| 21 | Pipeline linting | SHOULD | [Pass/Partial/Fail] | [evidence] |
| 22 | No hardcoded secrets | MUST | [Pass/Partial/Fail] | [evidence] |
| 23 | Parallel test stages | SHOULD | [Pass/Partial/Fail] | [evidence] |

## Performance Analysis

### Actual Metrics (if available)
| Metric | Value |
|--------|-------|
| Average PR pipeline duration | [minutes] |
| P90 PR pipeline duration | [minutes] |
| Pipeline failure rate | [percentage] |
| Most common failure reason | [reason] |
| Slowest job | [job name, duration] |

### Estimated Metrics (from config analysis)
| Pipeline | Critical Path Duration | Parallelizable Savings |
|----------|----------------------|----------------------|
| [name]   | [minutes]            | [minutes]            |

## Bottleneck Identification

| # | Bottleneck | Pipeline(s) Affected | Impact | Evidence |
|---|-----------|---------------------|--------|----------|
| 1 | [description] | [pipelines] | [time/cost impact] | [evidence] |

## Security Assessment

| Check | Status | Details |
|-------|--------|---------|
| Secrets in provider store | [Pass/Fail] | [details] |
| Permissions scoped | [Pass/Fail] | [details] |
| Actions pinned to SHA | [Pass/Fail] | [details] |
| No excessive write permissions | [Pass/Fail] | [details] |
| pull_request_target safety | [Pass/N/A] | [details] |

## Limitations
- [Any CI config files that could not be fully analyzed]
- [Metrics that were unavailable]
- [Assumptions made during estimation]
```

## Quality Criteria

- All CI/CD pipeline configurations in the repository are identified and analyzed -- none are missed
- Each pipeline has a documented trigger, job structure, and estimated duration
- Caching strategy is assessed for both dependencies and build artifacts with specific key strategy details
- Convention compliance (18-23) is checked with a clear Pass/Partial/Fail status and supporting evidence for each
- Actual build metrics are gathered from the CI API when accessible, with specific numbers (averages, p90, failure rate)
- Bottlenecks are specific and evidence-based -- each one identifies the pipeline, the job, and the estimated time impact
- Security assessment covers secrets management, permission scoping, and action pinning
- Estimated durations are based on observable factors (step count, dependency size, test suite size), not guesses
- The audit clearly distinguishes between MUST conventions (19, 22) and SHOULD conventions (18, 20, 21, 23)

## Context

This step is the first of two in the `cicd_optimization` workflow. It produces the evidence that drives the `cicd_recommendations` step, where specific optimization proposals are made with expected impact estimates. A thorough audit here ensures that recommendations are grounded in data rather than assumptions.

CI/CD pipeline performance directly affects developer productivity. Slow pipelines discourage frequent commits, delay code review, and reduce the number of iterations a team can make in a day. The 10-minute target for PR pipelines (convention 18) is based on research showing that developers context-switch to other tasks when feedback takes longer than 10 minutes, leading to reduced throughput and more merge conflicts.

The security assessment is included because CI/CD pipelines are a common attack vector -- leaked secrets, overly permissive actions, and unpinned third-party code can lead to supply chain compromises. Convention 22 (no hardcoded secrets) is a MUST requirement precisely because of this risk.
