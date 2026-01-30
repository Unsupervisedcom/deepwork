#!/bin/bash
# capture_prompt_work_tree.sh - Captures the git work tree state at prompt submission
#
# =============================================================================
# HOW THIS WORKS: GIT PLUMBING WITH TEMPORARY INDEX
# =============================================================================
#
# This script uses Git "plumbing" commands to create a snapshot of the entire
# working directory (including untracked files) WITHOUT touching your actual
# staging area or commit history.
#
# THE APPROACH:
# 1. Create a temporary file to act as a separate git index
#    - By setting GIT_INDEX_FILE, Git uses this temp file instead of .git/index
#    - This ensures we don't interfere with any actual staged changes
#
# 2. Stage everything to this temporary index (git add -A)
#    - Captures modified files, new files, and deleted files
#    - Respects .gitignore automatically
#
# 3. Create a "Tree Object" from the temporary index (git write-tree)
#    - A tree object is a snapshot stored in Git's object database
#    - Returns a SHA hash (e.g., "d8329fc1...") representing the exact state
#    - This is like a lightweight commit with no message/parent/author
#
# 4. Save the tree hash for later comparison
#    - At "stop" time, we create another tree object for the current state
#    - Then use "git diff-tree" to compare the two trees
#
# WHY THIS IS ROBUST:
# - FAST: Git is optimized for tree comparisons
# - SAFE: Does not touch HEAD, current Index, or Stashes
# - COMPLETE: Handles modified, new (untracked), and deleted files
# - CLEAN: Respects .gitignore automatically
#
# WHAT WE CAN DETECT:
# | Scenario              | Handled? | Explanation                                |
# |-----------------------|----------|-------------------------------------------|
# | Modified files        | ✅ Yes   | Git detects content hash changed          |
# | New untracked files   | ✅ Yes   | git add -A captures them in temp index    |
# | Deleted files         | ✅ Yes   | Tree comparison shows them as missing     |
# | Staged vs Unstaged    | ✅ Yes   | We look at disk state, ignore staging     |
# | Ignored files         | ❌ No    | git add respects .gitignore (by design)   |
#
# =============================================================================

set -e

# Ensure .deepwork directory exists
mkdir -p .deepwork

# 1. Create a temporary file to act as a separate git index
#    This ensures we don't mess with the actual 'git add' staging area.
TEMP_INDEX=$(mktemp)

# 2. Use this temp file instead of .git/index
export GIT_INDEX_FILE="$TEMP_INDEX"

# 3. Add EVERYTHING to this temp index
#    -A handles new files, deletions, and modifications
#    It respects .gitignore automatically
git add -A 2>/dev/null || true

# 4. Write this state to a "Tree Object" and get the hash
#    This stores the snapshot in git's object database without creating a commit
TREE_HASH=$(git write-tree 2>/dev/null || echo "")

# 5. Clean up the temporary index
rm -f "$TEMP_INDEX"

# 6. Save the tree hash for later comparison by rules_check
if [ -n "$TREE_HASH" ]; then
    echo "$TREE_HASH" > .deepwork/.last_tree_hash
else
    # Fallback: if git write-tree failed, clear the file
    rm -f .deepwork/.last_tree_hash
fi

# Also save the HEAD ref for backwards compatibility and as a fallback
# This is used for committed changes detection
git rev-parse HEAD > .deepwork/.last_head_ref 2>/dev/null || echo "" > .deepwork/.last_head_ref

# LEGACY: Keep .last_work_tree for backwards compatibility during transition
# This will be removed in a future version
git ls-files > .deepwork/.last_work_tree 2>/dev/null || true
git ls-files --others --exclude-standard >> .deepwork/.last_work_tree 2>/dev/null || true
if [ -f .deepwork/.last_work_tree ]; then
    sort -u .deepwork/.last_work_tree -o .deepwork/.last_work_tree
fi
