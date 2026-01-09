#!/bin/bash
# get_changed_files.sh - Gets files that changed since the last work tree capture
#
# This script compares the current git state against the baseline captured
# at the start of the session to determine what files were modified.

set -e

# Stage all current changes
git add -A 2>/dev/null || true

# Get current state
current_files=$(git diff --name-only HEAD 2>/dev/null || echo "")
untracked=$(git ls-files --others --exclude-standard 2>/dev/null || echo "")

# Combine and deduplicate current files
all_current=$(echo -e "${current_files}\n${untracked}" | sort -u | grep -v '^$' || true)

if [ -f .deepwork/.last_work_tree ]; then
    # Compare with baseline - files that are new or different
    # Get files in current that weren't in baseline
    last_files=$(cat .deepwork/.last_work_tree 2>/dev/null || echo "")

    # Output files that are in current state
    # This includes both newly changed files and files that were already changed
    echo "${all_current}"
else
    # No baseline exists - return all currently changed files
    echo "${all_current}"
fi
