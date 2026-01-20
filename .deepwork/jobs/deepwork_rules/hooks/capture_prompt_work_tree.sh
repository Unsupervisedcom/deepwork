#!/bin/bash
# capture_prompt_work_tree.sh - Captures the git work tree state at prompt submission
#
# This script creates a snapshot of ALL tracked files at the time the prompt
# is submitted. This baseline is used for rules with compare_to: prompt and
# created: mode to detect truly NEW files (not modifications to existing ones).
#
# The baseline contains ALL tracked files (not just changed files) so that
# the rules_check hook can determine which files are genuinely new vs which
# files existed before and were just modified.

set -e

# Ensure .deepwork directory exists
mkdir -p .deepwork

# Save ALL tracked files (not just changed files)
# This is critical for created: mode rules to distinguish between:
# - Newly created files (not in baseline) -> should trigger created: rules
# - Modified existing files (in baseline) -> should NOT trigger created: rules
git ls-files > .deepwork/.last_work_tree 2>/dev/null || true

# Also include untracked files that exist at prompt time
# These are files the user may have created before submitting the prompt
git ls-files --others --exclude-standard >> .deepwork/.last_work_tree 2>/dev/null || true

# Sort and deduplicate
if [ -f .deepwork/.last_work_tree ]; then
    sort -u .deepwork/.last_work_tree -o .deepwork/.last_work_tree
fi
