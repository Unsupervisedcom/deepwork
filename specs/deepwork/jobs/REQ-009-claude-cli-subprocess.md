# REQ-009: Claude CLI Subprocess Wrapper

## Overview

The `ClaudeCLI` class wraps the Claude Code CLI as an async subprocess for use in quality gate evaluations. It enforces structured JSON output via `--json-schema`, handles flag ordering requirements, parses the CLI's wrapper response format, and provides timeout and error management. This is the execution mechanism for external runner mode quality reviews.

## Requirements

### REQ-009.1: Initialization

1. The `ClaudeCLI` MUST accept a `timeout` parameter in seconds (default: 120).
2. The `ClaudeCLI` MUST accept an optional `_test_command` parameter (list of strings) for testing purposes.
3. When `_test_command` is set, it MUST be used as the base command instead of the `claude` binary.
4. When `_test_command` is set, the `--json-schema` flag MUST NOT be added to the command (the test mock handles it).

### REQ-009.2: Command Construction

1. The command MUST invoke the `claude` binary.
2. The command MUST include the `--print` flag for non-interactive mode.
3. The command MUST include `--output-format json` for JSON output.
4. The command MUST include `--system-prompt` followed by the system prompt text.
5. The command MUST include `--json-schema` followed by the JSON-serialized schema string.
6. The command MUST end with `-p --` to read the prompt from stdin.
7. All flags MUST appear BEFORE `-p --` in the command. This ordering is required because `-p` expects a prompt argument and `--` marks the end of flags.
8. When `_test_command` is provided, the command MUST be `[_test_command..., "--system-prompt", system_prompt]`.

### REQ-009.3: Subprocess Execution

1. `run()` MUST be an async method.
2. `run()` MUST create the subprocess using `asyncio.create_subprocess_exec`.
3. The prompt MUST be piped to the subprocess via stdin (encoded as bytes).
4. The subprocess MUST capture both stdout and stderr.
5. If a `cwd` parameter is provided, it MUST be passed to the subprocess as the working directory.
6. The `run()` method MUST accept an optional `timeout` parameter that overrides the instance default for that call.
7. When no per-call timeout is provided, the instance-level timeout MUST be used.

### REQ-009.4: Response Parsing

1. The `_parse_wrapper()` method MUST parse the stdout output as JSON.
2. If the JSON response contains `is_error: true`, the method MUST raise `ClaudeCLIError` with the error result.
3. The method MUST extract the `structured_output` field from the JSON wrapper.
4. If `structured_output` is missing (None), the method MUST raise `ClaudeCLIError` with a truncated excerpt of the response (first 500 characters).
5. If the stdout is not valid JSON, the method MUST raise `ClaudeCLIError` with parse error details and a truncated excerpt.

### REQ-009.5: Error Handling

1. If the subprocess times out, the system MUST kill the process and raise `ClaudeCLIError` indicating the timeout duration.
2. If the subprocess exits with a non-zero return code, the system MUST raise `ClaudeCLIError` with the exit code and stderr content.
3. If the `claude` command is not found on the system (FileNotFoundError), the system MUST raise `ClaudeCLIError` with a descriptive message.
4. All errors from the CLI MUST be wrapped in `ClaudeCLIError`, not raw exceptions.
