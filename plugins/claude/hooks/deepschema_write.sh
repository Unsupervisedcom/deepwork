#!/usr/bin/env bash
# DeepSchema write hook
# PostToolUse hook for Write/Edit - validates files against applicable DeepSchemas

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | deepwork hook deepschema_write
exit $?
