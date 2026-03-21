<!-- RFC 2119: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY -->
# Platform Engineering Conventions

This document defines the standards and practices for platform engineering workflows.
All step instructions in this job reference these conventions. Language follows RFC 2119.

## Investigation Principles

1. Agents MUST NOT take destructive actions during incident investigation.
2. Agents MUST suggest remediation commands but MUST NOT execute them without explicit user approval.
3. Investigation findings MUST include timestamps, evidence sources, and confidence levels.
4. Cross-referencing between data sources (logs, metrics, events) MUST be performed before assigning high confidence to a root cause hypothesis.
5. Confidence levels MUST follow this scale:
   - **High**: Verified with actual runtime data (checked real values, tested connections).
   - **Medium**: Supported by multiple indirect evidence points but not directly verified.
   - **Low**: Plausible based on architecture/code analysis, but no direct evidence.
6. Agents SHOULD document what was checked even when no anomalies are found — this narrows the investigation scope.

## Observability Standards

7. Every production service MUST have a primary dashboard covering the four golden signals: latency, traffic, errors, and saturation.
8. Dashboards MUST include time range selectors and SHOULD default to the last 1 hour.
9. Alert rules MUST have associated runbooks or investigation steps documented in the repository.
10. Log-based alerts SHOULD complement metric-based alerts for services where structured logging is available.
11. Loki queries MUST use label filters to avoid scanning all log streams.
12. Dashboard queries MUST specify explicit time ranges rather than relying on defaults.

## Infrastructure Standards

13. Infrastructure changes MUST be declarative (IaC) where tooling exists for the target platform.
14. Infrastructure configuration MUST be documented in a discoverable location within the repository (e.g., `docs/infrastructure.md` or `INFRASTRUCTURE.md`).
15. Secrets MUST NOT be stored in plain text in repositories, CI configs, or container images.
16. Resource limits (CPU, memory) MUST be set for all containerized workloads.
17. Infrastructure decisions SHOULD be recorded as Architecture Decision Records (ADRs) or equivalent documentation.

## CI/CD Standards

18. CI pipelines for pull requests SHOULD complete in under 10 minutes.
19. Build caching MUST be enabled where the CI provider supports it.
20. Dependency installation SHOULD be cached across CI runs.
21. Pipeline configurations SHOULD be linted or validated in CI (e.g., `actionlint` for GitHub Actions).
22. CI config files MUST NOT contain hardcoded secrets — use CI provider secret management.
23. Test stages SHOULD run in parallel where test suites are independent.

## Release Management Standards

24. Repositories MUST use semantic versioning (SemVer) for releases.
25. Release notes MUST be generated or reviewed before publishing a release.
26. Release branches (e.g., `release/*`, `hotfix/*`) SHOULD follow a documented branching strategy.
27. CI release pipelines MUST include: build, test, tag, and publish stages.
28. Artifact publishing MUST be automated through CI — manual uploads MUST NOT be the primary method.
29. Changelog entries SHOULD be derived from conventional commit messages or PR titles.

## Security Standards

30. Vulnerability scans MUST be run at least weekly on production dependencies.
31. Critical and High severity CVEs MUST be addressed within the timeframe defined by the organization's security policy.
32. Container base images MUST be kept up to date and SHOULD use minimal base images (e.g., distroless, Alpine).
33. Dependency updates SHOULD be automated using tools such as Dependabot, Renovate, or equivalent.
34. Security scan results MUST be triaged — not just collected — with clear severity assessments and remediation priorities.

## Cloud Cost Standards

35. Idle resources (unused load balancers, detached volumes, stopped instances) SHOULD be flagged and reviewed monthly.
36. Right-sizing recommendations SHOULD be reviewed quarterly.
37. Cost anomaly alerts SHOULD be configured where the cloud provider supports them.
38. Development and staging environments SHOULD auto-scale down or shut off outside business hours where feasible.
39. Cost analysis MUST distinguish between fixed costs and variable/usage-based costs.

## Migration Standards

40. Infrastructure migrations MUST have a documented rollback plan before execution begins.
41. Migration plans MUST be documented in a GitHub issue with a detailed checklist of steps.
42. Data migrations MUST be tested against a copy of production data before executing in production.
43. Blue-green or canary deployment SHOULD be used for critical service migrations.
44. Each migration step MUST have a validation gate — a check that confirms the step succeeded before proceeding.
45. Migration state (which steps completed, which are pending) MUST be tracked in the GitHub issue.

## Developer Environment Standards

46. Local development setup instructions MUST be documented in the repository (e.g., `README.md` or `docs/development.md`).
47. Development environments SHOULD be reproducible — using Nix flakes, Docker Compose, or equivalent.
48. Common developer issues and their solutions SHOULD be documented in a troubleshooting guide.
49. The `doctor` workflow SHOULD be the first tool a developer uses when their environment is broken.

## Error Tracking Standards

50. Production services MUST have exception monitoring configured (e.g., Sentry, Honeybadger, Bugsnag).
51. Error tracking MUST capture: stack traces, request context, user context (anonymized), and environment metadata.
52. Source maps or debug symbols SHOULD be uploaded during the release process for compiled/minified code.
53. Error tracking alerts SHOULD be configured for new error types and error rate spikes.
54. Error tracking configuration (DSN, SDK version) MUST be documented in the repository.

## Grafana MCP Usage

55. Agents SHOULD use Grafana MCP tools when available for querying dashboards, metrics, and logs.
56. If Grafana MCP is not available, agents MUST fall back to CLI tools (kubectl logs, prometheus CLI, etc.) and note this limitation.
57. Grafana MCP dashboard queries MUST specify explicit time ranges.
58. Loki queries via Grafana MCP MUST use label filters and SHOULD limit result counts to avoid timeouts.
59. Agents SHOULD check for active alerts via AlertManager before beginning manual investigation.

## SOC 2 Compliance Standards

60. Every repository subject to SOC 2 MUST maintain a compliance document at `docs/compliance/soc2.md` (or `COMPLIANCE.md` at the repo root) that records the current state of controls, evidence references, and audit readiness.
61. The compliance document MUST be platform-agnostic — it records what controls exist and where evidence is found, independent of any specific compliance platform (Vanta, Drata, Secureframe, etc.).
62. The compliance document MUST be kept in version control so that changes to controls are tracked over time.
63. Controls MUST be assessed against all applicable SOC 2 Trust Service Criteria: Security (CC), Availability, Processing Integrity, Confidentiality, and Privacy.
64. Each control MUST be classified as: **implemented** (evidence exists), **partial** (partially implemented or missing evidence), or **missing** (not implemented).
65. For each implemented control, the compliance document MUST reference where the evidence can be found (file path, CI workflow, dashboard URL, policy document, etc.).
66. Controls that require manual evidence (e.g., HR onboarding procedures, background checks, annual reviews) MUST be listed in an evidence collection checklist with the responsible party and collection cadence.
67. The `soc_audit` workflow SHOULD be run at least quarterly to keep the compliance document current.
68. Automated controls (encryption at rest, access logging, vulnerability scanning) SHOULD be verified by checking the actual infrastructure configuration, not just by reviewing documentation.
69. The compliance document SHOULD map each control to the specific TSC criteria it satisfies (e.g., CC6.1, A1.2) to facilitate auditor review.
70. Gap remediation recommendations MUST include estimated effort and priority to help teams plan compliance work.
