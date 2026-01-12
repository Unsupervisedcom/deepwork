#!/bin/bash
# capture_work_tree.sh - Captures the current git work tree state
#
# This script creates a snapshot of the current git state by recording
# all files that have been modified, added, or deleted. This baseline
# is used later to detect what changed during an agent session.

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
