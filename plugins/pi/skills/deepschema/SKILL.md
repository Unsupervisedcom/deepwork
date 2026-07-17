---
name: deepschema
description: "Create and manage DeepSchemas with validation and review generation"
---

# DeepSchema

DeepSchemas define rich schemas for files in your project. They provide:

- Automatic write-time validation when Pi write/edit tools modify matching files
- Review generation during `/review` and workflow quality gates
- RFC 2119 requirements for semantic rules

## Two Types

### Named Schemas

Named schemas live in `.deepwork/schemas/<name>/` and match files via glob patterns.

```text
.deepwork/schemas/api_endpoint/
  deepschema.yml
  endpoint.schema.json
  examples/
  references/
```

### Anonymous Schemas

Anonymous schemas sit next to a one-off target file:

```text
src/config.yml
.deepschema.config.yml.yml
```

## Creating a Named Schema

1. Create `.deepwork/schemas/<name>/`.
2. Create `deepschema.yml`:

```yaml
summary: Short description of this file type
instructions: |
  Guidelines for creating and modifying files of this type.

matchers:
  - "**/*.config.yml"

requirements:
  no-secrets: "Config files MUST NOT contain secrets or credentials."

json_schema_path: "config.schema.json"
verification_bash_command:
  - "yamllint -d relaxed"
```

3. Call `get_named_schemas` to verify discovery.

## JSON Schema First

Put every structural constraint that can be expressed exactly in JSON Schema or `verification_bash_command`. Use requirements only for semantic rules that need judgment or cross-file context.

Use JSON Schema for validity, types, required fields, property names, enums, patterns, array constraints, numeric ranges, and conditionals.

Use requirements for meaning, cross-file concerns, behavioral gotchas, and design guidance.

## MCP Tools

- `get_named_schemas` - list discovered named schemas

If direct MCP tools are not visible, use the `mcp` proxy tool and search for `get_named_schemas`.
