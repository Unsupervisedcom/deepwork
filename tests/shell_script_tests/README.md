# Shell Script Tests

Automated tests for DeepWork shell scripts and hooks, with a focus on validating Claude Code hooks JSON response formats.

## Hooks and Scripts Tested

| Hook/Script | Type | Description |
|-------------|------|-------------|
| `deepwork.hooks.rules_check` | Stop Hook (Python) | Evaluates rules and blocks agent stop if rules are triggered |
| `user_prompt_submit.sh` | UserPromptSubmit Hook | Captures work tree state when user submits a prompt |
| `capture_prompt_work_tree.sh` | Helper | Records current git state for `compare_to: prompt` rules |
| `make_new_job.sh` | Utility | Creates directory structure for new DeepWork jobs |

## Claude Code Hooks JSON Format

Hook scripts must return valid JSON responses. The tests enforce these formats:

### Stop Hooks (`hooks.after_agent`)
```json
{}                                          // Allow stop
{"decision": "block", "reason": "..."}      // Block stop with reason
```

### UserPromptSubmit Hooks (`hooks.before_prompt`)
```json
{}    // No output or empty object (side-effect only hooks)
```

### All Hooks
- Must return valid JSON if producing output
- Non-JSON output on stdout is **not allowed** (stderr is ok)
- Exit code 0 indicates success (even when blocking)

## Running Tests

```bash
# Run all shell script tests
uv run pytest tests/shell_script_tests/ -v

# Run tests for a specific script
uv run pytest tests/shell_script_tests/test_rules_stop_hook.py -v

# Run with coverage
uv run pytest tests/shell_script_tests/ --cov=src/deepwork
```

## Test Structure

```
tests/shell_script_tests/
├── conftest.py                      # Shared fixtures and helpers
├── test_hooks.py                    # Consolidated hook tests (JSON format, exit codes)
├── test_rules_stop_hook.py          # Stop hook blocking/allowing tests
├── test_user_prompt_submit.py       # Prompt submission hook tests
├── test_capture_prompt_work_tree.py # Work tree capture tests
└── test_make_new_job.py             # Job directory creation tests
```

## Shared Fixtures

Available in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `git_repo` | Basic git repo with initial commit |
| `git_repo_with_rule` | Git repo with a Python file rule |
| `jobs_scripts_dir` | Path to job management scripts |

## Adding New Tests

1. Use shared fixtures from `conftest.py` when possible
2. Use `run_shell_script()` helper for running scripts
3. Validate JSON output with `validate_json_output()` and `validate_stop_hook_response()`
4. Test both success and failure cases
5. Verify exit codes (hooks should exit 0 even when blocking)
