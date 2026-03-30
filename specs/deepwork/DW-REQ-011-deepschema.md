# DW-REQ-011: DeepSchema System

The DeepSchema system provides rich, file-level schemas with automatic validation on writes and synthetic review rule generation.

## DW-REQ-011.1: Schema Types

1. The system MUST support two schema types: **named** and **anonymous**.
2. Named schemas MUST be directories containing a `deepschema.yml` manifest, located under a schema folder.
3. Anonymous schemas MUST be single files named `.deepschema.<filename>.yml`, placed alongside the target file.

## DW-REQ-011.2: Schema Configuration

1. The `deepschema.yml` manifest MUST support the following fields: `summary`, `instructions`, `matchers`, `requirements`, `parent_deep_schemas`, `json_schema_path`, `verification_bash_command`, `examples`, `references`.
2. All fields MUST be optional — an empty schema is valid.
3. The manifest MUST be validated against the DeepSchema JSON Schema (`deepschema_schema.json`).
4. The `requirements` field MUST be a mapping of requirement names to RFC 2119 requirement descriptions.
5. The `matchers` field MUST be an array of glob patterns.
6. The `json_schema_path` field MUST be a relative path from the schema directory to a JSON Schema file.
7. The `verification_bash_command` field MUST be an array of shell command strings.
8. The `parent_deep_schemas` field MUST be an array of named schema names to inherit from.

## DW-REQ-011.3: Named Schema Discovery

1. Named schemas MUST be discovered from multiple directories in priority order: project-local (`.deepwork/schemas/`), standard (`standard_schemas/`), and `DEEPWORK_ADDITIONAL_SCHEMAS_FOLDERS` env var (colon-delimited).
2. If the same schema name appears in multiple sources, the first source MUST win.
3. Each source directory MUST be scanned for subdirectories containing `deepschema.yml`.

## DW-REQ-011.4: Anonymous Schema Discovery

1. Anonymous schemas MUST be found by walking the project tree for files matching `.deepschema.<filename>.yml`.
2. Standard skip directories (`.git`, `node_modules`, `__pycache__`, `.venv`, etc.) MUST be excluded from the walk.

## DW-REQ-011.5: Schema Inheritance

1. When a schema lists `parent_deep_schemas`, the resolver MUST merge parent requirements into the child.
2. Child requirements MUST override parent requirements with the same key.
3. If a child has no `json_schema_path`, it MUST inherit the parent's.
4. `verification_bash_command` entries from parents MUST be appended to the child's list.
5. Circular references in `parent_deep_schemas` MUST be detected and reported as errors.

## DW-REQ-011.6: File Matching

1. A file MUST match a named schema if any of the schema's `matchers` glob patterns match the file's project-relative path.
2. A file MUST match an anonymous schema if a `.deepschema.<filename>.yml` file exists alongside it.
3. The `get_schemas_for_file_fast()` function MUST avoid full tree walks — it MUST only scan named schema folders and check for the anonymous schema file at O(1).

## DW-REQ-011.7: Write Hook (PostToolUse)

1. The write hook MUST fire on PostToolUse events for Write and Edit tools.
2. For each applicable schema, the hook MUST inject a conformance note: "Note: this file must conform to the DeepSchema at `<path>`".
3. If `json_schema_path` is set, the hook MUST validate the written file against the JSON Schema. YAML files (`.yml`/`.yaml`) MUST be parsed as YAML before validation.
4. If `verification_bash_command` is set, the hook MUST execute each command with the file path as `$1`, with a 30-second timeout.
5. Validation failures MUST be reported via `hookSpecificOutput.additionalContext` so the agent can act on them.
6. The hook MUST NOT use `systemMessage` for validation output — that route is user-visible only.

## DW-REQ-011.8: Review Bridge

1. Each discovered schema with requirements MUST generate a synthetic `ReviewRule`.
2. Review rule names MUST follow the pattern `"<name> DeepSchema Compliance"`.
3. Named schema reviews MUST include the schema's summary, instructions, and requirements in the review prompt.
4. Anonymous schema reviews MUST include only the requirements.
5. All generated reviews MUST use the `"individual"` strategy (one file at a time).
6. Generated reviews MUST be included in both `/review` runs and workflow quality gate checks.
7. Review instructions MUST specify RFC 2119 severity logic: reviewers MUST fail any violation of a MUST requirement, MUST fail any SHOULD requirement that could easily be followed but is not, SHOULD give feedback without failing on other applicable items, and MUST ignore requirements that are not applicable.

## DW-REQ-011.9: MCP Tool — get_named_schemas

1. The `get_named_schemas` MCP tool MUST return all discovered named schemas.
2. Each entry MUST include `name`, `summary`, and `matchers` fields.
3. Schemas that fail to parse MUST still appear in the results with an error summary instead of a real summary.
