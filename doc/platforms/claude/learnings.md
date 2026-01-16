# Claude Code Platform Learnings

This document captures behaviors, quirks, and insights discovered while implementing DeepWork's Claude Code adapter.

## Add Your Learnings Here

When you discover something about Claude Code behavior that isn't obvious from documentation, add it to the appropriate section below.

---

## Hook System

### Stop Hook Behavior

- **Blocking requires `decision: "block"`** - Using `"deny"` does not work
- **Exit code 2 also blocks** - stderr message is shown to the agent
- **Empty JSON `{}` allows stopping** - No explicit allow needed
- **`reason` field is shown to Claude** - Use it to explain what needs to be done

### Transcript Path

- **transcript_path is JSONL format** - Each line is a separate JSON object
- **Assistant messages have nested structure** - Content is in `.message.content[].text`
- **Role is at top level** - Check `.role == "assistant"` to find assistant messages

### Environment Variables

- **CLAUDE_PROJECT_DIR is always set** - Reliable for finding project root
- **CLAUDE_ENV_FILE only in SessionStart** - Not available in other hooks

## JSON Format Quirks

### Input Parsing

- **jq works well** - Standard JSON parsing, no special escaping needed
- **tool_input varies by tool** - Check tool_name to know the structure

### Output Formatting

- **Use heredocs for complex JSON** - Avoids shell escaping issues
- **Newlines in reason are preserved** - Can use multi-line explanations

## Testing Notes

### Local Testing

- **PYTHONPATH must include src/** - For Python module imports to work
- **Working directory matters** - Hook scripts expect to be run from project root
- **Create .deepwork directory** - Required for prompt baseline tracking

---

## Date Log

| Date | Finding | Author |
|------|---------|--------|
| 2026-01-15 | Initial documentation created | Claude |
