#!/bin/bash
# capture_prompt_work_tree.sh - Captures the git work tree state at prompt submission
#
# This script creates a snapshot of the current git state by recording
# all files that have been modified, added, or deleted. This baseline
# is used for policies with compare_to: prompt to detect what changed
# during an agent response (between user prompts).

set -e

# Ensure .deepwork directory exists
mkdir -p .deepwork

# Stage all changes so we can diff against HEAD
git add -A 2>/dev/null || true

# Save the current state of changed files
# Using git diff --name-only HEAD to get the list of all changed files
git diff --name-only HEAD > .deepwork/.last_work_tree 2>/dev/null || true

# Also include untracked files not yet in the index
git ls-files --others --exclude-standard >> .deepwork/.last_work_tree 2>/dev/null || true

# Sort and deduplicate
if [ -f .deepwork/.last_work_tree ]; then
    sort -u .deepwork/.last_work_tree -o .deepwork/.last_work_tree
fi
