# Scan Vulnerabilities

## Objective

Run security vulnerability scans against the project's dependencies and container images, assess the severity and exploitability of findings, and produce a prioritized remediation plan. The output helps the user understand their current security posture and gives them a clear action list for addressing vulnerabilities.

## Task

Determine the appropriate scanning tools for the project's stack, execute scans, analyze results, check compliance with security conventions 30-34, and produce a comprehensive vulnerability report with prioritized remediation actions.

### Process

#### 1. Read Context and Determine Stack

Read `context.md` to identify:
- Programming languages and package managers in use (npm, pnpm, yarn, pip, uv, cargo, go, bundler)
- Whether containers are used (Dockerfiles, container images)
- Available security scanning tools (trivy, grype, pip-audit, cargo-audit, etc.)
- CI provider (to check for existing automated scanning workflows)
- Whether Dependabot, Renovate, or other dependency automation is configured

This determines which scanners to run and where to look for existing scan results.

#### 2. Check for Existing Vulnerability Management

Before running new scans, check what security infrastructure already exists:

**Dependency automation:**
- Check for Dependabot config: `.github/dependabot.yml`
- Check for Renovate config: `renovate.json`, `.renovaterc`, `.github/renovate.json`
- Check for existing Dependabot or Renovate PRs: `gh pr list --label dependabot --limit 5` or `gh pr list --label renovate --limit 5`
- Note which ecosystems are covered and the update frequency

**CI security scanning:**
- Check CI workflow files for security scan jobs (look for `npm audit`, `trivy`, `snyk`, `cargo audit`, etc.)
- Check for scheduled scan workflows (cron triggers)
- Note the scan frequency if configured

**GitHub Security Alerts:**
```bash
# Dependabot alerts (requires appropriate permissions)
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[].security_advisory.summary' 2>/dev/null

# Code scanning alerts
gh api repos/{owner}/{repo}/code-scanning/alerts --jq '.[].rule.description' 2>/dev/null

# Secret scanning alerts
gh api repos/{owner}/{repo}/secret-scanning/alerts --jq '.[].secret_type_display_name' 2>/dev/null
```

**Security policy:**
- Check for `SECURITY.md` or `docs/security.md`
- Note whether response timeframes are defined

#### 3. Run Vulnerability Scans

Execute the appropriate scanner(s) based on the detected stack. Run ALL applicable scanners — a project may use multiple languages or have both application dependencies and container images.

**JavaScript/TypeScript (npm/pnpm/yarn):**
```bash
# npm
npm audit --json 2>/dev/null || npm audit 2>/dev/null

# pnpm
pnpm audit --json 2>/dev/null || pnpm audit 2>/dev/null

# yarn (v1)
yarn audit --json 2>/dev/null || yarn audit 2>/dev/null

# yarn (v2+/berry)
yarn npm audit --json 2>/dev/null || yarn npm audit 2>/dev/null
```

**Python:**
```bash
# pip-audit (preferred — uses OSV database)
pip-audit --format json 2>/dev/null || pip-audit 2>/dev/null

# safety (uses Safety DB)
safety check --json 2>/dev/null || safety check 2>/dev/null

# If neither is available, check for known vulnerable packages
pip list --outdated --format json 2>/dev/null
```

**Rust:**
```bash
# cargo-audit (uses RustSec advisory database)
cargo audit --json 2>/dev/null || cargo audit 2>/dev/null
```

**Go:**
```bash
# govulncheck (official Go vulnerability checker)
govulncheck -json ./... 2>/dev/null || govulncheck ./... 2>/dev/null
```

**Ruby:**
```bash
# bundler-audit
bundle audit check --update 2>/dev/null || bundle audit 2>/dev/null
```

**Container images:**
```bash
# trivy (comprehensive scanner — preferred)
trivy image --format json <image-name> 2>/dev/null || trivy image <image-name> 2>/dev/null

# grype (alternative)
grype <image-name> --output json 2>/dev/null || grype <image-name> 2>/dev/null
```

Identify container image names from Dockerfiles (`FROM` directives), docker-compose files, or Kubernetes manifests. If a built image is available locally, scan it directly. If not, scan the base image from the Dockerfile.

**General filesystem scanning:**
```bash
# trivy filesystem scan (catches dependencies across multiple ecosystems)
trivy fs --format json . 2>/dev/null || trivy fs . 2>/dev/null
```

If a scanning tool is not available in the environment, note it as "not available" and recommend installing it. If the project uses Nix, suggest adding the scanner to the devshell. Do NOT mark the project as secure simply because no scanner was available.

If a scanner exits with an error unrelated to vulnerabilities (e.g., parse error, authentication failure, lockfile mismatch), note the error and move on to the next scanner. Do not let a broken scanner block the entire report.

#### 4. Analyze Each Vulnerability

For each vulnerability found by any scanner, assess the following:

**Severity classification:**
- **Critical**: CVSS 9.0-10.0, or remote code execution, or authentication bypass, or data exfiltration without authentication
- **High**: CVSS 7.0-8.9, or significant data exposure, or privilege escalation, or denial of service against critical services
- **Medium**: CVSS 4.0-6.9, or limited impact requiring specific conditions, or information disclosure of non-sensitive data
- **Low**: CVSS 0.1-3.9, or informational, or requires unlikely preconditions, or minimal impact

Use the severity provided by the scanner as the baseline, but adjust if the project context changes the effective risk.

**Exploitability in this project's context:**

Assess whether the vulnerability is actually exploitable given how the project uses the affected package:

- **Is the vulnerable code path reachable?**
  - A vulnerability in a transitive dependency may not be exploitable if the project never calls the affected function or API
  - Check whether the vulnerable functionality is imported or used in the codebase
  - A regex DoS vulnerability matters only if the affected regex processes untrusted input

- **Is the vulnerable functionality exposed to untrusted input?**
  - A deserialization vulnerability is critical if the service accepts user-supplied data for deserialization
  - The same vulnerability in an internal admin tool behind VPN and authentication is lower effective risk
  - A server-side vulnerability in a dev-only dependency (linter, test framework) is typically low risk

- **Does the deployment context mitigate the risk?**
  - Container isolation limits lateral movement from container escape vulnerabilities
  - Network policies may prevent exploitation of SSRF vulnerabilities
  - WAF rules may block known exploit patterns
  - Read-only file systems prevent path traversal write attacks

Mark exploitability as:
- **Yes**: The vulnerable code path is reachable and processes untrusted input
- **No**: The vulnerable code path is not reachable or the deployment context prevents exploitation
- **Unclear**: Cannot determine without deeper analysis — treat as potentially exploitable

**Fix availability:**
- Is there a patched version available? What specific version?
- Is the fix a patch version bump (low risk), minor version bump (moderate risk), or major version bump (potential breaking changes)?
- If no fix exists, is there a known workaround (e.g., configuration change, input validation)?
- Is the vulnerable dependency direct or transitive?
  - Direct: Update directly in the project's manifest
  - Transitive: May require updating the intermediate package, or using an override/resolution

**Deduplication:**
Multiple scanners may report the same vulnerability (e.g., both `npm audit` and `trivy fs` may flag the same CVE). Deduplicate findings where possible, noting which scanners detected each issue.

#### 5. Check Against Security Conventions

Assess the project's compliance with each security convention:

**Convention 30 — Scan frequency:**
- Are vulnerability scans run at least weekly on production dependencies?
- Evidence to check:
  - CI workflows with cron schedules that run security scans
  - Dependabot configuration with update schedule
  - Renovate configuration with schedule
- Status: pass (automated weekly+ scans exist) / fail (no automated scanning) / partial (scans exist but less frequently than weekly)

**Convention 31 — Response timeframes:**
- Does the organization have a defined policy for CVE response times?
- Check for `SECURITY.md` or equivalent policy documentation
- Are there existing Critical/High CVEs that have been open for an extended period?
  - Check Dependabot alerts age: `gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[].created_at'`
  - Old unaddressed alerts indicate poor response timeframes
- Status: pass (policy exists and is followed) / fail (no policy or old unaddressed critical CVEs) / partial (policy exists but adherence is unclear)

**Convention 32 — Base image currency:**
- If container images are used:
  - Read Dockerfiles for `FROM` directives
  - Is the base image pinned to a specific digest or version? (good for reproducibility)
  - Is the base image recent? Check tag date if possible
  - Is a minimal base image used? (distroless, Alpine, slim, scratch)
  - Are there multiple `FROM` stages? (multi-stage builds are good practice)
- Status: pass (recent, minimal base) / fail (outdated or bloated base) / partial (mixed) / N/A (no containers)

**Convention 33 — Automated updates:**
- Is Dependabot or Renovate configured?
  - Check `.github/dependabot.yml` for Dependabot
  - Check `renovate.json`, `.renovaterc`, or `.github/renovate.json` for Renovate
- What ecosystems are covered? (npm, pip, docker, github-actions, cargo, go, etc.)
- Are there ecosystems used by the project that are NOT covered by the automation?
- Are security updates prioritized? (Dependabot: `open-pull-requests-limit`, Renovate: `prPriority`)
- Status: pass (configured covering all ecosystems) / fail (not configured) / partial (configured but missing ecosystems)

**Convention 34 — Triage process:**
- Are scan results being actively triaged? Evidence:
  - Dependabot alerts have been dismissed with documented reasons
  - Security PRs are merged in a timely manner (check merge dates)
  - There is a documented triage process or cadence
  - Alert count is stable or decreasing (not piling up)
- Status: pass (evidence of active triage) / fail (alerts ignored or accumulating) / partial (some triage but inconsistent)

#### 6. Prioritize Remediation

Create a prioritized remediation plan using four tiers based on: severity multiplied by exploitability multiplied by fix availability.

**Tier 1 — Immediate (do now):**
- Critical/High severity AND exploitable in this project AND fix available
- These represent active risk that can be resolved immediately
- Include the exact update command

**Tier 2 — Soon (this sprint/week):**
- Critical/High severity with fix available but low/unclear exploitability
- Medium severity with high exploitability and fix available
- Still important but slightly lower urgency

**Tier 3 — Planned (this month):**
- Medium severity with fix available
- High severity with no fix (apply workaround, monitor for fix)
- Important but can be scheduled into normal work

**Tier 4 — Backlog (track and monitor):**
- Low severity vulnerabilities
- Vulnerabilities with no fix and no workaround
- Informational findings
- Monitor for fix releases; re-assess if a fix becomes available

For each remediation action, provide:
- The specific package(s) to update and the target version
- The exact command to run (e.g., `npm update lodash`, `cargo update -p serde`, `pip install package==X.Y.Z`)
- Whether the update is a patch/minor/major version bump
- Known breaking changes to watch for (check the package's changelog)
- Testing recommendations after the update

## Output Format

Write the report to `.deepwork/tmp/platform_engineer/vulnerability_scan/vulnerability_report.md`. Create parent directories if they do not exist.

```markdown
# Vulnerability Scan Report

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name>
**Scanners Used**: <list of scanners that were successfully run>
**Scanners Not Available**: <list of scanners that could not be run, with reason>

## Summary

| Severity | Count | Fix Available | No Fix |
|----------|-------|--------------|--------|
| Critical | X | X | X |
| High | X | X | X |
| Medium | X | X | X |
| Low | X | X | X |
| **Total** | **X** | **X** | **X** |

**Overall Risk Assessment**: <one paragraph summarizing the security posture — are there critical issues needing immediate attention, or is the project in reasonable shape? Include overall exploitability assessment.>

## Vulnerability Details

### Critical

| CVE / Advisory | Package | Current Version | Fix Version | Exploitable | Priority | Scanner |
|---------------|---------|----------------|-------------|-------------|----------|---------|
| <CVE-XXXX-XXXXX> | <package> | <version> | <version or "none"> | <yes/no/unclear> | <immediate/soon/planned/backlog> | <scanner> |

#### <CVE-XXXX-XXXXX>: <brief title>
- **Package**: <package name> (<direct / transitive dependency>)
- **Description**: <what the vulnerability allows — e.g., "Remote code execution via crafted input to X function">
- **CVSS Score**: <score> (<vector string if available>)
- **Exploitability in this project**: <detailed assessment — is the code path reachable? is untrusted input involved?>
- **Fix**: <"Upgrade to version X.Y.Z" or "No fix available — workaround: ...">
- **Breaking changes**: <known breaking changes in the fix version, or "none expected for patch bump">
- **Command**: `<exact command to fix>`

### High

| CVE / Advisory | Package | Current Version | Fix Version | Exploitable | Priority | Scanner |
|---------------|---------|----------------|-------------|-------------|----------|---------|
| ... | ... | ... | ... | ... | ... | ... |

*(Detail blocks for each High vulnerability, same format as Critical)*

### Medium

| CVE / Advisory | Package | Current Version | Fix Version | Exploitable | Priority | Scanner |
|---------------|---------|----------------|-------------|-------------|----------|---------|
| ... | ... | ... | ... | ... | ... | ... |

*(Summary table sufficient for Medium — add detail blocks only for notable or highly exploitable ones)*

### Low

| CVE / Advisory | Package | Current Version | Fix Version | Priority |
|---------------|---------|----------------|-------------|----------|
| ... | ... | ... | ... | ... |

*(Summary table only for Low severity)*

## Convention Compliance

| # | Convention | Status | Evidence / Notes |
|---|-----------|--------|-----------------|
| 30 | Weekly vulnerability scans | pass / fail / partial | <details — what scanning is configured, frequency> |
| 31 | CVE response timeframes | pass / fail / partial | <details — policy exists? old alerts?> |
| 32 | Base images current & minimal | pass / fail / partial / N/A | <details — which base image, how old, how large> |
| 33 | Automated dependency updates | pass / fail / partial | <details — Dependabot/Renovate config, ecosystem coverage> |
| 34 | Scan results triaged | pass / fail / partial | <details — evidence of active triage> |

## Remediation Plan

### Immediate (do now)

| # | Action | Packages | Command | Breaking Changes | Risk |
|---|--------|----------|---------|-----------------|------|
| 1 | <what to do> | <packages> | `<command>` | <yes/no — details> | <low/med/high> |
| ... | ... | ... | ... | ... | ... |

### Soon (this sprint)

| # | Action | Packages | Command | Breaking Changes | Risk |
|---|--------|----------|---------|-----------------|------|
| ... | ... | ... | ... | ... | ... |

### Planned (this month)

| # | Action | Packages | Command | Breaking Changes | Risk |
|---|--------|----------|---------|-----------------|------|
| ... | ... | ... | ... | ... | ... |

### Backlog (track and monitor)

| # | Vulnerability | Package | Status | Notes |
|---|--------------|---------|--------|-------|
| ... | ... | ... | <no fix available / monitoring> | <re-assess when fix is released> |

## Recommendations for Security Posture

<Bulleted list of recommendations to improve the overall security process:>
- <Set up automated scanning if not configured (convention 30)>
- <Configure Dependabot/Renovate for uncovered ecosystems (convention 33)>
- <Create a SECURITY.md with response timeframes (convention 31)>
- <Switch to minimal base images for containers (convention 32)>
- <Establish a regular triage cadence for scan results (convention 34)>
- <Add vulnerability scanning to CI pipeline for PR checks>
```

## Quality Criteria

- **Scans Executed**: Vulnerability scans were actually run (or existing scan results reviewed) for every applicable ecosystem in the project. If a scanner was not available, it is explicitly noted as "not available" with a recommendation to install it. The report does not claim "no vulnerabilities" simply because no scanner was run.
- **Severity Assessed**: Every vulnerability has a severity classification (Critical/High/Medium/Low) based on CVSS scores or scanner-provided severity. Critical and High vulnerabilities include detailed exploitability assessments specific to this project's context, not just generic descriptions.
- **Remediation Prioritized**: Remediation actions are organized into four priority tiers (Immediate/Soon/Planned/Backlog) based on severity, exploitability, and fix availability. Each action includes the exact command to run and the target version.
- **Convention Compliance Checked**: All five security conventions (30-34) are assessed with pass/fail/partial status and supporting evidence. Gaps are accompanied by specific recommendations for remediation.
- **Context-Aware Exploitability**: The exploitability assessment considers the project's actual usage of vulnerable packages, deployment context, and network exposure. A transitive dependency vulnerability in a code path never reached by the project is appropriately de-prioritized compared to a vulnerability in code that processes untrusted input.
- **No False Sense of Security**: If scanners could not be run, permissions were insufficient, or scan coverage was incomplete, the report clearly states these limitations. An incomplete scan is reported as incomplete, never as "clean."

## Context

This step is the sole working step in the `vulnerability_scan` workflow (after `gather_context`). It produces a standalone vulnerability report.

Security scanning is one of the most operationally important platform engineering tasks. The output needs to be immediately actionable — a developer should be able to take the Remediation Plan section and start fixing vulnerabilities without additional research.

The exploitability assessment is where this step adds the most value beyond raw scanner output. Scanners report every known CVE in every dependency, but not all of them are equally urgent. A critical RCE vulnerability in a package used only in the test suite has lower practical risk than a medium SSRF in a package that handles user input in production. The agent's role is to make these contextual risk assessments explicit so the team can prioritize effectively.

Convention 30 (weekly scans) is the foundation of ongoing security hygiene. If automated scanning is not configured, that is the highest-priority recommendation regardless of what the current scan finds. One-time scans catch existing issues; automated scanning catches new ones as they are disclosed.

Convention 33 (automated updates via Dependabot/Renovate) represents the proactive side of vulnerability management. When dependency update automation is properly configured, many vulnerabilities are addressed automatically before they accumulate. If this infrastructure is missing, recommending it is high-impact.

Multiple scanners may report the same vulnerability (e.g., both `npm audit` and `trivy fs` may flag the same CVE in a Node.js dependency). The report SHOULD deduplicate findings where possible, noting which scanners detected each issue. This avoids inflating the count and provides a more accurate picture of the actual vulnerability surface.
