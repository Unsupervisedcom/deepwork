---
name: Hooks and Validation
keywords:
  - hooks
  - validation
  - quality
  - lifecycle
last_updated: 2025-02-01
---

# Hooks and Validation

How to use lifecycle hooks for quality validation in DeepWork workflows.

## Lifecycle Hook Events

DeepWork supports three generic hook events:

| Event | When it fires | Use case |
|-------|---------------|----------|
| `after_agent` | After agent finishes responding | Quality validation, output verification |
| `before_tool` | Before agent uses a tool | Pre-tool checks, validation |
| `before_prompt` | When user submits a prompt | Session setup, context loading |

## Platform Mapping

Hooks are mapped to platform-specific event names:

| Generic | Claude Code |
|---------|-------------|
| `after_agent` | `Stop`, `SubagentStop` |
| `before_tool` | `PreToolUse` |
| `before_prompt` | `UserPromptSubmit` |

Note: Gemini CLI does not support skill-level hooks (only global hooks).

## Hook Action Types

### Inline Prompt

Best for simple validation criteria:

```yaml
hooks:
  after_agent:
    - prompt: |
        Verify the output meets these criteria:
        1. Contains at least 5 competitors
        2. Each has a description
        3. Sources are cited
```

**Important**: Prompt hooks are currently parsed but NOT executed by Claude Code.
This is a documented limitation. Use script hooks for actual enforcement.

### Prompt File

For detailed/reusable criteria:

```yaml
hooks:
  after_agent:
    - prompt_file: hooks/quality_check.md
```

The prompt file is read and its content is embedded in the generated skill.
Same limitation applies - parsed but not executed.

### Script Hook

For programmatic validation (actually executed):

```yaml
hooks:
  after_agent:
    - script: hooks/run_tests.sh
```

Scripts are shell scripts that can:
- Run test suites
- Lint output files
- Check for required content
- Validate file formats

Exit code 0 = pass, non-zero = fail.

## Script Hook Example

Create `.deepwork/experts/[expert]/workflows/[workflow]/hooks/validate.sh`:

```bash
#!/bin/bash
# Validate research output

OUTPUT_FILE="research_notes.md"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "ERROR: $OUTPUT_FILE not found"
    exit 1
fi

# Check minimum content
LINES=$(wc -l < "$OUTPUT_FILE")
if [ "$LINES" -lt 50 ]; then
    echo "ERROR: Output has only $LINES lines, expected at least 50"
    exit 1
fi

echo "Validation passed"
exit 0
```

Make it executable:
```bash
chmod +x .deepwork/experts/[expert]/workflows/[workflow]/hooks/validate.sh
```

## Combining Multiple Hooks

```yaml
hooks:
  after_agent:
    - script: hooks/lint.sh
    - script: hooks/run_tests.sh
    - prompt: "Verify documentation is complete"
```

Hooks run in order. Script hooks are executed; prompt hooks are for reference.

## Quality Criteria Alternative

For simple validation, use declarative `quality_criteria` instead of hooks:

```yaml
steps:
  - id: research
    quality_criteria:
      - "**Data Coverage**: Each competitor has at least 3 data points"
      - "**Source Attribution**: All facts are cited"
      - "**Relevance**: All competitors are in the target market"
```

Quality criteria are rendered in the skill with instructions to use a
sub-agent (Haiku model) for review:

1. Agent completes work
2. Spawns sub-agent to review against criteria
3. Fixes any issues identified
4. Repeats until sub-agent confirms all criteria pass

This is the recommended approach for most validation needs - it's more
flexible than scripts and actually works with Claude Code.

## When to Use Each Approach

| Approach | When to use |
|----------|-------------|
| `quality_criteria` | Most cases - subjective quality checks |
| Script hooks | Objective checks (tests, linting, format validation) |
| Prompt hooks | Documentation only (not currently executed) |

## Generated Skill Output

For script hooks, the generated skill includes:

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/experts/expert_name/workflows/workflow_name/hooks/validate.sh"
  SubagentStop:
    - hooks:
        - type: command
          command: ".deepwork/experts/expert_name/workflows/workflow_name/hooks/validate.sh"
```

Both `Stop` and `SubagentStop` are registered so hooks fire for both
the main agent and any sub-agents.
