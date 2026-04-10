#!/usr/bin/env bash
# run_hook.sh - Cross-platform hook dispatcher
#
# Routes to the correct platform-specific hook script based on OS.
# On Windows (MSYS/Cygwin/Git Bash), runs the .ps1 PowerShell version.
# On macOS/Linux, runs the .sh bash version.
#
# Usage: run_hook.sh <hook_name>
#   hook_name: base name without extension (e.g., "startup_context")
#
# Input (stdin):  passed through to the platform-specific script
# Output (stdout): output from the platform-specific script
# Exit codes:     propagated from the platform-specific script

set -euo pipefail

HOOK_NAME="${1:?Usage: run_hook.sh <hook_name>}"
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${HOOK_DIR}/${HOOK_NAME}.ps1"
else
  exec "${HOOK_DIR}/${HOOK_NAME}.sh"
fi
