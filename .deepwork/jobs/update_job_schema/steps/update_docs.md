# Update Documentation

## Objective

Update all documentation files affected by the schema change, including architecture docs, MCP interface docs, and any other files that reference job.yml structure.

## Task

Documentation must accurately reflect the current schema. Outdated docs cause confusion for both users and AI agents working with DeepWork.

### Process

1. **Read the change summary**
   - Read `.deepwork/tmp/schema_change_summary.md` for what changed

2. **Identify affected documentation**
   - `doc/architecture.md` — comprehensive architecture documentation, references job.yml structure, JobDefinition dataclasses, parsing process
   - `doc/mcp_interface.md` — MCP tool documentation, references job fields through tool descriptions
   - `CLAUDE.md` — project instructions, references standard_jobs structure
   - `README.md` — project overview
   - Search for other files that reference the changed fields using grep

3. **Update architecture.md**
   - Update any sections describing job.yml structure
   - Update JobDefinition dataclass documentation if fields changed
   - Update parsing process descriptions if parsing logic changed
   - Update any example job.yml snippets

4. **Update mcp_interface.md**
   - Update tool response descriptions if MCP schemas changed
   - Update any example responses that include changed fields

5. **Update other docs as needed**
   - Search for references to changed field names across all .md files
   - Update CLAUDE.md if the project structure description needs updating
   - Update README.md if the change affects user-facing workflow descriptions

6. **Verify consistency**
   - Ensure all docs tell the same story about the schema
   - Check that example snippets in docs match the actual schema

### Key Files

- **Architecture doc**: `doc/architecture.md`
- **MCP interface doc**: `doc/mcp_interface.md`
- **Project instructions**: `CLAUDE.md`
- **README**: `README.md`
- **Change summary**: `.deepwork/tmp/schema_change_summary.md`

## Output Format

### doc_files

All updated documentation files. Each should accurately reflect the current schema state.

**Example — updating architecture.md when adding a `timeout` field to steps:**

Before (outdated):
```markdown
### Step Fields
- `id` — Step identifier
- `name` — Human-readable name
- `dependencies` — List of prerequisite step IDs
```

After (updated):
```markdown
### Step Fields
- `id` — Step identifier
- `name` — Human-readable name
- `dependencies` — List of prerequisite step IDs
- `timeout` — Optional maximum execution time in seconds
```

**Common mistake to avoid**: Updating a field description in one section of a doc but missing the same field mentioned in a different section (e.g., updating the "Step Fields" table but missing a YAML example snippet that shows step structure). Search the entire document for references to the changed area.

**Also check**: If the doc contains example YAML snippets showing job.yml structure, update those snippets to include new required fields. Example snippets that don't match the real schema are confusing.

## Quality Criteria

- Architecture doc accurately describes the current schema structure
- MCP interface doc reflects any changes to tool responses
- Example snippets in documentation match the actual schema
- No documentation references removed or renamed fields by old names
- All affected sections are updated (not just the first one found)
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

Documentation is read by both humans and AI agents. The CLAUDE.md and architecture.md files are particularly important because they are loaded into AI agent context when working on this project. Stale documentation here means AI agents will make incorrect assumptions about the codebase.
