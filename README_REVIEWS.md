# DeepWork Reviews

DeepWork Reviews lets you define automated code review policies using `.deepreview` config files placed anywhere in your project. When you run a review, it detects which files changed on your branch, matches them against your rules, and dispatches parallel review agents — each with focused instructions and only the files it needs to see.

## Examples of What You Can Do with DeepWork Reviews

- **Targeted code reviews** — Match files by language or directory so each review rule focuses on the right code (e.g., Python best practices for `**/*.py`, TypeScript linting for `**/*.ts`)
- **Prompt and instruction file reviews** — Watch your prompt files, agent definitions, and skill instructions for adherence to prompt engineering best practices
- **Documentation-code sync checks** — Monitor documentation files alongside the code they describe, and flag when one changes without the other
- **"Gotcha" regression checkers** — Watch a specific file or module for a known class of mistake that has regressed before, with instructions describing exactly what to look for
- **Cross-file consistency reviews** — Group a logical set of interrelated files (e.g., API schema + client code + tests) so the reviewer can verify that any individual change makes sense in the wider context
- **Tone and style reviews for human-facing content** — Review copy, docs, blog posts, or marketing pages for consistent voice, reading level, and style guidelines
- **Requirements validation** — Verify that code, config, and instruction files satisfy formal requirements that need judgment to evaluate (see below)

## How It Works

1. You create `.deepreview` files that define review rules (what to match, how to review)
2. You run `deepwork review --instructions-for claude`
3. DeepWork Reviews diffs your branch, matches changed files to rules, and generates review instructions
4. Your CLI agent spawns parallel review tasks — one per rule match — each scoped to exactly the right files

The outer agent never needs to load the full context of every review. Each sub-agent gets a self-contained instruction file with just its files and instructions.

## What Files Are Considered "Changed"?

When you run a review without explicit `--files`, DeepWork detects changed files using local git operations. Here's exactly what is and isn't included:

### Included

| Change type | Example | Why it's included |
|-------------|---------|-------------------|
| **Committed changes on your branch** | You committed a fix 3 commits ago | `git diff` against the merge-base with `main`/`master` catches all commits since the branch diverged |
| **Staged but not yet committed** | You ran `git add myfile.py` but haven't committed | A separate `git diff --cached` picks up index changes |
| **Unstaged modifications to tracked files** | You edited a file but haven't staged it | The working-tree diff against the merge-base includes these |

### Not included

| Change type | Why it's excluded |
|-------------|-------------------|
| **Untracked files** (new files never added to git) | `git diff` only operates on tracked files. Run `git add` first, or pass them explicitly with `--files`. |
| **Deleted files** | The `--diff-filter=ACMR` flag excludes deletions — there's nothing to review in a deleted file. |

### Local-only detection

All detection is local. DeepWork does not fetch from or communicate with any remote (GitHub, GitLab, etc.). This means:

- **Commits pushed to the remote but not fetched locally** won't appear. Run `git fetch` first if your local branch is behind.
- **Commits that are local but not yet pushed** are fully included — pushing has no effect on what DeepWork sees.
- In practice, if your local branch is up to date, the changed files match what a GitHub PR would show.

### Overriding detection

You can bypass git diff entirely by providing files explicitly:

```bash
# Explicit file arguments (highest priority)
deepwork review --instructions-for claude --files src/app.py --files src/lib.py

# Piped from another command (second priority)
git diff --name-only HEAD~3 | deepwork review --instructions-for claude
```

When files are provided explicitly, `--base-ref` is ignored.

## The `.deepreview` Config File

A `.deepreview` file is YAML. It contains one or more named rules, each with a `match` section (what files to trigger on) and a `review` section (how to review them).

### Placement in the File Hierarchy

`.deepreview` files work like `.gitignore` — each file applies to the directory it lives in, and its glob patterns match relative to that directory. You can place them at any level:

```
my-project/
├── .deepreview              # Rules for the whole project
├── src/
│   ├── .deepreview          # Rules scoped to src/
│   └── auth/
│       └── .deepreview      # Rules scoped to src/auth/
└── infrastructure/
    └── .deepreview          # Rules scoped to infrastructure/
```

A `.deepreview` at the root with `include: ["**/*.py"]` matches all Python files in the project. The same pattern in `src/.deepreview` only matches Python files under `src/`. Rules from different files are completely independent — they don't override or interact with each other.

This lets you keep review policies close to the code they govern. The security team can own `src/auth/.deepreview`, the platform team can own `infrastructure/.deepreview`, and so on.

### Rule Structure

```yaml
rule_name:
  description: "Short description"  # Required. Under 256 characters.
  match:
    include:
      - "glob/pattern/**/*.ext"    # Required. At least one pattern.
    exclude:                        # Optional.
      - "pattern/to/skip/**"
  review:
    strategy: individual            # Required. How to group files.
    instructions: |                 # Required. What to tell the reviewer.
      Review this file for ...      # Can be inline text (like this) or a file reference like:
    # instructions:
    #   file: .deepwork/review/python_review.md
    agent:                          # Optional. Use a specific agent persona.
      claude: "security-expert"
    additional_context:             # Optional. Extra context for the reviewer.
      all_changed_filenames: true
      unchanged_matching_files: true
```

## Review Strategies

The `strategy` field controls how matched files are grouped into review tasks.

### `individual` — One review per file

Each changed file that matches the rule gets its own review task. The reviewing agent sees only that one file.

Best for: file-level linting, per-component checks, style reviews.

```yaml
python_review:
  description: "Review Python source files for code quality and best practices."
  match:
    include:
      - "**/*.py"
    exclude:
      - "tests/**/*.py"
  review:
    strategy: individual
    instructions:
      file: .github/prompts/python_review.md
```

### `matches_together` — One review for all matched files

All changed files matching the rule are grouped into a single review task. The reviewing agent sees all of them together.

Best for: cross-file consistency checks, migration sequence validation, documentation link checks.

```yaml
db_migration_safety:
  description: "Check database migrations for conflicts, destructive ops, and ordering."
  match:
    include:
      - "alembic/versions/*.py"
  review:
    strategy: matches_together
    agent:
      claude: "db-expert"
    instructions: |
      Review these database migrations together.
      Ensure there are no conflicting locks, no destructive
      drops without backups, and that the sequence IDs are ordered correctly.
```

### `all_changed_files` — Tripwire that reviews everything

The match patterns act as a trigger. If *any* changed file matches, the review task gets *all* changed files in the entire changeset — not just the matched ones.

Best for: security audits, broad impact analysis when sensitive areas are touched.

```yaml
pr_security_review:
  description: "Security audit triggered by auth or config changes."
  match:
    include:
      - "src/auth/**/*.py"
      - "config/*"
    exclude:
      - "config/*.dev.yaml"
  review:
    strategy: all_changed_files
    agent:
      claude: "security-expert"
    instructions: |
      A change was detected in the authentication module or core config.
      Review all the changed files in this changeset for potential security
      regressions, leaked secrets, or broken authorization logic.
```

## Additional Context

The `additional_context` flags give the reviewer extra information beyond the matched files.

### `all_changed_filenames`

Includes a list of every file changed in the branch — even files that don't match this rule's patterns. The reviewer can use this to spot related changes (e.g., "a component's API changed but its consumers weren't updated").

```yaml
ui_component_review:
  description: "Review React components for accessibility and prop-type safety."
  match:
    include:
      - "src/components/**/*.tsx"
  review:
    strategy: individual
    additional_context:
      all_changed_filenames: true
    instructions: |
      Review this React component for accessibility and prop-type safety.
      Check the changed filenames list to see if the consumer of this component
      was also updated if you notice breaking API changes.
```

### `unchanged_matching_files`

Includes files that match the `include` patterns but were *not* changed. This is useful when you need the reviewer to see the complete set of files, not just the changed ones — for example, verifying version numbers are in sync.

```yaml
versions_in_sync:
  description: "Ensure version numbers stay in sync across release files."
  match:
    include:
      - "CHANGELOG.md"
      - "pyproject.toml"
      - "uv.lock"
  review:
    strategy: matches_together
    additional_context:
      unchanged_matching_files: true
    instructions: "Make sure the version number is exactly the same across all three of these files."
```

If only `pyproject.toml` changed, the reviewer still sees all three files so it can verify they match.

## Instructions

The `instructions` field tells the reviewing agent what to look for. It can be an inline string or a reference to an external file.

### Inline

```yaml
review:
  instructions: "Check for proper error handling and logging."
```

```yaml
review:
  instructions: |
    Review this file for:
    1. Proper error handling
    2. Consistent logging
    3. No hardcoded secrets
```

### File reference

```yaml
review:
  instructions:
    file: .deepwork/review/python_review.md
```

These are snippets showing just the `review` block. In a full rule, the `description` field is also required at the rule level (see Rule Structure above).

The file path is resolved relative to the directory containing the `.deepreview` file. This is useful for longer review guidelines that you want to maintain separately and reuse across rules.

We recommend putting instruction files in `.deepwork/review/` so they're easy to find and reuse across multiple `.deepreview` configs. For example, a single `python_review.md` file can be referenced from both root and subdirectory `.deepreview` files.

## Agent Personas

The optional `agent` field maps platform names to agent persona strings. When the review runs on that platform, the specified persona is used instead of the default agent.

```yaml
review:
  agent:
    claude: "security-expert"
```

This maps to Claude Code's agent system. If no agent is specified (or the platform key is missing), the default agent is used.

## Running a Review

```bash
deepwork review --instructions-for claude
```

This:
1. Finds all `.deepreview` files in your project
2. Runs `git diff` to detect changed files on your branch
3. Matches changed files against the rules
4. Generates instruction files in `.deepwork/tmp/review_instructions/`
5. Prints structured instructions for Claude Code to dispatch parallel review agents

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--instructions-for` | (required) | Target platform. Currently: `claude`. |
| `--base-ref` | auto-detect | Git ref to diff against. Auto-detects merge-base with `main` or `master`. |
| `--path` | `.` | Project root directory. |

### What the output looks like

```
Invoke the following list of Tasks in parallel:

Name: "python_review review of src/app.py"
	Agent: Default
	prompt: "@.deepwork/tmp/review_instructions/7142141.md"

Name: "python_review review of src/lib.py"
	Agent: Default
	prompt: "@.deepwork/tmp/review_instructions/6316224.md"

Name: "db_migration_safety review of 2 files"
	Agent: db-expert
	prompt: "@.deepwork/tmp/review_instructions/3847291.md"
```

Each sub-agent gets a self-contained instruction file. The `@` prefix tells Claude Code to read the file contents into the prompt. The outer agent stays lightweight — it just dispatches tasks.

## Full Example

Here is a `.deepreview` file that covers several common review scenarios:

```yaml
# =====================================================================
# Standard Python File Review
# Triggers on changes to any Python file outside of tests or docs.
# Every modified file is reviewed individually.
# =====================================================================
python_file_best_practices:
  description: "Review Python source files for best practices and code quality."
  match:
    include:
      - "**/*.py"
    exclude:
      - "tests/**/*.py"
      - "docs/**/*.py"
  review:
    strategy: individual
    instructions:
      file: .github/prompts/python_review.md

# =====================================================================
# UI Component Contextual Review
# Each component is reviewed individually, but the AI also gets a list
# of all other changed files to spot if a component's API changed
# without the consumers being updated.
# =====================================================================
ui_component_review:
  description: "Review React components for accessibility and prop-type safety."
  match:
    include:
      - "src/components/**/*.tsx"
  review:
    strategy: individual
    additional_context:
      all_changed_filenames: true
    instructions: |
      Review this React component for accessibility and prop-type safety.
      Check the changed filenames list to see if the consumer of this component
      was also updated if you notice breaking API changes.

# =====================================================================
# Database Migration Batch Review
# All changed migration files are reviewed together so the agent can
# check for sequence conflicts and overall migration safety.
# =====================================================================
db_migration_safety:
  description: "Check database migrations for conflicts, destructive ops, and ordering."
  match:
    include:
      - "alembic/versions/*.py"
  review:
    strategy: matches_together
    agent:
      claude: "db-expert"
    instructions: |
      Review these database migrations together.
      Ensure there are no conflicting locks, no destructive
      drops without backups, and that the sequence IDs are ordered correctly.

# =====================================================================
# Version Synchronization Check
# If any version file changes, all three are reviewed together —
# including unchanged ones — to verify version strings match.
# =====================================================================
versions_in_sync:
  description: "Ensure version numbers stay in sync across release files."
  match:
    include:
      - "CHANGELOG.md"
      - "pyproject.toml"
      - "uv.lock"
  review:
    strategy: matches_together
    additional_context:
      unchanged_matching_files: true
    instructions: "Make sure the version number is exactly the same across all three of these files."

# =====================================================================
# Global Security Audit
# Tripwire: if anything in auth or config is touched, ALL changed files
# in the branch get a security review.
# =====================================================================
pr_security_review:
  description: "Security audit triggered by auth or config changes."
  match:
    include:
      - "src/auth/**/*.py"
      - "config/*"
    exclude:
      - "config/*.dev.yaml"
  review:
    strategy: all_changed_files
    agent:
      claude: "security-expert"
    instructions: |
      A change was detected in the authentication module or core config.
      Review all the changed files in this changeset for potential security
      regressions, leaked secrets, or broken authorization logic.

# =====================================================================
# API Route Authorization Check
# Each route file is reviewed individually with a security persona.
# =====================================================================
api_route_auth_check:
  description: "Verify API routes have proper auth middleware and RBAC scopes."
  match:
    include:
      - "src/routes/**/*.ts"
  review:
    strategy: individual
    agent:
      claude: "security-expert"
    instructions: |
      Verify that all exported API routes in this file are protected by
      the `requireAuth` middleware unless explicitly decorated with `@Public`.
      Check for proper role-based access control (RBAC) scopes.

# =====================================================================
# Dockerfile Optimization
# Each container config is reviewed individually for best practices.
# =====================================================================
dockerfile_optimization:
  description: "Check container configs for build optimization and security."
  match:
    include:
      - "**/Dockerfile"
      - "docker-compose*.yml"
  review:
    strategy: individual
    agent:
      claude: "devops-engineer"
    instructions: |
      Review this container configuration. Ensure multi-stage builds are used
      where appropriate, layers are optimized for caching, dependencies are
      pinned, and the default execution user is not root.

# =====================================================================
# CI/CD Pipeline Audit
# All matched workflow files are reviewed together for consistency.
# =====================================================================
cicd_pipeline_audit:
  description: "Audit CI/CD workflows for secret leaks and pinned actions."
  match:
    include:
      - ".github/workflows/*.yml"
  review:
    strategy: matches_together
    agent:
      claude: "devops-engineer"
    instructions: |
      Review these CI/CD workflows. Verify that no secrets are being echoed
      to the console, third-party actions are pinned to a specific commit SHA,
      and deployment environments require manual approval.

# =====================================================================
# Documentation Consistency Check
# Matched docs are reviewed together for broken links and tone.
# =====================================================================
docs_consistency_check:
  description: "Check documentation for consistent tone, broken links, and syntax."
  match:
    include:
      - "docs/**/*.md"
  review:
    strategy: matches_together
    instructions: |
      Review these documentation files. Ensure the tone is consistent,
      check for any broken relative links between these documents, and
      verify that code blocks have language tags for syntax highlighting.

# =====================================================================
# GraphQL Schema Evolution
# Schema files reviewed together, with a list of all other changed
# files so the agent can check if deprecated fields were removed
# before frontend clients stopped using them.
# =====================================================================
graphql_schema_evolution:
  description: "Flag breaking GraphQL schema changes and verify frontend updates."
  match:
    include:
      - "schema/**/*.graphql"
  review:
    strategy: matches_together
    additional_context:
      all_changed_filenames: true
    instructions: |
      Review these GraphQL schema changes. Flag any breaking changes
      (e.g., removing a field, changing a type). If there are breaking changes,
      check the list of changed filenames to ensure the corresponding frontend
      queries were also updated.
```

## Glob Pattern Reference

Patterns follow standard glob syntax, evaluated relative to the `.deepreview` file's directory:

| Pattern | Matches | Does not match |
|---------|---------|----------------|
| `**/*.py` | `app.py`, `src/lib.py`, `deep/nested/file.py` | `app.ts` |
| `*.py` | `app.py` | `src/app.py` (not recursive) |
| `src/components/**/*.tsx` | `src/components/Button.tsx`, `src/components/ui/Card.tsx` | `src/pages/Home.tsx` |
| `config/*` | `config/settings.yaml` | `config/deep/nested.yaml` |
| `**/Dockerfile` | `Dockerfile`, `services/api/Dockerfile` | `Dockerfile.dev` |
| `CHANGELOG.md` | `CHANGELOG.md` | `docs/CHANGELOG.md` |
