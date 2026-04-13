#!/usr/bin/env bash
set -euo pipefail

# Requirements Traceability Precompute Script
# Produces a structured summary for the requirements-reviewer agent,
# eliminating the need for dozens of sequential grep/read tool calls.
#
# Usage: .deepwork/requirements_traceability_info.sh [base_branch]
# Output: Structured markdown to stdout

BASE_REF="${1:-}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Configurable directories
SPEC_DIR="doc/specs"
TEST_DIR="tests"

TMPDIR_TRACE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_TRACE"' EXIT

# ==== Detect base ref (mirrors src/deepwork/review/matcher.py) ====

if [ -z "$BASE_REF" ]; then
  # Auto-detect: try symbolic-ref, then well-known names
  BASE_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/||' || true)
  if [ -z "$BASE_REF" ] || ! git rev-parse --verify "$BASE_REF" &>/dev/null; then
    for ref in origin/main origin/master main master; do
      if git rev-parse --verify "$ref" &>/dev/null; then
        BASE_REF="$ref"
        break
      fi
    done
  fi
  [ -z "$BASE_REF" ] && BASE_REF="HEAD"
fi

# Find merge-base (common ancestor) — this is what we diff against
if [ "$BASE_REF" = "HEAD" ]; then
  MERGE_BASE="HEAD"
else
  MERGE_BASE=$(git merge-base HEAD "$BASE_REF" 2>/dev/null || echo "HEAD")
fi

# ==== Collect common data upfront ====

# Changes committed on this branch since merge-base
BRANCH_CHANGED=$(git diff "${MERGE_BASE}" --name-only --diff-filter=ACMR 2>/dev/null || true)
# Staged but uncommitted
STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
# Untracked non-ignored
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)
# Combine all (deduplicated)
ALL_FILES=$(echo -e "${BRANCH_CHANGED}\n${STAGED}\n${UNTRACKED}" | sort -u | grep -v '^$' || true)

# Single grep across the whole repo (excluding specs/) for REQ references
grep -roHE '[A-Z]+-REQ-[0-9]+(\.[0-9]+)*' --exclude-dir="$SPEC_DIR" . 2>/dev/null | \
  sed 's|^\./||' | sort -u > "$TMPDIR_TRACE/all_refs.txt" || true

# ==== Section 0: PR Description ====

echo "# Precomputed Requirements Traceability Data"
echo ""
echo "## 0. PR Description"
echo ""
# Try to get PR description for current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
PR_BODY=$(gh pr view "$CURRENT_BRANCH" --json body --jq '.body' 2>/dev/null || true)
if [ -n "$PR_BODY" ]; then
  echo '```text'
  echo "$PR_BODY"
  echo '```'
else
  echo "[No PR found for branch '${CURRENT_BRANCH}']"
fi
echo ""

# ==== Section 1: Changed files by top-level directory ====

echo "## 1. Changed Files"
echo ""
echo '```'
if [ -n "$ALL_FILES" ]; then
  # Group by top-level directory (or "root" for files at repo root)
  echo "$ALL_FILES" | awk -F/ '{
    if (NF == 1) dir = "(root)"
    else dir = $1
    files[dir] = files[dir] ? files[dir] "\n  " $0 : "  " $0
  }
  END {
    for (d in files) order[++n] = d
    for (i = 1; i <= n; i++)
      for (j = i+1; j <= n; j++)
        if (order[i] > order[j]) { t=order[i]; order[i]=order[j]; order[j]=t }
    for (i = 1; i <= n; i++) print order[i] ":\n" files[order[i]]
  }'
else
  echo "(no files changed)"
fi
echo '```'
echo ""

# Quick-reject hints
CHANGED_SPECS=$(echo "$ALL_FILES" | grep "^${SPEC_DIR}/" || true)
CHANGED_TESTS=$(echo "$ALL_FILES" | grep "^${TEST_DIR}/" || true)
CHANGED_NON_SPEC_TEST=$(echo "$ALL_FILES" | grep -v "^${SPEC_DIR}/" | grep -v "^${TEST_DIR}/" || true)

HINTS=""
[ -z "$CHANGED_SPECS" ] && HINTS="${HINTS}- No spec files changed — check PR description and diffs to determine if requirements need to be added or updated for this change.\n"
[ -z "$CHANGED_TESTS" ] && HINTS="${HINTS}- No test files changed — skip test stability check.\n"
[ -z "$CHANGED_NON_SPEC_TEST" ] && HINTS="${HINTS}- No source/config files changed — skip new-functionality coverage check.\n"
if [ -n "$HINTS" ]; then
  echo "**Review shortcuts:**"
  echo -e "$HINTS"
fi

# ==== Section 2: Requirement IDs referenced in changed files ====

echo "## 2. Requirement IDs Referenced in Changed Files"
echo ""
echo '```'
IN_PLAY_REQS=""
if [ -n "$ALL_FILES" ]; then
  while IFS= read -r f; do
    if [ -f "$f" ]; then
      REFS=$(grep -oE '[A-Z]+-REQ-[0-9]+(\.[0-9]+)*' "$f" 2>/dev/null | sort -u || true)
      if [ -n "$REFS" ]; then
        echo "$f:"
        echo "$REFS" | sed 's/^/  /'
        IN_PLAY_REQS="${IN_PLAY_REQS}${REFS}"$'\n'
      fi
    fi
  done <<< "$ALL_FILES"
fi
echo '```'
echo ""

# Build the set of in-play requirement section IDs (unique, section-level)
IN_PLAY_SECTIONS=$(echo "$IN_PLAY_REQS" | grep -oE '[A-Z]+-REQ-[0-9]+' | sort -u || true)

# Also include sections from changed spec files
if [ -n "$CHANGED_SPECS" ]; then
  SPEC_SECTIONS=$(grep -roh '^### [A-Z]*-REQ-[0-9.]*' ${CHANGED_SPECS} 2>/dev/null | \
    sed 's/^### //' | grep -oE '[A-Z]+-REQ-[0-9]+' | sort -u || true)
  IN_PLAY_SECTIONS=$(echo -e "${IN_PLAY_SECTIONS}\n${SPEC_SECTIONS}" | sort -u || true)
fi

# ==== Section 3: Files that reference each in-play requirement ====

echo "## 3. Files That Reference Each In-Play Requirement"
echo ""
echo "Scoped to requirements referenced by changed files or in changed specs."
echo "Check the full repo if you need coverage for other requirements."
echo ""

# Collect in-play REQ IDs at full granularity from specs
IN_PLAY_REQ_IDS=""
if [ -n "$IN_PLAY_SECTIONS" ]; then
  while IFS= read -r section; do
    [ -z "$section" ] && continue
    SECTION_REQS=$(grep -roh "^### ${section}\.[0-9.]*" "$SPEC_DIR/" 2>/dev/null | sed 's/^### //' || true)
    IN_PLAY_REQ_IDS="${IN_PLAY_REQ_IDS}${section}"$'\n'"${SECTION_REQS}"$'\n'
  done <<< "$IN_PLAY_SECTIONS"
  IN_PLAY_REQ_IDS=$(echo "$IN_PLAY_REQ_IDS" | sort -u | grep -v '^$' || true)
fi

echo '```'
if [ -n "$IN_PLAY_REQ_IDS" ]; then
  while IFS= read -r req_id; do
    [ -z "$req_id" ] && continue
    MATCHES=$(grep ":${req_id}$" "$TMPDIR_TRACE/all_refs.txt" 2>/dev/null | cut -d: -f1 | sort -u || true)
    if [ -z "$MATCHES" ]; then
      echo "${req_id}: (not referenced)"
    else
      echo "${req_id}:"
      echo "$MATCHES" | sed 's/^/  /'
    fi
  done <<< "$IN_PLAY_REQ_IDS"
else
  echo "(no in-play requirements)"
fi
echo '```'
echo ""

# ==== Section 4: Test stability cross-reference ====

echo "## 4. Test Stability Cross-Reference"
echo ""
echo "For each changed test file: which requirements it validates and whether"
echo "those requirements also changed in this branch."
echo ""

# Collect REQ IDs from changed spec files
CHANGED_REQ_IDS=""
if [ -n "$CHANGED_SPECS" ]; then
  CHANGED_REQ_IDS=$(grep -ohE '[A-Z]+-REQ-[0-9]+(\.[0-9]+)*' ${CHANGED_SPECS} 2>/dev/null | sort -u || true)
fi

if [ -n "$CHANGED_TESTS" ]; then
  while IFS= read -r test_file; do
    [ -z "$test_file" ] || [ ! -f "$test_file" ] && continue
    TEST_REQS=$(grep -oE '[A-Z]+-REQ-[0-9]+(\.[0-9]+)*' "$test_file" 2>/dev/null | sort -u || true)

    echo "### ${test_file}"
    echo ""

    if [ -z "$TEST_REQS" ]; then
      echo "Referenced requirements: (none)"
      echo ""
      continue
    fi

    # Split into changed and unchanged requirements
    CHANGED_LIST=""
    UNCHANGED_LIST=""
    while IFS= read -r req; do
      REQ_SECTION=$(echo "$req" | grep -oE '[A-Z]+-REQ-[0-9]+')
      if echo "$CHANGED_REQ_IDS" | grep -q "^${req}$" 2>/dev/null || \
         echo "$CHANGED_REQ_IDS" | grep -q "^${REQ_SECTION}\." 2>/dev/null; then
        CHANGED_LIST="${CHANGED_LIST}  ${req}"$'\n'
      else
        UNCHANGED_LIST="${UNCHANGED_LIST}  ${req}"$'\n'
      fi
    done <<< "$TEST_REQS"

    if [ -n "$CHANGED_LIST" ]; then
      echo "With spec changes:"
      echo "$CHANGED_LIST"
    fi
    if [ -n "$UNCHANGED_LIST" ]; then
      UNCHANGED_COUNT=$(echo "$UNCHANGED_LIST" | grep -c '[A-Z]' || true)
      echo "WITHOUT spec changes (${UNCHANGED_COUNT}):"
      echo "$UNCHANGED_LIST"
    fi
    echo ""
  done <<< "$CHANGED_TESTS"
else
  echo "(no test files changed)"
  echo ""
fi
echo ""

# ==== Section 5: New or changed requirements in this branch ====

echo "## 5. New or Changed Requirements in This Branch"
echo ""
if [ -n "$CHANGED_SPECS" ]; then
  ADDED_SECTIONS=$(git diff "${MERGE_BASE}" -- ${CHANGED_SPECS} 2>/dev/null | grep -E '^\+###' | sed 's/^\+### //' | sort -u || true)
  REMOVED_SECTIONS=$(git diff "${MERGE_BASE}" -- ${CHANGED_SPECS} 2>/dev/null | grep -E '^-###' | sed 's/^-### //' | sort -u || true)

  if [ -n "$ADDED_SECTIONS" ]; then
    echo "**Added sections:**"
    echo '```'
    echo "$ADDED_SECTIONS"
    echo '```'
    echo ""
  fi
  if [ -n "$REMOVED_SECTIONS" ]; then
    echo "**Removed sections:**"
    echo '```'
    echo "$REMOVED_SECTIONS"
    echo '```'
    echo ""
  fi
  if [ -z "$ADDED_SECTIONS" ] && [ -z "$REMOVED_SECTIONS" ]; then
    echo "No section headings added or removed (changes were within existing sections)."
    echo ""
    echo "Changed spec files: ${CHANGED_SPECS}" | tr '\n' ', '
    echo ""
  fi
else
  echo "(no spec files changed)"
fi
echo ""

# ==== Section 6: Diffs (ALL REMAINING CONTENT IS DIFFS) ====

echo "## 6. Diffs (ALL REMAINING CONTENT IS DIFFS)"
echo ""
echo "### Stat"
echo '```'
git diff "${MERGE_BASE}" --stat || true
echo '```'
echo ""

# Get unique top-level directories from changed files
TOP_DIRS=$(echo "$ALL_FILES" | awk -F/ '{ if (NF == 1) print "(root)"; else print $1 }' | sort -u || true)

if [ -n "$TOP_DIRS" ]; then
  while IFS= read -r dir; do
    [ -z "$dir" ] && continue

    if [ "$dir" = "(root)" ]; then
      # Root-level files: match files with no slash
      ROOT_FILES=$(echo "$ALL_FILES" | grep -v '/' || true)
      [ -z "$ROOT_FILES" ] && continue
      echo "### ${dir}"
      echo '```diff'
      # Committed root-level files
      while IFS= read -r f; do
        git diff "${MERGE_BASE}" -- "$f" 2>/dev/null || true
      done <<< "$ROOT_FILES"
      # Staged root-level files
      (echo "$STAGED" | grep -v '/' 2>/dev/null || true) | while IFS= read -r f; do
        [ -n "$f" ] && git diff --cached -- "$f" 2>/dev/null || true
      done
      # Untracked root-level files
      (echo "$UNTRACKED" | grep -v '/' 2>/dev/null || true) | while IFS= read -r f; do
        [ -n "$f" ] && [ -f "$f" ] && git diff --no-index /dev/null "$f" 2>/dev/null || true
      done
      echo '```'
      echo ""
    else
      echo "### ${dir}/"
      echo '```diff'
      git diff "${MERGE_BASE}" -- "${dir}/**" 2>/dev/null || true
      # Staged files in this dir
      git diff --cached -- "${dir}/**" 2>/dev/null || true
      # Untracked files in this dir
      (echo "$UNTRACKED" | grep "^${dir}/" 2>/dev/null || true) | while IFS= read -r f; do
        [ -n "$f" ] && [ -f "$f" ] && git diff --no-index /dev/null "$f" 2>/dev/null || true
      done
      echo '```'
      echo ""
    fi
  done <<< "$TOP_DIRS"
fi
