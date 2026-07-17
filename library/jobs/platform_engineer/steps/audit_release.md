# Audit Release Process

## Objective

Review the existing release process for the repository to determine what release infrastructure exists, assess compliance with release management conventions 24-29, and identify gaps that need to be addressed in the next step (`setup_release_pipeline`). This is a read-only audit — no files are created or modified except the output artifact.

## Task

Systematically examine the repository for all release-related infrastructure, tooling, and conventions. Compare findings against the platform engineering release management standards and produce a detailed gap analysis.

### Process

#### 1. Read Context

Read `context.md` produced by `gather_context` to understand:
- Which CI provider is in use (GitHub Actions, Forgejo Actions, GitLab CI, etc.)
- Which package managers and build tools are available (npm, cargo, uv, etc.)
- Repository structure — where CI configs, scripts, and docs live
- What cloud CLIs or registries are available for artifact publishing

This determines which files to look for and which tools to check.

#### 2. Check for Existing Release Infrastructure

Examine each category of release infrastructure. For each item, record whether it exists, its location, and its current configuration.

**CI release workflows:**
- Check for dedicated release workflow files. Common names and locations:
  - `.github/workflows/release.yml`, `.github/workflows/release.yaml`
  - `.github/workflows/publish.yml`, `.github/workflows/deploy.yml`
  - `.github/workflows/cd.yml`
  - `.forgejo/workflows/release.yml`
  - `.gitlab-ci.yml` (look for `release` or `deploy` stages)
- Read any found release workflow files to understand:
  - What triggers the release (tag push, manual dispatch, merge to main)
  - What stages exist (build, test, tag, publish)
  - Where artifacts are published (npm, PyPI, crates.io, container registry, GitHub Releases)
  - Whether the workflow creates GitHub Releases with notes

**Version files:**
- Check for version definitions in project manifests:
  - `package.json` — look for `"version"` field
  - `Cargo.toml` — look for `version =` in `[package]`
  - `pyproject.toml` — look for `version =` in `[project]` or `[tool.poetry]`
  - `setup.py` or `setup.cfg` — look for `version=`
  - `flake.nix` — check if version is tracked
  - Custom version files: `VERSION`, `version.txt`, `src/**/version.py`, `src/**/version.ts`
- Note the current version value and whether it follows SemVer (MAJOR.MINOR.PATCH)

**Changelog files:**
- Search for changelog files at the repository root:
  - `CHANGELOG.md`, `CHANGELOG`, `CHANGELOG.txt`
  - `CHANGES.md`, `CHANGES`
  - `HISTORY.md`, `HISTORY`
  - `NEWS.md`, `NEWS`
- If found, check the format:
  - Is it manually maintained or auto-generated?
  - Does it follow Keep a Changelog format?
  - Are entries linked to commits or PRs?
  - When was the last entry added?

**Release branch patterns:**
- Run `git branch -r | grep -iE 'release|hotfix'` to check for release branch naming patterns
- Check for branch protection rules if GitHub CLI is available: `gh api repos/{owner}/{repo}/branches`
- Look for documentation of branching strategy in README, CONTRIBUTING, or docs/

**Tag conventions:**
- Run `git tag --list` to see existing tags
- Analyze tag naming patterns:
  - SemVer tags: `v1.2.3`, `1.2.3`
  - Pre-release tags: `v1.2.3-rc.1`, `v1.2.3-beta.1`
  - Prefix conventions: `v` prefix, package-scoped tags like `@scope/pkg@1.2.3`
- Check tag frequency and recency: when was the last tag created?
- Run `git tag --list --sort=-creatordate | head -10` for the most recent tags

**GitHub Releases:**
- If `gh` CLI is available, run `gh release list --limit 10` to check for existing releases
- Note whether releases have release notes, assets, or are auto-generated
- Check if releases are marked as pre-release or draft

**Release scripts:**
- Check for release automation scripts:
  - `scripts/release.*` (sh, bash, py, ts, js)
  - `bin/release`, `bin/publish`
  - Makefile targets: look for `release`, `publish`, `deploy` targets in `Makefile` or `Justfile`
- Read any found scripts to understand the current release process

**Release tooling configuration:**
- Check for release tool configs:
  - `.release-please-manifest.json`, `release-please-config.json` (release-please)
  - `.releaserc`, `.releaserc.json`, `.releaserc.yml` (semantic-release)
  - `cliff.toml`, `.cliff.toml` (git-cliff)
  - `.changeset/config.json` (changesets)
  - `cargo-release` config in `Cargo.toml` or `.cargo/config.toml`
  - `.goreleaser.yml`, `.goreleaser.yaml` (goreleaser)

**Release policy clarity:**
- Check whether the repository already makes the release policy explicit in docs or automation.
- At minimum, look for explicit decisions about:
  - release cadence
  - version semantics
  - stabilization model
  - backport policy
  - hotfix policy
  - merge-back policy
  - publish targets
  - stable-vs-unstable consumption guidance
- If any of those remain unclear after auditing the repo, record them as policy gaps that the setup step MUST ask the user to resolve.

#### 3. Assess Against Release Management Conventions

Evaluate each convention with a clear pass/fail/partial/not-applicable status:

**Convention 24 — SemVer compliance:**
- Does the project use semantic versioning?
- Are version bumps consistent (do tags follow SemVer)?
- Is there a mechanism for automated version bumping?

**Convention 25 — Release notes generation:**
- Are release notes generated before publishing?
- Are they manual, semi-automated, or fully automated?
- Do they include meaningful descriptions of changes?

**Convention 26 — Release branch strategy:**
- Is a branching strategy documented?
- Are `release/*` or `hotfix/*` branches used?
- Is the merge flow clear (who creates branches, how they flow back to main)?

**Convention 27 — CI release pipeline stages:**
- Does the CI release pipeline include all required stages: build, test, tag, publish?
- Are any stages missing?
- Is the pipeline triggered appropriately (tag push, manual, etc.)?

**Convention 28 — Automated artifact publishing:**
- Are artifacts published automatically through CI?
- Or is publishing manual (e.g., someone runs `npm publish` locally)?
- Where are artifacts published to?

**Convention 29 — Changelog from commits/PRs:**
- Are changelog entries derived from conventional commits or PR titles?
- Or is the changelog manually curated?
- Is the changelog up to date with recent releases?

#### 4. Document Findings

Compile all findings into the output document, clearly separating what exists from what is missing. Be specific about file paths, tool versions, and configuration details so the next step (`setup_release_pipeline`) can act on the gaps without re-scanning.

## Output Format

Write the audit to `.deepwork/artifacts/platform_engineer/release_builder/release_audit.md`. Create parent directories if they do not exist.

```markdown
# Release Process Audit

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name>

## Current State

### CI Release Workflows
- **Found**: yes / no
- **Files**: <list of workflow file paths, or "none">
- **Trigger**: <tag push / manual dispatch / merge to main / none>
- **Stages**: <build / test / tag / publish — list which exist>
- **Publish target**: <npm / PyPI / container registry / GitHub Releases / none>
- **Notes**: <any observations about the workflow quality or completeness>

### Versioning
- **Version file(s)**: <file path(s) and current version value>
- **SemVer compliant**: yes / no / partial
- **Version bumping**: <manual / automated tool name / none>
- **Notes**: <any observations>

### Changelog
- **File**: <path or "none">
- **Format**: <Keep a Changelog / custom / auto-generated / none>
- **Last updated**: <date or "unknown">
- **Derived from commits**: yes / no / unknown
- **Notes**: <any observations>

### Tags
- **Total tags**: <count>
- **Recent tags** (last 5):
  - <tag> — <date>
  - ...
- **Naming pattern**: <vX.Y.Z / X.Y.Z / other>
- **Pre-release tags used**: yes / no

### GitHub Releases
- **Total releases**: <count or "not checked">
- **Recent releases** (last 5):
  - <version> — <date> — <has notes: yes/no>
  - ...
- **Auto-generated notes**: yes / no
- **Release assets**: <list or "none">

### Release Branches
- **Pattern detected**: <release/* / hotfix/* / none>
- **Branch protection**: <configured / not configured / not checked>
- **Strategy documented**: yes / no — <location if yes>

### Release policy
- **Cadence documented**: yes / no — <where, or "not explicit">
- **Version semantics documented**: yes / no — <where, or "not explicit">
- **Stabilization model documented**: yes / no — <where, or "not explicit">
- **Backport policy documented**: yes / no — <where, or "not explicit">
- **Hotfix policy documented**: yes / no — <where, or "not explicit">
- **Merge-back policy documented**: yes / no — <where, or "not explicit">
- **Stable vs unstable guidance documented**: yes / no — <where, or "not explicit">
- **Open policy questions for user**: <list or "none">

### Release Scripts
- **Scripts found**: <list of paths or "none">
- **Makefile/Justfile targets**: <list or "none">
- **Purpose**: <brief description of what scripts do>

### Release Tooling
- **Tool**: <release-please / semantic-release / git-cliff / changesets / goreleaser / none>
- **Config file**: <path or "none">
- **Notes**: <any observations about configuration>

## Convention Compliance

| # | Convention | Status | Notes |
|---|-----------|--------|-------|
| 24 | SemVer versioning | pass / fail / partial | <details> |
| 25 | Release notes generated | pass / fail / partial | <details> |
| 26 | Release branch strategy documented | pass / fail / partial | <details> |
| 27 | CI pipeline: build/test/tag/publish | pass / fail / partial | <details> |
| 28 | Automated artifact publishing | pass / fail / partial | <details> |
| 29 | Changelog from commits/PRs | pass / fail / partial | <details> |

## Gaps

| Gap | Convention | Recommendation | Priority |
|-----|-----------|----------------|----------|
| <what is missing> | <convention #> | <specific recommendation> | high / medium / low |
| ... | ... | ... | ... |

Priority guide:
- **High**: Missing fundamental release capability (no versioning, no CI pipeline)
- **Medium**: Exists but incomplete (pipeline missing stages, manual steps that should be automated)
- **Low**: Nice-to-have improvements (better changelog format, pre-release tag support)

## Versioning Assessment

<Paragraph summarizing the overall state of versioning in the project:
current scheme, consistency, whether it matches the ecosystem conventions
(e.g., npm expects SemVer), and recommendation for the version bumping
strategy to adopt in setup_release_pipeline.>
```

## Quality Criteria

- **Current State Documented**: The existing release process (or lack thereof) is fully documented with specific file paths, tool names, and configuration details. No area is left as "did not check."
- **Gaps Identified**: Missing components are identified by systematically checking against each of the six release management conventions (24-29). Each gap includes a concrete recommendation, not just "add this."
- **Versioning Assessed**: The current versioning scheme is documented with the actual version value, tag history, and a clear assessment of SemVer compliance. The assessment includes a recommendation for the version bumping approach.
- **Policy Gaps Identified**: Missing release-policy decisions that require explicit user judgment are called out before automation work begins.
- **Actionable for Next Step**: The audit contains enough detail that `setup_release_pipeline` can act on every gap without re-scanning the repository. File paths, tool names, and specific missing pieces are all documented.
- **No Changes Made**: This step is read-only. No files in the repository are created or modified. Only the output artifact is written.

## Context

This step is the first of two in the `release_builder` workflow. It runs after `gather_context` and feeds directly into `setup_release_pipeline`. The audit output is the primary input for the setup step, so completeness and specificity matter — vague findings lead to vague setup recommendations.

The six release management conventions (24-29) in `conventions.md` define the target state. This audit measures the distance between current state and target state for each convention. The gap table with priorities helps the user and the setup step focus on the most impactful improvements first.

Projects at different maturity levels will have vastly different starting points — from zero release infrastructure to fully automated pipelines with minor gaps. The audit must handle both extremes gracefully, documenting "none" or "not found" explicitly rather than omitting sections.
