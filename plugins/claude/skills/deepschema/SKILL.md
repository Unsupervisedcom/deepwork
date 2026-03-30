---
name: deepschema
description: "Create and manage DeepSchemas — rich file-level schemas with automatic validation and review generation"
---

# DeepSchema

DeepSchemas define rich schemas for files in your project. They provide:

- **Automatic write-time validation** — when you write or edit a file, applicable schemas are checked immediately and errors are reported inline
- **Review generation** — schemas automatically generate review rules that run during `/review` and workflow quality gates
- **RFC 2119 requirements** — requirements use MUST/SHOULD/MAY keywords to control enforcement severity

## Two Types of DeepSchemas

### Named Schemas

Named schemas live in `.deepwork/schemas/<name>/` and match files via glob patterns. Use these for file types that appear throughout your project.

```
.deepwork/schemas/api_endpoint/
  deepschema.yml          # Manifest with requirements, matchers, etc.
  endpoint.schema.json    # Optional JSON Schema for structural validation
  examples/               # Optional example files
  references/             # Optional reference docs
```

### Anonymous Schemas

Anonymous schemas are single files placed alongside the file they apply to. Use these for one-off requirements on a specific file.

```
src/config.yml                    # The file
.deepschema.config.yml.yml        # Its anonymous schema
```

The naming convention is `.deepschema.<filename>.yml`.

## Creating a Named Schema

1. Create the directory: `.deepwork/schemas/<name>/`
2. Create `deepschema.yml` inside it:

```yaml
summary: Short description of this file type
instructions: |
  Guidelines for creating and modifying files of this type.

matchers:
  - "**/*.config.yml"
  - "src/configs/**/*.json"

requirements:
  has-version: "Every config file MUST include a version field."
  documented-fields: "All fields SHOULD have inline comments explaining their purpose."
  no-secrets: "Config files MUST NOT contain secrets or credentials."

# Optional: structural validation
json_schema_path: "config.schema.json"

# Optional: custom validation commands (file path passed as $1)
verification_bash_command:
  - "yamllint -d relaxed"
```

3. Call `get_named_schemas` to verify your schema is discovered.

## Creating an Anonymous Schema

Place a `.deepschema.<filename>.yml` file next to the target file:

```yaml
requirements:
  api-key-rotated: "The API key MUST be rotated every 90 days."
  format-valid: "The file MUST be valid YAML."

# Reference a named schema for shared requirements
parent_deep_schemas:
  - api_endpoint
```

## Schema Fields Reference

| Field | Description |
|-------|-------------|
| `summary` | Brief description for discoverability |
| `instructions` | Guidelines for working with these files |
| `matchers` | Glob patterns this schema applies to (named schemas) |
| `requirements` | Key-value pairs of RFC 2119 requirements |
| `parent_deep_schemas` | Named schemas to inherit requirements from |
| `json_schema_path` | Relative path to a JSON Schema file |
| `verification_bash_command` | Shell commands to validate the file (receives path as `$1`) |
| `examples` | Array of `{path, description}` for example files |
| `references` | Array of `{path, description}` or `{url, description}` for reference docs |

## How Validation Works

When you write or edit a file:
1. DeepWork finds all applicable schemas (named schemas with matching globs + any anonymous schema for the file)
2. A conformance note is injected listing applicable schemas
3. `json_schema_path` validation runs automatically
4. `verification_bash_command` commands run with the file path as `$1`
5. Failures are reported as errors the agent must fix

During `/review` and workflow quality gates, each schema generates a review rule that checks all requirements.

## Discovery Sources

Named schemas are loaded from multiple directories in priority order (first match wins):

1. `.deepwork/schemas/` — project-local schemas
2. DeepWork built-in standard schemas (e.g., `job_yml`, `deepschema`)
3. `DEEPWORK_ADDITIONAL_SCHEMAS_FOLDERS` env var — colon-delimited extra directories

## MCP Tools

- `get_named_schemas` — list all discovered named schemas with their names, summaries, and matchers
