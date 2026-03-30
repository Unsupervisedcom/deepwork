# Update JSON Schema

## Objective

Edit `src/deepwork/schemas/job.schema.json` — the single source of truth for all job.yml file structure — to implement the desired schema change.

## Task

Apply the requested change to the JSON Schema file. This is always the first step because every other file in the codebase derives its understanding of job.yml structure from this schema.

### Process

1. **Understand the change**
   - Read the `change_description` and `motivation` inputs
   - Ask structured questions if the change is ambiguous (e.g., "Should this field be required or optional?", "What type should this field be?", "Should it have a default value?")

2. **Read the current schema**
   - Read `src/deepwork/schemas/job.schema.json` in full
   - Understand the existing structure, `$defs`, and how fields relate to each other

3. **Plan the change**
   - Identify exactly which section(s) of the schema need modification
   - Determine if new `$defs` entries are needed
   - Consider whether the change is backwards-compatible (new optional fields) or breaking (new required fields, removed fields, changed types)
   - If breaking, plan what existing files will need to change

4. **Apply the change**
   - Edit the JSON Schema file
   - Follow existing patterns for field definitions (look at peer fields for style)
   - Use `$ref` for reusable sub-schemas
   - Add `description` fields for new properties to make the schema self-documenting

5. **Write the change summary**
   - Create `.deepwork/tmp/schema_change_summary.md` documenting what changed
   - This file is critical — every subsequent step reads it to know what to update

## Output Format

### schema_file

The updated `src/deepwork/schemas/job.schema.json`. Must be valid JSON Schema Draft 7.

### change_summary

A markdown file at `.deepwork/tmp/schema_change_summary.md`:

```markdown
# Schema Change Summary

## Change Description
[What was changed in plain English]

## Motivation
[Why this change was made]

## Breaking Change
[Yes/No — and if yes, what existing files will need to change]

## Fields Modified
- **[field_path]**: [description of change]
  - Type: [type]
  - Required: [yes/no]
  - Default: [value, if any]

## Impact on Existing Files
- [ ] Parser dataclasses need: [what]
- [ ] MCP schemas need: [what]
- [ ] Fixture job.yml files need: [what]
- [ ] Standard/library jobs need: [what]
- [ ] Tests need: [what]
- [ ] Docs need: [what]
- [ ] Repair workflow needs: [migration logic description, or "no migration needed"]
```

## Quality Criteria

- The schema file is valid JSON Schema Draft 7
- New fields follow existing naming conventions (snake_case)
- If backwards-compatible, new fields are optional with sensible defaults
- If breaking, the change summary clearly documents what needs to change
- The change summary has a complete impact checklist for all downstream files
- `$ref` is used for reusable sub-schemas rather than inline duplication
## Context

The JSON Schema at `src/deepwork/schemas/job.schema.json` is the single source of truth for job.yml structure. It is used by:
- `src/deepwork/utils/validation.py` for schema validation via jsonschema
- `src/deepwork/schemas/job_schema.py` which loads and exports it as `JOB_SCHEMA`
- `src/deepwork/core/parser.py` which parses job.yml into dataclasses
- The installed copy at `.deepwork/schemas/job.schema.json`

Historical pattern: schema changes typically touch 20-40 files across the codebase. The change summary you write here is the roadmap for all subsequent steps.
