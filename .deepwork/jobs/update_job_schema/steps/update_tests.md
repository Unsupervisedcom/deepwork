# Update Unit and Integration Tests

## Objective

Update test files to cover new/modified schema fields: add new test cases, update existing tests that reference changed structure, and ensure the full test suite passes.

## Task

Tests validate that the schema, parser, MCP layer, and validation logic all work correctly. After a schema change, tests need updating to cover the new fields and ensure no regressions.

### Process

1. **Read the change summary**, the updated parser, and MCP schemas to understand the new code

2. **Identify affected test files**
   - `tests/unit/test_parser.py` — parser and dataclass tests
   - `tests/unit/test_validation.py` — schema validation tests
   - `tests/unit/mcp/test_schemas.py` — MCP Pydantic model tests
   - `tests/unit/mcp/test_tools.py` — MCP tool logic tests
   - `tests/unit/mcp/test_state.py` — workflow state management tests
   - `tests/unit/mcp/test_quality_gate.py` — quality review tests
   - `tests/unit/mcp/test_async_interface.py` — async interface tests
   - `tests/integration/test_install_flow.py` — install flow tests
   - There may be additional test files — always check with glob

3. **Update test_parser.py**
   - Add tests for new dataclass fields
   - Test parsing of the new field from YAML
   - Test default values for optional fields
   - Test validation errors for invalid values
   - Update existing test fixtures/assertions if the change modified existing behavior

4. **Update test_validation.py**
   - Add tests that validate the new schema field
   - Test valid values pass validation
   - Test invalid values fail validation
   - Update the `complex_job` fixture used in validation tests if needed

5. **Update MCP test files** (if MCP schemas changed)
   - Update test_schemas.py for new Pydantic model fields
   - Update test_tools.py if tool logic changed
   - Update test_state.py if workflow state handling changed

6. **Run the test suite**
   - Run `uv run pytest tests/` to verify all tests pass
   - Fix any failures from the schema change
   - Do NOT delete tests that fail — fix them to work with the new schema

## Output Format

### test_files

All updated test files. Each should have new test cases, pass against the updated code, and not have deleted tests.

**Example — test patterns for a new optional `timeout` field:**

Parser test (test_parser.py):
```python
def test_step_timeout_parsed():
    """Test that timeout field is parsed from step data."""
    step = make_step({"id": "s1", "timeout": 300, ...})
    assert step.timeout == 300

def test_step_timeout_defaults_to_none():
    """Test that timeout defaults to None when not specified."""
    step = make_step({"id": "s1", ...})  # No timeout field
    assert step.timeout is None
```

Validation test (test_validation.py):
```python
def test_timeout_invalid_type():
    """Test that non-integer timeout fails validation."""
    job_data = make_valid_job()
    job_data["steps"][0]["timeout"] = "not_a_number"
    with pytest.raises(ValidationError):
        validate_against_schema(job_data, JOB_SCHEMA)
```

**Common mistake to avoid**: Only testing the happy path. Always include tests for:
- Valid values (field present and correct)
- Default behavior (field absent)
- Invalid values (wrong type, out of range, etc.)

## Quality Criteria

- New schema fields have dedicated test cases in test_parser.py and test_validation.py
- Tests cover both valid and invalid values for new fields
- Existing tests are updated (not deleted) to work with the schema change
- The full test suite passes: `uv run pytest tests/`
- If MCP schemas changed, MCP test files are updated accordingly
## Context

Tests are the safety net that catches bugs before they reach users. A schema change that isn't properly tested will eventually cause hard-to-debug failures. The test suite should provide confidence that the change works correctly across all layers.
