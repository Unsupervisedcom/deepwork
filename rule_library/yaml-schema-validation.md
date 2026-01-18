---
name: YAML Schema Validation
trigger:
  - "**/*.yml"
  - "**/*.yaml"
action:
  command: python3 rule_library/scripts/validate_yaml_schema.py {file}
  run_for: each_match
compare_to: prompt
---
Validates YAML files against their declared JSON Schema.

This rule triggers on any `.yml` or `.yaml` file that is modified. It looks for
a `$schema` declaration at the top of the file:

```yaml
$schema: https://json-schema.org/draft-07/schema
# or
$schema: ./schemas/my-schema.json
```

## Behavior

- **Pass**: File validates against the declared schema, or no schema is declared
- **Fail**: Returns a blocking JSON response with validation error details

## Example Output

On validation failure:
```json
{
  "status": "fail",
  "file": "config.yaml",
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

The validation script requires:
- Python 3.10+
- `pyyaml` package
- `jsonschema` package

Install with: `pip install pyyaml jsonschema`
