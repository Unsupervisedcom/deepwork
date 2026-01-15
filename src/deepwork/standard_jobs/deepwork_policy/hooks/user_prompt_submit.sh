#!/bin/bash
# user_prompt_submit.sh - Runs on every user prompt submission
#
# This script captures the work tree state at each prompt submission.
# This baseline is used for policies with compare_to: prompt to detect
# what changed during an agent response.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Capture work tree state at each prompt for compare_to: prompt policies
"${SCRIPT_DIR}/capture_prompt_work_tree.sh"

# Exit successfully - don't block the prompt
exit 0
