# PLUG-REQ-002: Windows Support

## Overview

The Claude Code plugin must work on Windows, where PowerShell is the default shell. Every bash hook script in the plugin must have a functionally equivalent PowerShell (`.ps1`) script so that hooks execute correctly on Windows without requiring Git Bash, WSL, or any Unix compatibility layer.

## Requirements

### PLUG-REQ-002.1: PowerShell Equivalents for Hook Scripts

1. Every `.sh` file under `plugins/claude/hooks/` MUST have a corresponding `.ps1` file in the same directory with the same base name (e.g., `startup_context.sh` → `startup_context.ps1`).
2. Each `.ps1` script MUST be functionally equivalent to its `.sh` counterpart — same stdin/stdout contract, same exit code semantics, same JSON output structure.
3. PowerShell scripts MUST NOT depend on Unix-only tools (`jq`, `grep`, `sed`, `awk`). Use PowerShell-native JSON parsing (`ConvertFrom-Json`, `ConvertTo-Json`) and string operations instead.

### PLUG-REQ-002.2: hooks.json Platform Dispatch

1. `plugins/claude/hooks/hooks.json` MUST be updated to reference both `.sh` and `.ps1` scripts, using platform-conditional dispatch so the correct script runs on each OS.
2. If Claude Code's hook system does not yet support platform-conditional dispatch in `hooks.json`, the `.ps1` files MUST still exist and be documented as the Windows alternative, ready to wire in when platform dispatch is available.

### PLUG-REQ-002.3: PowerShell Script Conventions

1. PowerShell scripts MUST use `$ErrorActionPreference = 'Stop'` for fail-fast behavior (equivalent to `set -euo pipefail`).
2. PowerShell scripts MUST include a header comment block matching the bash convention: description, input/output, exit codes.
3. PowerShell scripts MUST handle errors with try/catch and output `{}` or appropriate fallback JSON on failure, matching the bash error-handling pattern.
