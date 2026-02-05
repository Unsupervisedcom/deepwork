# Calling Claude Code in Print Mode

This document covers how to invoke Claude Code as a subprocess using the `--print` flag for non-interactive, programmatic usage.

## Basic Usage

The `--print` (or `-p`) flag runs Claude Code in non-interactive mode, suitable for scripting and subprocess invocation.

### Piping Input

When piping a prompt via stdin, use `-p --` to separate flags from the piped content:

```bash
echo "your prompt here" | claude -p --
```

**Important**: The `--` is required because `-p` expects a prompt argument immediately after it. Without `--`, the next argument is interpreted as the prompt itself.

### Flag Ordering

Flags must come **before** `-p --`. Anything after `--` is treated as part of the prompt:

```bash
# Correct - flags before -p --
echo "say hello" | claude --max-turns 3 -p --

# Wrong - flags after -- become part of the prompt
echo "say hello" | claude -p -- --max-turns 3
```

## Structured Output with JSON Schema

Claude Code supports structured output via the `--json-schema` flag. This constrains the model's response to conform to a specified JSON schema.

### Requirements

To get structured JSON output, you need **all three** flags:
- `--print` - Non-interactive mode
- `--output-format json` - JSON output format
- `--json-schema '<schema>'` - The JSON schema as a **string** (not a filename)

### Example

```bash
echo "say hello" | claude --print --output-format json --json-schema '{"type":"object","properties":{"greeting":{"type":"string"}},"required":["greeting"]}'
```

### Output Format

The output is a JSON object with metadata about the run. The structured output conforming to your schema is in the `structured_output` field:

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 4557,
  "num_turns": 2,
  "result": "",
  "session_id": "ca428892-a13e-4c4c-85df-b29f8ec851a0",
  "total_cost_usd": 0.063,
  "structured_output": {
    "greeting": "Hello! How can I help you today?"
  }
}
```

### Key Insight

The model automatically conforms to the schema **without being told about it in the prompt**. You don't need to instruct the model to output JSON or describe the expected format - the `--json-schema` flag handles this behind the scenes.

## Common Flags for Print Mode

| Flag | Description |
|------|-------------|
| `--print` / `-p` | Non-interactive mode |
| `--output-format <format>` | Output format: `text` (default), `json`, or `stream-json` |
| `--json-schema <schema>` | JSON schema string for structured output validation |
| `--max-turns <n>` | Maximum number of agentic turns |
| `--input-format <format>` | Input format: `text` (default) or `stream-json` |
| `--include-partial-messages` | Include partial message chunks (with `stream-json`) |

## Gotchas

1. **`--json-schema` takes a string, not a filename** - Pass the actual JSON schema content, not a path to a file.

2. **`--output-format json` only works with `--print`** - These flags are designed for non-interactive/programmatic use.

3. **Max turns matters** - If you set `--max-turns 1` and the model needs to use tools, it may hit the limit before producing output. Use a reasonable number of turns.

4. **The `--` separator is critical** - When piping input with `-p`, always use `--` to mark the end of flags.

## Full Example

```bash
# Define a schema for listing files
SCHEMA='{"type":"object","properties":{"files":{"type":"array","items":{"type":"string"}},"count":{"type":"integer"}},"required":["files","count"]}'

# Run with structured output
echo "List Python files in src/" | claude --print --output-format json --json-schema "$SCHEMA" --max-turns 5

# Parse the structured_output field with jq
echo "List Python files in src/" | claude --print --output-format json --json-schema "$SCHEMA" --max-turns 5 | jq '.structured_output'
```
