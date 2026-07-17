---
name: deepreviews
description: "Reference documentation for DeepWork Reviews"
---

# DeepWork Reviews

Reference for `.deepreview` rules and DeepSchema-generated review rules.

## Overview

DeepWork Reviews define automated review policies using `.deepreview` files placed anywhere in a project. A review detects changed files, matches them against rules, and generates focused review tasks.

Reviews run:
- On demand via `/review`
- During workflows via `finished_step` quality gates

## .deepreview Files

A `.deepreview` file is YAML containing named rules. Globs match relative to the file's directory.

```yaml
rule_name:
  description: "Short description"
  match:
    include:
      - "src/**/*.py"
    exclude:
      - "src/generated/**"
  review:
    strategy: individual
    instructions: |
      Review this file for error handling issues.
    reference_files:
      - path: "docs/style_guide.md"
        description: "Style guide"
```

## Strategies

| Strategy | Behavior |
| --- | --- |
| `individual` | One review per matched file |
| `matches_together` | All matched files in one review |
| `all_changed_files` | If any file matches, reviewer sees all changed files |

## Instructions

Instructions can be inline or reference a file:

```yaml
instructions:
  file: .deepwork/review/python_review.md
```

Reusable instructions should live in `.deepwork/review/`.

## DeepSchema Reviews

DeepSchemas automatically generate review rules from their `requirements`. Generated reviews run during `/review` and workflow quality gates.

## Workflow Quality Gates

`finished_step` reviews step outputs from:
- Step output `review` blocks
- Step argument `review` blocks
- `.deepreview` rules and DeepSchema-generated rules

If any review fails, `finished_step` returns `needs_work`.

## Key Skills

- `/review` - run reviews
- `/configure-reviews` - create or modify rules
- `/deepschema` - create DeepSchemas
