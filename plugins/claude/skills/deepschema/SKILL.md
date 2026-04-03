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
  # Semantic rules only — structural constraints go in config.schema.json
  documented-fields: "All fields SHOULD have inline comments explaining their purpose."
  no-secrets: "Config files MUST NOT contain secrets or credentials."

# Structural validation — enforce types, required fields, enums, etc. here
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
  no-plaintext-secrets: "Credentials MUST use environment variable references, not literal values."

# Reference a named schema for shared requirements
parent_deep_schemas:
  - api_endpoint
```

## JSON Schema First: Maximize Structural Validation

**The `json_schema_path` file is the primary enforcement mechanism.** Every constraint that _can_ be expressed structurally MUST go in the JSON Schema, not in requirements. Requirements exist only for semantic rules that JSON Schema cannot express.

Put in the JSON Schema (not requirements):
- File format validity (valid JSON, valid YAML)
- Field types (string, number, boolean, array, object)
- Required fields
- Allowed property names (`additionalProperties: false`)
- Enum values and allowed constants
- Array item types and constraints (`minItems`, `uniqueItems`)
- Numeric ranges (`minimum`, `maximum`)
- String patterns (`pattern`, `format`)
- Conditional field presence (`if`/`then` — e.g., "when type is 'http', url is required")
- Nested object shapes and their constraints

Put in requirements (not the JSON Schema):
- Semantic rules about _meaning_ ("secrets MUST NOT appear in shared settings")
- Cross-file concerns ("this field MUST reference an existing named schema")
- Behavioral gotchas ("sandbox paths use different prefix semantics than permission paths")
- Design guidance ("deny rules SHOULD be used for hard security boundaries, not soft preferences")
- Anything requiring judgment or context a machine validator cannot assess

**Build the JSON Schema to be as strict and comprehensive as possible.** Use `additionalProperties: false` to catch typos. Use enums for closed sets. Use `if/then` for conditional requirements. Use `pattern` for string formats. Use `$defs` and `$ref` for reusable types. Use `anyOf` for discriminated unions. Use `uniqueItems`, `minLength`, `minItems` where appropriate. A good JSON Schema catches errors at write time before a reviewer ever sees the file. Requirements that duplicate what the schema already enforces are noise — they dilute the reviewer's attention and risk contradicting the schema.

### Verification Commands for Non-JSON Files

For files that aren't JSON or YAML (markdown, shell scripts, plain text, custom formats), `verification_bash_command` serves the same role as `json_schema_path` — it's the primary structural enforcement mechanism. The same principle applies: anything a command can check exactly MUST go in a verification command, not in requirements.

```yaml
# Example: RFC 2119 requirements files (markdown)
verification_bash_command:
  - "grep -nE '^[0-9]+\\.' \"$1\" | grep -vE 'MUST|SHALL|SHOULD|MAY|REQUIRED|RECOMMENDED|OPTIONAL' | { if read -r line; then echo \"FAIL: Requirement without RFC 2119 keyword: $line\"; exit 1; fi; }"

requirements:
  # Only semantic rules the command can't check
  testability: "Each requirement MUST be specific enough to be verifiable."
```

Commands receive the file path as `$1`, must exit 0 on success and non-zero on failure, and have a 30-second timeout.

### Check SchemaStore for Existing Schemas

Before writing a JSON Schema from scratch, check whether a published schema already exists at [SchemaStore](https://www.schemastore.org/) (`https://json.schemastore.org/<name>.json`). SchemaStore hosts community-maintained schemas for hundreds of config file formats.

If a good schema exists:
1. **Vendor a local copy** into your schema directory (e.g., `claude_settings.schema.json`)
2. **Add a `_source` field** at the top of the file with the original URL and sync date:
   ```json
   {
     "_source": "Vendored from https://json.schemastore.org/example.json. To update: fetch the latest version from that URL and replace this file. Last synced: 2026-04-01."
   }
   ```
3. **Point `json_schema_path`** at the local copy — this avoids network dependencies during validation
4. **Periodically re-fetch** the upstream schema to pick up improvements — the `_source` field tells future maintainers where to look

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
