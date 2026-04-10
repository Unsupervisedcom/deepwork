# PLUG-REQ-002: Windows Support

## Overview

The Claude Code plugin must work on Windows, where PowerShell is the default shell. Every bash hook script in the plugin must have a functionally equivalent PowerShell (`.ps1`) script so that hooks execute correctly on Windows without requiring Git Bash, WSL, or any Unix compatibility layer.

## Requirements

### PLUG-REQ-002.1: PowerShell Equivalents for Hook Scripts

1. Every `.sh` file under `plugins/claude/hooks/` MUST have a corresponding `.ps1` file in the same directory with the same base name (e.g., `startup_context.sh` → `startup_context.ps1`).
2. Each `.ps1` script MUST be functionally equivalent to its `.sh` counterpart — same stdin/stdout contract, same exit code semantics, same JSON output structure.
3. PowerShell scripts MUST NOT depend on Unix-only tools (`jq`, `grep`, `sed`, `awk`). Use PowerShell-native JSON parsing (`ConvertFrom-Json`, `ConvertTo-Json`) and string operations instead.

### PLUG-REQ-002.2: hooks.json Platform Dispatch

1. Every hook entry in `plugins/claude/hooks/hooks.json` MUST list both the `.sh` command (default shell) and the `.ps1` command with `"shell": "powershell"` so that Claude Code runs the correct script per OS.
2. Both hooks run in parallel; on each OS one succeeds and the other fails gracefully (non-blocking). The `.sh` and `.ps1` hooks for the same event MUST produce identical output when they succeed.

### PLUG-REQ-002.3: PowerShell Script Conventions

1. PowerShell scripts MUST use `$ErrorActionPreference = 'Stop'` for fail-fast behavior (equivalent to `set -euo pipefail`).
2. PowerShell scripts MUST include a header comment block matching the bash convention: description, input/output, exit codes.
3. PowerShell scripts MUST handle errors with try/catch and output `{}` or appropriate fallback JSON on failure, matching the bash error-handling pattern.
