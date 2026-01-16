#!/bin/bash
# gemini_hook.sh - Gemini CLI hook wrapper
#
# This script wraps Python hooks to work with Gemini CLI's hook system.
# It handles input/output normalization so Python hooks can be written once
# and work on any supported platform.
#
# Usage:
#   gemini_hook.sh <python_hook_module>
#
# Example:
#   gemini_hook.sh deepwork.hooks.policy_check
#
# The Python module should implement a main() function that:
# 1. Calls deepwork.hooks.wrapper.run_hook() with a hook function
# 2. The hook function receives HookInput and returns HookOutput
#
# Environment variables set by Gemini CLI:
#   GEMINI_PROJECT_DIR - Absolute path to project root
#
# Input (stdin): JSON from Gemini CLI hook system
# Output (stdout): JSON response for Gemini CLI
# Exit codes:
#   0 - Success (allow action)
#   2 - Blocking error (prevent action)

set -e

# Get the Python module to run
PYTHON_MODULE="${1:-}"

if [ -z "${PYTHON_MODULE}" ]; then
    echo "Usage: gemini_hook.sh <python_hook_module>" >&2
    echo "Example: gemini_hook.sh deepwork.hooks.policy_check" >&2
    exit 1
fi

# Read stdin into variable
HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# Set platform environment variable for the Python module
export DEEPWORK_HOOK_PLATFORM="gemini"

# Run the Python module, passing the input via stdin
# The Python module is responsible for:
# 1. Reading stdin (normalized by wrapper)
# 2. Processing the hook logic
# 3. Writing JSON to stdout
echo "${HOOK_INPUT}" | python -m "${PYTHON_MODULE}"
exit_code=$?

exit ${exit_code}
