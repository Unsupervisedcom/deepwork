#!/usr/bin/env bash
# Post-commit reminder hook — delegates to deepwork Python hook.
# Falls back to `uvx deepwork` so end-user installs (where the plugin's
# MCP server is launched via uvx and `deepwork` is not on PATH) still work.
INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
if command -v deepwork >/dev/null 2>&1; then
  echo "${INPUT}" | deepwork hook post_commit_reminder
else
  echo "${INPUT}" | uvx deepwork hook post_commit_reminder
fi
exit $?
