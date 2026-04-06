#!/usr/bin/env bash
# DeepPlan exit guard hook
# PreToolUse hook for ExitPlanMode - enforces DeepPlan workflow

INPUT=$(cat)
export DEEPWORK_HOOK_PLATFORM="claude"
echo "${INPUT}" | deepwork hook deepplan_exit
exit $?
