---
name: deepreviews
description: "Reference documentation for DeepWork Reviews — automated code review rules using .deepreview configs and DeepSchema-generated rules"
---

# DeepWork Reviews — How It Works

This is a reference skill. Read it to understand the DeepWork Reviews system before running or configuring reviews.

## Overview

DeepWork Reviews lets you define automated code review policies using `.deepreview` config files placed anywhere in your project. When a review runs, it detects which files changed on your branch, matches them against rules, and dispatches parallel review agents — each with focused instructions and only the files it needs.

Reviews are triggered in two ways:
1. **On-demand** via the `/review` skill — runs all matching rules against your branch's changes
2. **During workflows** via quality gates — `finished_step` automatically runs reviews on step outputs

## .deepreview Config Files

A `.deepreview` file is YAML containing one or more named rules. Each rule has a `match` section (what files to trigger on) and a `review` section (how to review them).

### Placement

`.deepreview` files work like `.gitignore` — glob patterns match relative to the file's directory. Place them close to the code they govern:

```
project/
├── .deepreview              # Project-wide rules
├── src/
│   ├── .deepreview          # Rules scoped to src/
│   └── auth/
│       └── .deepreview      # Rules scoped to src/auth/
```

### Rule Structure

```yaml
rule_name:
  description: "Short description"        # Required, under 256 chars
  match:
    include:
      - "glob/pattern/**/*.ext"           # Required, at least one
    exclude:
      - "pattern/to/skip/**"              # Optional
  review:
    strategy: individual                  # Required: individual | matches_together | all_changed_files
    instructions: |                       # Required: inline text or file reference
      Review this file for ...
    agent:                                # Optional: platform-specific agent persona
      claude: "security-expert"
    precomputed_info_for_reviewer_bash_command: .deepwork/review/gather_context.sh  # Optional
    additional_context:                   # Optional
      all_changed_filenames: true         # Include all changed files list
      unchanged_matching_files: true      # Include unchanged files matching the pattern
```

## Review Strategies

| Strategy | Behavior | Best for |
|----------|----------|----------|
| `individual` | One review per matched file | Per-file linting, style checks |
| `matches_together` | All matched files in one review | Cross-file consistency, migration safety |
| `all_changed_files` | If any file matches, reviewer sees ALL changed files | Security audits, broad impact analysis |

## Instructions

Instructions tell the reviewer what to check. They can be inline or reference an external file:

```yaml
# Inline
instructions: "Check for proper error handling."

# File reference (resolved relative to .deepreview location)
instructions:
  file: .deepwork/review/python_review.md
```

Reusable instruction files should live in `.deepwork/review/`.

## How Reviews Run

1. DeepWork discovers all `.deepreview` files in the project
2. It diffs the current branch to find changed files (committed, staged, unstaged, and untracked)
3. Changed files are matched against rule patterns
4. Each match generates a self-contained instruction file in `.deepwork/tmp/review_instructions/`
5. The agent dispatches parallel review sub-agents, one per task

Deleted files are excluded — there's nothing to review.

## DeepSchema-Generated Reviews

DeepSchemas automatically generate synthetic review rules. When a file matches a DeepSchema with requirements, the review pipeline creates a rule that checks those requirements during `/review` and workflow quality gates. No `.deepreview` file is needed — the DeepSchema's `requirements` field drives the review.

This means requirements defined in a DeepSchema are enforced in two places:
- **Write-time**: validation runs when the file is written or edited
- **Review-time**: a generated review rule checks compliance during `/review`

## Workflow Quality Gates

During DeepWork workflows, `finished_step` triggers reviews on step outputs. These come from three sources:

1. **Step output reviews** — `review` blocks defined on step outputs in `job.yml`
2. **Step argument reviews** — default `review` blocks on `step_arguments` in `job.yml`
3. **`.deepreview` rules and DeepSchema rules** — any rules whose patterns match the output files

All three run automatically. If any review fails, `finished_step` returns `needs_work` with feedback.

## Additional Context Flags

- `all_changed_filenames: true` — gives the reviewer a list of every changed file, even those outside this rule's scope. Useful for spotting related changes.
- `unchanged_matching_files: true` — includes files matching the pattern that weren't changed. Useful for sync checks (e.g., "are all version files still in sync?").

## Precomputed Context

The `precomputed_info_for_reviewer_bash_command` field runs a shell command before the review and injects its stdout into the instruction file as a "Precomputed Context" section. This eliminates the need for the reviewer agent to run many tool calls to gather context.

```yaml
review:
  strategy: all_changed_files
  precomputed_info_for_reviewer_bash_command: .deepwork/requirements_traceability_info.sh
  instructions: |
    Review changed files for requirements traceability...
```

Behavior:
- The command path is resolved relative to the `.deepreview` file's directory
- The command runs from the project root with a 60-second timeout
- If the command fails or times out, an error message is injected instead — the review pipeline does not crash
- When multiple rules have precompute commands, all unique commands run in parallel

## Agent Personas

The optional `agent` field assigns a specialized persona to the reviewer:

```yaml
agent:
  claude: "security-expert"
```

If omitted, the default agent handles the review.

## Changed File Detection

All detection is local (no remote fetches). Included: committed branch changes, staged changes, unstaged modifications, untracked files. Excluded: deleted files. You can override detection by passing explicit files.

## Key Skills

- `/review` — Run reviews on the current branch
- `/configure_reviews` — Create or modify `.deepreview` rules
- `/deepschema` — Create DeepSchemas that auto-generate review rules
