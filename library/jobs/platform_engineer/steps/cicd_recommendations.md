# CI/CD Recommendations

## Objective

Produce a prioritized CI/CD optimization plan with specific, implementable recommendations that address the bottlenecks identified in the audit. Each recommendation includes estimated impact, implementation effort, and ready-to-use configuration snippets for the detected CI provider.

## Task

Read the `cicd_audit.md` produced by the `audit_cicd` step and transform each identified bottleneck and convention failure into a concrete optimization with an implementation plan. The output should be actionable enough that someone could implement each recommendation without additional research.

**Important**: Recommendations must be specific to the CI provider and tooling detected in the audit. Do not provide generic advice -- every recommendation must include configuration snippets that are ready to adapt and apply.

### Process

1. **Read the audit report**
   - Read `cicd_audit.md` from the previous step.
   - Extract all identified bottlenecks from the Bottleneck Identification table.
   - Extract all convention compliance failures (Partial or Fail) from the Convention Compliance table.
   - Extract security assessment failures.
   - Note the CI provider(s), runner types, and tooling in use -- all recommendations must target these.

2. **Map bottlenecks to optimizations**

   For each bottleneck identified in the audit, determine the appropriate optimization. Common mappings:

   | Bottleneck | Optimization Category |
   |-----------|----------------------|
   | Slow dependency installation | Dependency caching with lockfile-based cache keys |
   | No build caching | Configure build cache (Docker layer cache, Turborepo, Nx, Nix binary cache) |
   | Sequential test jobs | Split into parallel jobs with matrix strategy or separate job definitions |
   | Large Docker images | Multi-stage builds, smaller base images (Alpine, distroless, Chainguard) |
   | No path filtering | Add path-based trigger filters to skip irrelevant pipelines |
   | Redundant builds on same branch | Enable concurrency controls with cancel-in-progress |
   | Full git clone | Switch to shallow clone with `fetch-depth: 1` (or appropriate depth) |
   | No pipeline linting | Add actionlint/yamllint step to the CI pipeline |
   | Hardcoded secrets | Migrate to CI provider secret store, rotate compromised values |
   | Unpinned third-party actions | Pin all actions to full commit SHA |
   | Missing concurrency cancellation | Add concurrency group with cancel-in-progress |
   | Monorepo without selective builds | Configure change detection (paths filter, Nx affected, Turborepo filter) |
   | Oversized runners | Right-size runner labels to match actual resource needs |

3. **Estimate impact for each recommendation**

   For each proposed optimization, estimate:

   **Time savings:**
   - Calculate the expected reduction in pipeline duration (in minutes).
   - Base estimates on the audit's measured or estimated durations.
   - For caching: typical first-hit penalty is full install time; subsequent runs save 60-90% of that time.
   - For parallelism: savings = (sequential duration - longest parallel job duration).
   - For path filtering: savings = (full pipeline duration * percentage of runs that would be skipped).

   **Cost savings (if runner costs are known):**
   - GitHub-hosted runners: ~$0.008/min (Linux), ~$0.016/min (Windows), ~$0.08/min (macOS).
   - Self-hosted: estimate based on infrastructure costs.
   - Calculate: (time saved per run) * (runs per month) * (cost per minute).

   **Implementation effort:**
   - **Low**: Configuration-only change, no code modifications, low risk of breakage. Can be done in under 1 hour. Examples: adding cache steps, enabling concurrency controls, adding path filters.
   - **Medium**: Requires restructuring pipeline jobs, testing new configurations, or modifying build scripts. Takes 2-4 hours. Examples: splitting into parallel jobs, implementing multi-stage Docker builds, adding pipeline linting.
   - **High**: Requires significant refactoring, new tooling setup, or coordination across teams. Takes 1+ days. Examples: migrating to a different CI provider, implementing monorepo build orchestration, setting up self-hosted runners.

4. **Prioritize by impact-to-effort ratio**

   Score each recommendation:
   - **Impact score**: High (saves > 5 min per run or fixes MUST convention), Medium (saves 2-5 min or fixes SHOULD convention), Low (saves < 2 min or cosmetic improvement).
   - **Effort score**: Low (< 1 hour), Medium (2-4 hours), High (1+ days).
   - **Priority**: Rank by impact/effort ratio. High-impact + low-effort items come first. Low-impact + high-effort items come last.

   Priority tiers:
   - **P0 (Do Now)**: High impact, low effort -- these are quick wins
   - **P1 (Do Soon)**: High impact, medium effort -- or medium impact, low effort
   - **P2 (Plan)**: Medium impact, medium effort -- or high impact, high effort
   - **P3 (Backlog)**: Low impact regardless of effort

5. **Produce configuration snippets**

   For each recommendation, provide ready-to-use configuration snippets specific to the detected CI provider. Snippets must be complete enough to copy-paste with minimal adaptation.

   **GitHub Actions examples:**

   *Dependency caching (Node.js):*
   ```yaml
   - name: Cache node_modules
     uses: actions/cache@v4
     with:
       path: node_modules
       key: node-modules-${{ hashFiles('pnpm-lock.yaml') }}
       restore-keys: |
         node-modules-
   ```

   *Parallel test jobs:*
   ```yaml
   jobs:
     unit-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - run: npm run test:unit
     integration-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - run: npm run test:integration
     e2e-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - run: npm run test:e2e
   ```

   *Concurrency controls:*
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

   *Path filtering:*
   ```yaml
   on:
     pull_request:
       paths:
         - 'src/**'
         - 'tests/**'
         - 'package.json'
         - 'pnpm-lock.yaml'
   ```

   *Action pinning:*
   ```yaml
   # Instead of:
   - uses: actions/checkout@v4
   # Use:
   - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
   ```

   **Forgejo Actions examples:**
   - Forgejo Actions are largely compatible with GitHub Actions syntax, but note differences in available runners and cache backend.
   - Forgejo-specific cache action may differ -- check the instance's available actions.

   **GitLab CI examples:**

   *Dependency caching:*
   ```yaml
   cache:
     key:
       files:
         - package-lock.json
     paths:
       - node_modules/
     policy: pull-push
   ```

   *Parallel jobs:*
   ```yaml
   unit-tests:
     stage: test
     script: npm run test:unit
   integration-tests:
     stage: test
     script: npm run test:integration
   ```

   Provide snippets for the actual CI provider detected in the audit. Do not provide snippets for providers that are not in use.

6. **Handle convention compliance failures**

   For each convention that failed or was partial in the audit:

   - **Convention 19 (build caching) -- MUST**: If failing, this is automatically P0 priority. Provide the specific cache configuration for the build tool in use.
   - **Convention 22 (no hardcoded secrets) -- MUST**: If failing, this is P0 priority. Identify the specific secrets, recommend immediate rotation, and provide the migration steps to the CI provider's secret store.
   - **Conventions 18, 20, 21, 23 -- SHOULD**: Priority depends on impact assessment. Include in the recommendation table with appropriate priority.

7. **Identify quick wins vs. larger projects**

   Separate recommendations into two categories in the output:
   - **Quick Wins**: Can be implemented in a single PR, low risk, immediate benefit. These should be implementable today.
   - **Projects**: Require planning, testing, or coordination. These need a tracking issue.

## Output Format

### optimization_plan.md

A prioritized optimization plan ready to drive implementation.

**Structure**:
```markdown
# CI/CD Optimization Plan

## Summary
- **Repository**: [repo name]
- **CI Provider**: [provider]
- **Date**: [date]
- **Total Recommendations**: [count]
- **Estimated Total Time Savings**: [minutes per run]
- **Estimated Monthly Cost Savings**: [amount, if calculable]

## Priority Matrix

| # | Recommendation | Impact | Effort | Priority | Est. Time Saved | Convention |
|---|---------------|--------|--------|----------|----------------|------------|
| 1 | [title]       | [H/M/L]| [L/M/H]| [P0-P3] | [min/run]      | [#, if any]|
| 2 | ...           | ...    | ...    | ...      | ...            | ...        |

## Quick Wins (implement today)

### 1. [Recommendation Title]

**Bottleneck**: [what problem this solves, from the audit]
**Impact**: [High/Medium/Low] -- saves ~[N] minutes per run
**Effort**: Low -- [estimated time to implement]
**Convention**: [convention number, if applicable]

**Current State**:
[Description of what the pipeline does now, referencing specific file and line numbers from the audit]

**Recommended Change**:
[Description of what to change]

**Implementation**:
```yaml
[Ready-to-use configuration snippet]
```

**Verification**:
[How to verify the optimization is working after implementation]

---

[Repeat for each quick win]

## Projects (require planning)

### [N]. [Recommendation Title]

**Bottleneck**: [what problem this solves]
**Impact**: [High/Medium/Low] -- saves ~[N] minutes per run
**Effort**: [Medium/High] -- [estimated time to implement]
**Convention**: [convention number, if applicable]

**Current State**:
[Description of current pipeline behavior]

**Recommended Change**:
[Description of the change, broken into sub-steps if needed]

**Implementation Steps**:
1. [Step 1 with specific details]
2. [Step 2 with specific details]
3. [Step 3 with specific details]

**Configuration**:
```yaml
[Configuration snippet, may be larger or require multiple file changes]
```

**Risks and Mitigations**:
- [Risk 1]: [Mitigation]
- [Risk 2]: [Mitigation]

**Verification**:
[How to verify after implementation]

**Suggested Tracking Issue Title**: `[conventional commit format title for tracking issue]`

---

[Repeat for each project]

## Security Fixes

[If the audit identified security issues, list them separately with immediate remediation steps]

### [N]. [Security Fix Title]

**Risk**: [what could go wrong if not fixed]
**Remediation**:
1. [Step 1]
2. [Step 2]

**Configuration**:
```yaml
[fix snippet]
```

## Implementation Roadmap

### Week 1: Quick Wins
- [ ] [Recommendation 1]
- [ ] [Recommendation 2]

### Week 2-3: Medium Effort
- [ ] [Recommendation N]

### Month 2+: Large Projects
- [ ] [Recommendation N]

## Expected Outcome

After implementing all recommendations:
- **PR pipeline duration**: [current estimate] -> [target estimate]
- **Convention compliance**: [current score] -> [target score]
- **Monthly CI cost**: [current estimate] -> [target estimate, if applicable]
```

## Quality Criteria

- Every bottleneck from `cicd_audit.md` has a corresponding recommendation -- nothing is left unaddressed
- Every recommendation includes a specific, ready-to-use configuration snippet for the detected CI provider
- Impact estimates are grounded in the audit's measurements or estimates, not arbitrary numbers
- Effort estimates distinguish between configuration-only changes (Low) and structural changes (Medium/High)
- Recommendations are prioritized by impact-to-effort ratio with clear P0/P1/P2/P3 tiers
- MUST convention failures (19, 22) are automatically P0 priority
- Security issues are addressed in a dedicated section with immediate remediation steps
- Quick wins are separated from larger projects so the team knows what to implement today
- Each recommendation references the specific pipeline file and bottleneck it addresses
- The implementation roadmap provides a realistic timeline for completing all recommendations
- Verification steps are provided so the team can confirm each optimization is working

## Context

This is the second step in the `cicd_optimization` workflow. It transforms the audit findings into an actionable plan. The key principle is that every recommendation must be specific enough to implement without additional research -- vague suggestions like "add caching" are not useful; the exact cache configuration with proper keys and paths is what engineers need.

The priority matrix ensures that the team works on the highest-value improvements first. Quick wins (P0) often deliver 80% of the total time savings with 20% of the effort. Identifying and implementing these first builds momentum and demonstrates the value of the optimization work, making it easier to get buy-in for the larger projects.

CI/CD pipelines are living infrastructure -- they need periodic review and optimization just like production services. This optimization plan should be revisited quarterly or whenever the development workflow changes significantly (new test suites, new build targets, new deployment environments).
