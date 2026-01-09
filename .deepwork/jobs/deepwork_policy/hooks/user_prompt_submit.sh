#!/bin/bash
# user_prompt_submit.sh - Runs on every user prompt submission
#
# This script captures the work tree baseline if it doesn't exist yet.
# This ensures we have a baseline to compare against when evaluating policies.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Only capture if no baseline exists yet (first prompt of session)
if [ ! -f .deepwork/.last_work_tree ]; then
    "${SCRIPT_DIR}/capture_work_tree.sh"
fi

# Exit successfully - don't block the prompt
exit 0
