# REQ-006: Hook Wrapper System

## Overview

The hook wrapper system provides cross-platform compatibility for hooks running on different AI CLI platforms (Claude Code, Gemini CLI). It normalizes platform-specific event names, tool names, and output formats into a common representation, allowing hooks to be written once in Python and executed on any supported platform. The wrapper handles all I/O (stdin/stdout JSON) and error handling.

## Requirements

### REQ-006.1: Supported Platforms

1. The system MUST support the following platforms as a `Platform` enum: `CLAUDE` (`"claude"`) and `GEMINI` (`"gemini"`).
2. The `Platform` enum MUST be a `StrEnum` for string serialization.

### REQ-006.2: Event Normalization

1. The system MUST define a `NormalizedEvent` enum with the following values: `AFTER_AGENT`, `BEFORE_TOOL`, `BEFORE_PROMPT`, `SESSION_START`, `SESSION_END`, `AFTER_TOOL`, `BEFORE_MODEL`, `AFTER_MODEL`.
2. The `NormalizedEvent` enum MUST be a `StrEnum`.

#### Claude Code Event Mapping

3. Claude `"Stop"` MUST map to `AFTER_AGENT`.
4. Claude `"SubagentStop"` MUST map to `AFTER_AGENT`.
5. Claude `"PreToolUse"` MUST map to `BEFORE_TOOL`.
6. Claude `"PostToolUse"` MUST map to `AFTER_TOOL`.
7. Claude `"UserPromptSubmit"` MUST map to `BEFORE_PROMPT`.
8. Claude `"SessionStart"` MUST map to `SESSION_START`.
9. Claude `"SessionEnd"` MUST map to `SESSION_END`.

#### Gemini CLI Event Mapping

10. Gemini `"AfterAgent"` MUST map to `AFTER_AGENT`.
11. Gemini `"BeforeTool"` MUST map to `BEFORE_TOOL`.
12. Gemini `"AfterTool"` MUST map to `AFTER_TOOL`.
13. Gemini `"BeforeAgent"` MUST map to `BEFORE_PROMPT`.
14. Gemini `"SessionStart"` MUST map to `SESSION_START`.
15. Gemini `"SessionEnd"` MUST map to `SESSION_END`.
16. Gemini `"BeforeModel"` MUST map to `BEFORE_MODEL`.
17. Gemini `"AfterModel"` MUST map to `AFTER_MODEL`.

#### Reverse Mapping

18. The system MUST maintain reverse mappings (`NORMALIZED_TO_EVENT`) for converting normalized events back to platform-specific names.

### REQ-006.3: Tool Name Normalization

1. Tool names MUST be normalized to snake_case.

#### Claude Code Tool Mapping

2. Claude `"Write"` MUST map to `"write_file"`.
3. Claude `"Edit"` MUST map to `"edit_file"`.
4. Claude `"Read"` MUST map to `"read_file"`.
5. Claude `"Bash"` MUST map to `"shell"`.
6. Claude `"Glob"` MUST map to `"glob"`.
7. Claude `"Grep"` MUST map to `"grep"`.
8. Claude `"WebFetch"` MUST map to `"web_fetch"`.
9. Claude `"WebSearch"` MUST map to `"web_search"`.
10. Claude `"Task"` MUST map to `"task"`.

#### Gemini CLI Tool Mapping

11. Gemini tool names MUST already be in snake_case and SHALL map to themselves.

#### Fallback

12. Unknown tool names MUST be lowercased as a fallback normalization strategy.

#### Reverse Mapping

13. The system MUST maintain reverse mappings (`NORMALIZED_TO_TOOL`) for converting normalized tool names back to platform-specific names.

### REQ-006.4: HookInput Normalization

1. `HookInput` MUST be a dataclass with fields: `platform`, `event`, `session_id`, `transcript_path`, `cwd`, `tool_name`, `tool_input`, `tool_response`, `prompt`, `raw_input`.
2. `HookInput.from_dict()` MUST extract `hook_event_name` from the raw input and normalize it via `EVENT_TO_NORMALIZED`.
3. `HookInput.from_dict()` MUST extract `tool_name` from the raw input and normalize it via `TOOL_TO_NORMALIZED`.
4. If the raw event name is not found in the mapping, it MUST default to `AFTER_AGENT`.
5. `HookInput.from_dict()` MUST preserve the original raw input in the `raw_input` field.
6. `normalize_input()` MUST parse JSON from a raw string, defaulting to an empty dict on empty input or JSON decode error.

### REQ-006.5: HookOutput Denormalization

1. `HookOutput` MUST be a dataclass with fields: `decision`, `reason`, `context`, `continue_loop` (default: True), `stop_reason`, `suppress_output` (default: False), `raw_output`.
2. When `decision` is empty, the output dict MUST NOT contain a `decision` key.
3. When `decision` is `"block"` on the Gemini platform, it MUST be converted to `"deny"` in the output.
4. When `decision` is `"block"` on the Claude platform, it MUST remain as `"block"`.
5. When `reason` is non-empty, it MUST be included as `"reason"` in the output.
6. When `continue_loop` is `False`, the output MUST include `"continue": false`.
7. When `continue_loop` is `False` and `stop_reason` is non-empty, the output MUST include `"stopReason"`.
8. When `suppress_output` is `True`, the output MUST include `"suppressOutput": true`.

### REQ-006.6: Context Output (Platform-Specific)

1. On Claude for `SESSION_START` events, context MUST be set via `hookSpecificOutput.additionalContext` with `hookEventName` set to the platform-specific event name.
2. On Claude for all other events, context MUST be set via `systemMessage`.
3. On Gemini for all events, context MUST be set via `hookSpecificOutput.additionalContext` with `hookEventName`.

### REQ-006.7: Output Serialization

1. `denormalize_output()` MUST convert a `HookOutput` to a platform-specific JSON string.
2. If the output dict is empty (no decision, no reason, no context, etc.), the result MUST be `"{}"`.
3. Raw output fields MUST be merged into the result, but MUST NOT overwrite fields already set by the normalization logic.

### REQ-006.8: I/O Functions

1. `read_stdin()` MUST return an empty string if stdin is a TTY.
2. `read_stdin()` MUST return an empty string if reading stdin raises any exception.
3. `write_stdout()` MUST print the data to stdout.

### REQ-006.9: Error Handling

1. `format_hook_error()` MUST produce a dict with `decision: "block"` and a `reason` containing the error details.
2. The error reason MUST include: a "Hook Script Error" header, optional context, error type, error message, and full traceback.
3. `output_hook_error()` MUST serialize the error dict to JSON and print to stdout.

### REQ-006.10: run_hook Entry Point

1. `run_hook()` MUST accept a hook function (Callable[[HookInput], HookOutput]) and a Platform.
2. `run_hook()` MUST read stdin, normalize input, call the hook function, denormalize output, and write to stdout.
3. `run_hook()` MUST always return exit code 0, regardless of success or failure.
4. When the hook function raises an exception, `run_hook()` MUST catch it, output a JSON error response via `output_hook_error()`, and return 0.
5. The exit code MUST always be 0 because the JSON `decision` field controls blocking behavior, not the exit code.
