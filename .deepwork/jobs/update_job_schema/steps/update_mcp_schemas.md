# Update MCP Schemas

## Objective

Update `src/deepwork/mcp/schemas.py` Pydantic models and `src/deepwork/mcp/tools.py` tool logic to reflect the schema change, ensuring MCP tool responses correctly expose new fields to clients.

## Task

The MCP layer is how external tools (like Claude Code) interact with DeepWork. If the schema change affects what information should be returned by MCP tools (get_workflows, start_workflow, finished_step), the Pydantic models and tool logic must be updated.

### Process

1. **Read the change summary**
   - Read `.deepwork/tmp/schema_change_summary.md` to understand what changed
   - Determine if the change affects MCP tool responses

2. **Read the current MCP schemas**
   - Read `src/deepwork/mcp/schemas.py` — Pydantic models for tool I/O
   - Key models: `JobInfo`, `WorkflowInfo`, `StepInfo`, `StartWorkflowInput`, `FinishedStepInput`, `GetWorkflowsResponse`
   - Read the updated `src/deepwork/core/parser.py` to see the new dataclass fields

3. **Determine what needs updating**
   - Not every schema change affects MCP responses. Ask:
     - Does the new field need to be visible to MCP clients?
     - Does it change how workflows are started or steps are completed?
     - Does it affect the information returned by `get_workflows`?
   - If the change is purely internal (e.g., a validation-only field), MCP schemas may not need changes

4. **Update Pydantic models** (if needed)
   - Add new fields to the appropriate Pydantic model(s)
   - Use `Optional` for fields that may not always be present
   - Match field types to the parser dataclass types

5. **Update tools.py** (if needed)
   - Read `src/deepwork/mcp/tools.py`
   - Update the conversion logic that transforms `JobDefinition` → MCP response models
   - Ensure new fields are correctly mapped from parser dataclasses to Pydantic models

### Key Files

- **MCP schemas**: `src/deepwork/mcp/schemas.py`
- **MCP tools**: `src/deepwork/mcp/tools.py`
- **Parser (for reference)**: `src/deepwork/core/parser.py`
- **Change summary**: `.deepwork/tmp/schema_change_summary.md`

## Output Format

### mcp_schemas_file

The updated `src/deepwork/mcp/schemas.py`. If no changes were needed, provide the unchanged file path.

**Example — adding an optional `timeout` field to StepInfo:**

Pydantic model change in schemas.py:
```python
class StepInfo(BaseModel):
    step_id: str
    # ... existing fields ...
    timeout: Optional[int] = None  # New field exposed to MCP clients
```

**Common mistake to avoid**: Adding a field to the Pydantic model but forgetting to populate it in tools.py. Both files must be updated together.

### mcp_tools_file

The updated `src/deepwork/mcp/tools.py`. If no changes were needed, provide the unchanged file path.

**Example — populating the new field in the conversion logic:**

In tools.py where `Step` dataclass is converted to `StepInfo`:
```python
StepInfo(
    step_id=step.id,
    # ... existing fields ...
    timeout=step.timeout,  # Map from parser dataclass to Pydantic model
)
```

**When NOT to update MCP schemas**: If the new field is purely for internal validation or parsing (e.g., a field that only affects how the parser processes other fields), it doesn't need to be in the MCP response.

## Quality Criteria

- If the schema change adds fields that should be visible to MCP clients, they are present in the Pydantic models
- Field types in Pydantic models match the parser dataclass types
- Conversion logic in tools.py correctly maps new dataclass fields to Pydantic fields
- No existing MCP response fields are broken or removed unintentionally
- The header comment in schemas.py about staying in sync with mcp_interface.md is respected
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

The MCP server is the primary interface for AI agents interacting with DeepWork. The Pydantic models in schemas.py define the contract between the MCP server and its clients. Changes here should be minimal and deliberate — only expose fields that clients actually need.
