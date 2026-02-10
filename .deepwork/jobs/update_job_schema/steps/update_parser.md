# Update Parser and Dataclasses

## Objective

Update `src/deepwork/core/parser.py` to handle the new/modified schema fields, including any needed dataclass changes, parsing logic, and validation. Also update `src/deepwork/schemas/job_schema.py` if the change affects schema loading or exported constants.

## Task

The parser is the runtime representation of job.yml files. It converts raw YAML into typed Python dataclasses that the rest of the codebase uses. Any schema change must be reflected here.

### Process

1. **Read the change summary**
   - Read `.deepwork/tmp/schema_change_summary.md` to understand what changed
   - Identify which dataclasses and parsing functions need updates

2. **Read the current parser**
   - Read `src/deepwork/core/parser.py` in full
   - Understand the existing dataclass hierarchy: `Step`, `OutputSpec`, `StepInput`, `HookAction`, `Review`, `Workflow`, `WorkflowStepEntry`, `JobDefinition`
   - Understand the parsing flow in `parse_job_definition()`

3. **Update dataclasses**
   - Add new fields to the appropriate dataclass(es)
   - Use appropriate Python types (str, bool, list, dict, Optional, etc.)
   - Set defaults for optional fields
   - Follow existing patterns (e.g., how `Optional` fields default to `None`)

4. **Update parsing logic**
   - Modify the parsing code in `parse_job_definition()` or related functions
   - Handle the new field extraction from raw YAML data
   - Add validation logic if needed (e.g., cross-referencing between fields)

5. **Check job_schema.py**
   - Read `src/deepwork/schemas/job_schema.py`
   - If the change adds new enum values or constants that the schema uses, update `LIFECYCLE_HOOK_EVENTS` or add new constants as needed
   - If no changes needed, note this in the output

### Key Files

- **Parser**: `src/deepwork/core/parser.py`
- **Schema loader**: `src/deepwork/schemas/job_schema.py`
- **Change summary**: `.deepwork/tmp/schema_change_summary.md`

## Output Format

### parser_file

The updated `src/deepwork/core/parser.py`. Follow the existing patterns in the file.

**Example — adding an optional `timeout` field to steps:**

Dataclass change:
```python
@dataclass
class Step:
    id: str
    name: str
    # ... existing fields ...
    timeout: Optional[int] = None  # New optional field with None default
```

Parsing logic change (in the step-parsing section of `parse_job_definition`):
```python
timeout = step_data.get("timeout")  # Optional — returns None if missing
```

**Common mistake to avoid**: Don't add step-level fields to `JobDefinition`, or job-level fields to `Step`. Match the schema hierarchy — if the field is under `steps[].properties` in the JSON Schema, it belongs on the `Step` dataclass.

**For required fields**, follow the pattern of raising `ParseError` when missing:
```python
new_field = step_data.get("new_field")
if new_field is None:
    raise ParseError(f"Step '{step_id}' missing required field 'new_field'")
```

### job_schema_py

The updated `src/deepwork/schemas/job_schema.py` (provide the path even if unchanged).

## Quality Criteria

- Every field added/modified in the schema has a corresponding dataclass field
- Parsing logic correctly extracts the new field from raw YAML data
- Optional schema fields have sensible Python defaults (typically `None`)
- Required schema fields raise clear errors when missing
- Validation logic catches invalid values (e.g., bad enum values, invalid cross-references)
- Existing parsing behavior is preserved for all unchanged fields
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

The parser defines the in-memory representation used by everything downstream: the MCP server reads `JobDefinition` objects, the CLI uses them for sync/install, and the skill generator uses them to create slash commands. Getting the dataclasses right here is critical — all subsequent steps depend on this representation.
