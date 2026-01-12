# Add Hook Capabilities

## Objective

Update the DeepWork job schema and platform adapters to support any new hook events that the new platform provides for slash command definitions.

## Task

Analyze the hooks documentation from the research step and update the codebase to support any new hook capabilities, ensuring consistency across all existing adapters.

### Prerequisites

Read the hooks documentation created in the previous step:
- `doc/platforms/<platform_name>/hooks_system.md`

Also review the existing schema and adapters:
- `src/deepwork/schemas/job_schema.py`
- `src/deepwork/adapters.py`

### Process

1. **Analyze the new platform's hooks**
   - Read `doc/platforms/<platform_name>/hooks_system.md`
   - List all hooks available for slash command definitions
   - Compare with hooks already in `job_schema.py`
   - Identify any NEW hooks not currently supported

2. **Determine if schema changes are needed**
   - If the platform has hooks that DeepWork doesn't currently support, add them
   - If all hooks are already supported, document this finding
   - Remember: Only add hooks that are available on slash command definitions

3. **Update job_schema.py (if needed)**
   - Add new hook fields to the step schema
   - Follow existing patterns for hook definitions
   - Add appropriate type hints and documentation
   - Example addition:
     ```python
     # New hook from <platform>
     new_hook_name: Optional[List[HookConfig]] = None
     ```

4. **Update all existing adapters**
   - Open `src/deepwork/adapters.py`
   - For EACH existing adapter class:
     - Add the new hook field (set to `None` if not supported)
     - This maintains consistency across all adapters
   - Document why each adapter does or doesn't support the hook

5. **Validate the changes**
   - Run Python syntax check: `python -m py_compile src/deepwork/schemas/job_schema.py`
   - Run Python syntax check: `python -m py_compile src/deepwork/adapters.py`
   - Ensure no import errors

6. **Document the decision**
   - If no new hooks were added, add a comment explaining why
   - If new hooks were added, ensure they're documented in the schema

## Output Format

### job_schema.py

Location: `src/deepwork/schemas/job_schema.py`

If new hooks are added:
```python
@dataclass
class StepDefinition:
    # ... existing fields ...

    # New hook from <platform_name> - [description of what it does]
    new_hook_name: Optional[List[HookConfig]] = None
```

### adapters.py

Location: `src/deepwork/adapters.py`

For each existing adapter, add the new hook field:
```python
class ExistingPlatformAdapter(PlatformAdapter):
    # ... existing code ...

    def get_hook_support(self) -> dict:
        return {
            # ... existing hooks ...
            "new_hook_name": None,  # Not supported by this platform
        }
```

Or if no changes are needed, add a documentation comment:
```python
# NOTE: <platform_name> hooks reviewed on YYYY-MM-DD
# No new hooks to add - all <platform_name> command hooks are already
# supported by the existing schema (stop_hooks covers their validation pattern)
```

## Quality Criteria

- Hooks documentation from research step has been reviewed
- If new hooks exist:
  - Added to `src/deepwork/schemas/job_schema.py` with proper typing
  - ALL existing adapters updated in `src/deepwork/adapters.py`
  - Each adapter indicates support level (implemented, None, or partial)
- If no new hooks needed:
  - Decision documented with a comment explaining the analysis
- Only hooks available on slash command definitions are considered
- `job_schema.py` has no syntax errors (verified with py_compile)
- `adapters.py` has no syntax errors (verified with py_compile)
- All adapters have consistent hook fields (same fields across all adapters)
- When all criteria are met, include `<promise>QUALITY_COMPLETE</promise>` in your response

## Context

DeepWork supports multiple AI platforms, and each platform may have different capabilities for hooks within command definitions. The schema defines what hooks CAN exist, while adapters define what each platform actually SUPPORTS.

This separation allows:
- Job definitions to use any hook (the schema is the superset)
- Platform-specific generation to only use supported hooks (adapters filter)
- Future platforms to add new hooks without breaking existing ones

Maintaining consistency is critical - all adapters must have the same hook fields, even if they don't support them (use `None` for unsupported).

## Common Hook Types

For reference, here are common hook patterns across platforms:

| Hook Type | Purpose | Example Platforms |
|-----------|---------|-------------------|
| `stop_hooks` | Quality validation loops | Claude Code |
| `pre_hooks` | Run before command | Various |
| `post_hooks` | Run after command | Various |
| `validation_hooks` | Validate inputs/outputs | Various |

When you find a new hook type, consider whether it maps to an existing pattern or is genuinely new functionality.
