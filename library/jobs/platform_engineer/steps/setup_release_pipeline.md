# Set Up Release Pipeline

## Objective

Configure a complete release pipeline based on the gaps identified in `release_audit.md`. For each missing or incomplete piece of release infrastructure, create the appropriate configuration files, CI workflows, and documentation. All decisions that require user judgment (e.g., which registry to publish to, which branching model to follow) MUST be surfaced via `AskUserQuestion` before proceeding.

## Task

Read the release audit, identify what needs to be built, and systematically set up each missing component. The goal is to move every release management convention (24-29) from fail/partial to pass.

### Process

#### 1. Read Inputs

Read both input files:
- `release_audit.md` — the gap analysis from the previous step. Focus on the Gaps table and Convention Compliance section to determine what needs to be done.
- `context.md` — the platform context. Use this to determine which CI provider to target, which package ecosystem the project uses, and what tools are available.

Identify the project's primary stack from context.md (e.g., Node/npm, Python/uv, Rust/cargo, Go, Nix) because this determines which versioning tools, changelog generators, and publishing targets are appropriate.

#### 2. Set Up Versioning (Convention 24)

If the audit shows versioning is missing or not SemVer-compliant:

**Choose a version bumping tool based on the stack:**

| Stack | Recommended Tool | Config File |
|-------|-----------------|-------------|
| Node (npm/pnpm) | `npm version` or `standard-version` | `package.json` |
| Python (uv/pip) | `python-semantic-release` or `bump2version` | `pyproject.toml` |
| Rust (cargo) | `cargo-release` | `Cargo.toml` + `release.toml` |
| Go | `svu` or manual tag | — |
| Nix | Manual version in `flake.nix` or a `VERSION` file | `flake.nix` |
| Multi-language | `release-please` (supports many ecosystems) | `release-please-config.json` |

If the project already has a version defined but lacks automation, configure the appropriate tool to read and bump that version.

If the choice is ambiguous (e.g., monorepo with multiple languages), use `AskUserQuestion` to confirm:
> Which version management approach do you prefer?
> 1. Single version for the whole repo (recommended for most projects)
> 2. Per-package versioning (for monorepos with independent release cycles)
> 3. Keep the current manual approach, just add SemVer validation

**Actions:**
- Ensure a version is defined in the appropriate manifest file
- Configure the version bumping tool with a config file if needed
- Document the versioning scheme in `release_docs.md`

#### 3. Set Up Changelog Generation (Convention 29)

If the audit shows no changelog or manually maintained changelog:

**Choose a changelog tool based on the stack and CI provider:**

| Tool | Best For | Config File |
|------|----------|-------------|
| `git-cliff` | Any stack, flexible templates | `cliff.toml` |
| `conventional-changelog` | Node projects | `.changelogrc` |
| `release-please` | GitHub Actions projects (also handles versioning) | `release-please-config.json` |
| `changesets` | Monorepos with npm packages | `.changeset/config.json` |
| `towncrier` | Python projects | `pyproject.toml` `[tool.towncrier]` |

If the project uses conventional commits (check recent commit history with `git log --oneline -20`), prefer tools that parse conventional commits directly.

Use `AskUserQuestion` if commit history is not conventional:
> Your recent commits do not follow conventional commit format. How should changelog entries be generated?
> 1. Start using conventional commits going forward, and generate changelog from them
> 2. Generate changelog from PR titles (requires GitHub)
> 3. Use manual changelog fragments (e.g., changesets or towncrier)

**Actions:**
- Install and configure the chosen changelog tool
- Create the configuration file with appropriate settings (commit types to include, output format, template)
- If a `CHANGELOG.md` does not exist, create an initial one (empty or seeded from existing tags)
- Document the changelog approach in `release_docs.md`

#### 4. Document Release Branch Strategy (Convention 26)

If the audit shows no documented branching strategy:

Use `AskUserQuestion` to determine the branching model:
> Which release branching strategy fits your workflow?
> 1. **Trunk-based**: Release directly from `main` via tags. No release branches. Best for continuous delivery.
> 2. **Release branches**: Create `release/X.Y` branches for stabilization before release. Best for projects with QA cycles.
> 3. **GitFlow**: `develop` + `release/*` + `hotfix/*` branches. Best for projects with scheduled releases.
> 4. **Keep current approach**: Document whatever you are doing now.

**Actions based on choice:**

For **trunk-based**:
- Document that releases are cut from `main` by tagging
- No branch protection beyond `main` is needed
- Configure CI to trigger release on tag push matching `v*`

For **release branches**:
- Document the branch naming convention (`release/X.Y`)
- Document who creates release branches and the merge flow (release branch merges to main AND tag)
- Configure branch protection for `release/*` if supported

For **GitFlow**:
- Document the full branch hierarchy and merge directions
- Configure branch protection for `develop`, `release/*`, and `hotfix/*`

**In all cases:**
- Write the branching strategy documentation to a discoverable location (e.g., `docs/releasing.md` or a section in `CONTRIBUTING.md`)
- Document the strategy in `release_docs.md`

#### 5. Create CI Release Workflow (Convention 27)

If the audit shows no CI release pipeline or the pipeline is missing stages:

Create a CI workflow file appropriate to the detected CI provider. The workflow MUST include all four required stages: build, test, tag, publish.

**GitHub Actions example structure:**

```yaml
name: Release
on:
  push:
    tags: ['v*']
  # Or: workflow_dispatch for manual releases

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      # Build stage
      - uses: actions/checkout@v4
      - name: Set up <language>
        # ...
      - name: Install dependencies
        # ...
      - name: Build
        # ...

      # Test stage
      - name: Run tests
        # ...

      # Tag stage (if not triggered by tag)
      - name: Create tag
        # Only if using workflow_dispatch trigger
        # ...

      # Publish stage
      - name: Publish to <registry>
        # ...
      - name: Create GitHub Release
        # ...
```

**Forgejo Actions:** Use a similar structure but check for Forgejo-specific syntax differences.

**GitLab CI:** Use stages: [build, test, release] with appropriate `only: tags` rules.

Use `AskUserQuestion` to determine publish targets:
> Where should release artifacts be published? (select all that apply)
> 1. GitHub Releases (binary assets, tarballs)
> 2. npm registry
> 3. PyPI
> 4. crates.io
> 5. Container registry (Docker Hub, GHCR, etc.)
> 6. Nix flake (users consume via flake input)
> 7. Other: <describe>

**Actions:**
- Create the CI workflow file in the appropriate location
- Include all four stages (build, test, tag, publish)
- Use CI provider secret management for registry credentials — NEVER hardcode tokens
- Add comments in the workflow explaining each stage
- Document which secrets need to be configured in CI settings (e.g., `NPM_TOKEN`, `PYPI_TOKEN`)

#### 6. Configure Automated Artifact Publishing (Convention 28)

If the audit shows manual publishing:

Based on the publish targets from step 5:

**npm**: Add `npm publish` step with `NODE_AUTH_TOKEN` secret
**PyPI**: Add `twine upload` or `uv publish` step with `PYPI_TOKEN` secret
**crates.io**: Add `cargo publish` step with `CARGO_REGISTRY_TOKEN` secret
**Container registry**: Add `docker build && docker push` with registry credentials
**GitHub Releases**: Use `gh release create` or `softprops/action-gh-release` action
**Nix flake**: Document that users consume via `inputs.project.url` (no explicit publish step needed)

**Actions:**
- Add publish steps to the CI release workflow
- Document which secrets need to be created in CI settings
- List the secrets in `release_docs.md` with instructions for how to obtain them (but NEVER include actual secret values)

#### 7. Configure Release Notes (Convention 25)

If the audit shows no release notes generation:

**Option A — release-please (GitHub only):**
- Creates release PRs automatically from conventional commits
- Generates changelog and release notes
- Handles version bumping
- Create `.github/release-please-config.json` and `.release-please-manifest.json`

**Option B — git-cliff + GitHub Release:**
- Use `git-cliff` to generate release notes at CI time
- Pass output to `gh release create --notes-file`
- Works with any CI provider

**Option C — GitHub auto-generated release notes:**
- Configure `.github/release.yml` to categorize PRs by label
- Use `gh release create --generate-notes`
- Simplest option but least customizable

Use `AskUserQuestion` if the preferred approach is unclear based on the stack.

**Actions:**
- Configure the chosen release notes tool
- Integrate it into the CI release workflow
- Document the approach in `release_docs.md`

#### 8. Document All Decisions

Create `release_docs.md` as a comprehensive record of all setup decisions. This serves both as documentation for the team and as an artifact for the review step.

## Output Format

### release_configs (files)

The specific files created depend on the stack and CI provider. Common examples:
- `.github/workflows/release.yml` — CI release workflow
- `cliff.toml` or `.changeset/config.json` — Changelog tool config
- `release-please-config.json` — Release automation config
- `docs/releasing.md` — Release branch strategy documentation

### release_docs.md

Write to `.deepwork/tmp/platform_engineer/release_builder/release_docs.md`:

```markdown
# Release Pipeline Setup

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name>

## Decisions Made

### Versioning
- **Tool**: <chosen tool>
- **Rationale**: <why this tool was chosen>
- **Version file**: <path to version definition>
- **Bump process**: <how versions are bumped — e.g., "run `npm version patch/minor/major`">

### Changelog
- **Tool**: <chosen tool>
- **Config file**: <path>
- **Entry source**: <conventional commits / PR titles / manual fragments>
- **Output file**: <path to CHANGELOG.md>

### Release Branch Strategy
- **Model**: <trunk-based / release branches / gitflow>
- **Branch naming**: <pattern>
- **Documentation**: <path to strategy docs>

### CI Release Pipeline
- **Workflow file**: <path>
- **Trigger**: <tag push / workflow_dispatch / release PR merge>
- **Stages**: build, test, tag, publish
- **Publish targets**: <list>

### Release Notes
- **Tool**: <chosen tool>
- **Integration**: <how it connects to the release workflow>

### Artifact Publishing
- **Target(s)**: <list of registries / release assets>
- **CI secrets required**:
  - `SECRET_NAME` — <what it is, how to obtain it>
  - ...

## Files Created

| File | Purpose |
|------|---------|
| <path> | <description> |
| ... | ... |

## Post-Setup Steps

<List any manual steps the user needs to complete, such as:
- Adding CI secrets
- Enabling branch protection
- Configuring registry access
- First release dry-run>

## Convention Coverage

| # | Convention | Status After Setup |
|---|-----------|-------------------|
| 24 | SemVer versioning | pass |
| 25 | Release notes generated | pass |
| 26 | Release branch strategy documented | pass |
| 27 | CI pipeline: build/test/tag/publish | pass |
| 28 | Automated artifact publishing | pass |
| 29 | Changelog from commits/PRs | pass |
```

## Quality Criteria

- **Pipeline Complete**: The CI release pipeline includes all four required stages — build, test, tag, and publish — per convention 27. No stage is omitted or left as a placeholder.
- **Versioning Configured**: Semantic versioning is set up with a concrete version bumping mechanism appropriate to the project's stack. The user knows exactly how to bump a version.
- **Release Notes Configured**: Changelog or release notes generation is configured and integrated into the release workflow per convention 29. The tool parses commits or PRs automatically.
- **Branch Strategy Documented**: The release branching strategy is documented in a discoverable location within the repository, not just in the artifact.
- **Decisions Documented**: All setup decisions (tool choices, publish targets, branching model) are recorded in `release_docs.md` with rationale. A new team member could understand the release process by reading this document.
- **Secrets Not Exposed**: No secret values, tokens, or credentials appear in any created files. CI secrets are referenced by name only, with instructions for how to set them up.
- **User Consulted**: Decisions requiring user judgment (registry targets, branching model, changelog approach) were surfaced via `AskUserQuestion` rather than assumed.

## Context

This step is the second of two in the `release_builder` workflow. It receives `release_audit.md` and `context.md` as inputs and produces configuration files plus documentation.

The step is interactive — it uses `AskUserQuestion` for decisions that depend on team preferences, organizational policies, or business requirements. Examples include which registry to publish to, which branching model to follow, and how changelog entries should be generated. The agent MUST NOT make these decisions unilaterally.

The output must be immediately usable. After this step completes, the user should be able to trigger their first release (possibly a dry-run) using the configured pipeline. Any manual steps that remain (e.g., adding CI secrets) MUST be clearly documented in the Post-Setup Steps section of `release_docs.md`.

Convention 22 from `conventions.md` (CI configs MUST NOT contain hardcoded secrets) is especially relevant here — the CI workflow files created in this step MUST use CI provider secret management exclusively.
