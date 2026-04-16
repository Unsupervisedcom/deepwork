#!/usr/bin/env bash
# DeepSchema write hook
# PostToolUse hook for Write/Edit - validates files against applicable DeepSchemas
# Falls back to `uvx deepwork` so end-user installs (where the plugin's
# MCP server is launched via uvx and `deepwork` is not on PATH) still work.

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
if command -v deepwork >/dev/null 2>&1; then
  echo "${INPUT}" | deepwork hook deepschema_write
else
  echo "${INPUT}" | uvx deepwork hook deepschema_write
fi
exit $?
