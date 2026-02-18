---
name: "Job YAML Schema and Validation"
keywords:
  - job.yml
  - schema
  - validation
  - json schema
  - field ordering
last_updated: "2026-02-18"
---

## Schema Location

The authoritative schema is at `src/deepwork/schemas/job.schema.json` (JSON Schema Draft 7). Job files can reference it via the language server comment:
```yaml
# yaml-language-server: $schema=.deepwork/schemas/job.schema.json
```

## Required Root Fields

`name`, `version`, `summary`, `common_job_info_provided_to_all_steps_at_runtime`, `steps`

## Name Validation

Job names, step IDs, and output names all follow `^[a-z][a-z0-9_]*$` — lowercase letters, digits, and underscores only, starting with a letter.

## Version Format

Semantic versioning: `^\d+\.\d+\.\d+$`

## Step Schema Requirements

Each step must have: `id`, `name`, `description`, `instructions_file`, `outputs`, `dependencies`, `reviews`.

Inputs and hooks are optional.

## Output Spec

Every output must declare `type` (either `file` or `files`), `description`, and `required` (boolean). The `required` field must be explicit — there is no default.

## Review Spec

`run_each` must be either `step` (review once with all outputs) or the name of a specific output. `quality_criteria` is a map of criterion name to statement string.

## Common Gotchas

- Missing `required` on output specs causes schema validation failure
- `run_each` referencing a nonexistent output name won't be caught by schema alone but will fail at runtime
- The `additionalProperties: false` constraint at root and step level means typos in field names produce clear errors
