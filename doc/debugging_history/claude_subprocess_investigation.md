# Claude Subprocess Investigation

**Date**: 2026-01-22
**Branch**: `claude/add-prompt-runtime-setting-gPJDA`
**Issue**: Running Claude as a subprocess from within Claude Code hangs indefinitely

## Problem Statement

The `prompt_runtime: claude` feature in DeepWork rules is designed to invoke Claude Code in headless mode to autonomously evaluate rules. When a rule with this setting triggers, the hook should:

1. Spawn `claude --print` as a subprocess
2. Send the rule prompt to it
3. Parse the response for allow/block decision
4. Return the result

However, when running inside a Claude Code session, this subprocess invocation hangs indefinitely.

## Environment

- Claude Code version: 2.1.15
- Platform: macOS (Darwin 25.2.0)
- Python: 3.11.14 (nix-managed)
- Environment variables: `CLAUDECODE=1`, `CLAUDE_CODE_ENTRYPOINT=cli`

## What Works

### Direct Bash Execution (via Claude's Bash tool)
```bash
echo "Say TEST" | claude --print --output-format json 2>&1 | cat
# Returns JSON response immediately
```

### Piping through head -1
```bash
echo "Say TEST" | claude --print --output-format json 2>&1 | head -1
# Returns JSON and terminates cleanly
```

### Python heredoc script (run directly in bash)
```bash
python3 << 'EOF'
import subprocess
# ... subprocess code ...
EOF
# Works correctly
```

## What Doesn't Work

### Python subprocess.run from within Claude
```python
# This hangs indefinitely when run from Python inside Claude Code
result = subprocess.run(
    ["claude", "--print", "prompt"],
    capture_output=True,
    timeout=30,
)
```

### Shell=True with pipes
```python
# Also hangs
subprocess.run(
    'echo "prompt" | claude --print',
    shell=True,
    capture_output=True,
)
```

### Popen with various options
```python
# All of these hang:
# - start_new_session=True
# - close_fds=True
# - stdin=subprocess.DEVNULL
# - Writing to temp file instead of capture_output
```

### Environment variable clearing
```bash
# Still hangs
CLAUDECODE= timeout 15 bash -c 'echo "test" | claude --print'
env -i PATH="$PATH" HOME="$HOME" timeout 15 bash -c 'echo "test" | claude --print'
```

## Key Observations

1. **Direct bash works, Python subprocess doesn't**: The exact same command that works when run via Claude's Bash tool hangs when run via Python's subprocess module.

2. **Piping to `head -1` helps in some cases**: The command `| head -1` causes Claude to terminate after outputting the JSON line, but this doesn't help when the subprocess itself never starts producing output.

3. **The hang occurs at the subprocess level**: Python's subprocess.run times out waiting for the process, suggesting Claude itself is blocked on something.

4. **`--output-format json` is required**: Without this, Claude hangs even longer (possibly waiting for terminal interaction).

5. **Hooks configuration doesn't prevent the hang**: Using `--settings '{"hooks": {}}'` to disable hooks in the subprocess doesn't help.

## Research Findings

### Related GitHub Issues
- [#1481 - Background Process Hangs](https://github.com/anthropics/claude-code/issues/1481): Claude Code waits for child processes even when backgrounded
- [#13598 - /dev/tty hang](https://github.com/anthropics/claude-code/issues/13598): Claude can hang when accessing terminal devices
- Subagent documentation states: "Subagents cannot spawn other subagents" - suggesting nested invocation is intentionally limited

### Root Cause Hypothesis
Claude Code appears to manage its process tree in a way that blocks nested Claude invocations. When running as a subprocess of another Claude instance (detected via `CLAUDECODE=1` environment variable or process hierarchy), the child Claude may be waiting for resources held by the parent.

## Attempted Solutions

### 1. Use `--output-format json` + `| head -1`
**Result**: Works from bash, still hangs from Python subprocess

### 2. Write to temp file instead of capturing output
**Result**: Still hangs - the file remains empty

### 3. Clear CLAUDECODE environment variable
**Result**: Still hangs - the detection/blocking isn't based on this variable alone

### 4. Use `start_new_session=True` for process isolation
**Result**: Still hangs

### 5. Fall back to returning prompt to agent when inside Claude
**Result**: Works but defeats the purpose of `prompt_runtime: claude`

### 6. Change hook command to use `uv run python`
**Result**: Still hangs - the issue is the nested Claude invocation, not Python version

## Recommended Next Steps

1. **Test immediate "allow" return**: Modify the code to immediately return "allow" for claude runtime rules to verify the rest of the flow works.

2. **Create bash wrapper script**: Instead of invoking Claude from Python, create a standalone bash script that the hook can call. This might bypass the subprocess blocking.

3. **Investigate Claude's process management**: Look at Claude Code's source or documentation for how it handles child processes and whether there's an API for nested invocation.

4. **External execution approach**: Consider having the hook queue the rule evaluation and have an external process (outside Claude) handle the actual Claude invocation.

5. **Test from CI/cron**: Verify that `prompt_runtime: claude` works correctly when invoked from outside a Claude session (e.g., from GitHub Actions or a cron job).

## Code Changes Made

The following changes were made to `src/deepwork/hooks/rules_check.py` during this investigation:

1. Added `is_inside_claude_session()` function to detect nested Claude context
2. Added `--output-format json` to get structured output
3. Added `| head -1` pipe to force clean termination
4. Added temp file approach for prompt/output handling
5. Added extensive comments explaining the sensitivity of the subprocess code

## Files Modified (not yet committed)

- `src/deepwork/hooks/rules_check.py` - Multiple changes to invoke_claude_headless()
- `.claude/settings.json` - Changed hook command to use `uv run python`
- `.deepwork/jobs/manual_tests/job.yml` - Added functionality_tests step
- `.deepwork/jobs/manual_tests/steps/functionality_tests.md` - Test instructions

## Conclusion

Running Claude as a subprocess from within a Claude Code session appears to be blocked at a fundamental level. The solution likely requires either:
- An official API for nested Claude invocation
- Running the subprocess invocation from outside the Claude process tree
- Accepting the limitation and falling back to returning prompts to the agent

The `prompt_runtime: claude` feature should work correctly when invoked from external automation (CI, cron, etc.) but cannot work when running inside Claude Code itself.
