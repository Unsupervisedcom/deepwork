#!/usr/bin/env bash
# Post-commit reminder hook — delegates to deepwork Python hook.
INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | deepwork hook post_commit_reminder
exit $?
