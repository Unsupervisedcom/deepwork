---
name: Schema Validation
trigger:
  - "**/*.yml"
  - "**/*.yaml"
  - "**/*.json"
action:
  command: python3 .deepwork/rules/json_validation/scripts/validate_schema.py {file}
  run_for: each_match
compare_to: prompt
---
Validates YAML and JSON files against their declared JSON Schema.

This rule triggers on any `.yml`, `.yaml`, or `.json` file that is modified. It
performs a quick text scan for a `$schema` declaration before doing any parsing.
Only files with a schema reference are fully parsed and validated.

## Schema Declaration

**YAML files:**
```yaml
$schema: https://json-schema.org/draft-07/schema
# or
$schema: ./schemas/my-schema.json
```

**JSON files:**
```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "name": "example"
}
```

## Behavior

1. **Quick scan**: Searches first 4KB for `$schema` pattern (no parsing)
2. **Skip if none**: Files without schema declaration pass immediately
3. **Full parse**: Only files with schema are fully parsed
4. **Validate**: Content validated against the declared schema

### Exit Codes

- **0 (pass)**: File validates against schema, or no schema declared
- **1 (fail)**: Validation failed - returns blocking JSON with error details
- **2 (error)**: Could not load schema or parse file

## Example Output

On validation failure:
```json
{
  "status": "fail",
  "file": "config.json",
  "schema": "https://example.com/schemas/config.json",
  "error_count": 2,
  "errors": [
    {
      "message": "'name' is a required property",
      "path": "/",
      "schema_path": "/required"
    },
    {
      "message": "42 is not of type 'string'",
      "path": "/version",
      "schema_path": "/properties/version/type",
      "value": 42
    }
  ]
}
```

## Requirements

- Python 3.10+
- `jsonschema` package (required)
- `pyyaml` package (required for YAML files)

Install with: `pip install jsonschema pyyaml`
