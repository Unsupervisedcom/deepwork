#!/bin/bash
# check_version.sh - SessionStart hook to check Claude Code version and deepwork installation
#
# This hook performs two critical checks:
# 1. Verifies that the 'deepwork' command is installed and directly invokable
# 2. Warns users if their Claude Code version is below the minimum required
#
# The deepwork check is blocking (exit 2) because hooks cannot function without it.
# The version check is informational only (exit 0) to avoid blocking sessions.
#
# Uses hookSpecificOutput.additionalContext to pass messages to Claude's context.

# ============================================================================
# READ STDIN INPUT
# ============================================================================
# SessionStart hooks receive JSON input via stdin with session information.
# We need to read this to check the session source (startup, resume, clear).

HOOK_INPUT=""
if [ ! -t 0 ]; then
    HOOK_INPUT=$(cat)
fi

# ============================================================================
# SKIP NON-INITIAL SESSIONS
# ============================================================================
# SessionStart hooks can be triggered for different reasons:
# - "startup": Initial session start (user ran `claude` or similar)
# - "resume": Session resumed (user ran `claude --resume`)
# - "clear": Context was cleared/compacted
#
# We only want to run the full check on initial startup. For resumed or
# compacted sessions, return immediately with empty JSON to avoid redundant
# checks and noise.

get_session_source() {
    # Extract the "source" field from the JSON input
    # Returns empty string if not found or not valid JSON
    if [ -n "$HOOK_INPUT" ]; then
        # Use grep and sed for simple JSON parsing (avoid jq dependency)
        echo "$HOOK_INPUT" | grep -o '"source"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*:.*"\([^"]*\)"/\1/' | head -1
    fi
}

SESSION_SOURCE=$(get_session_source)

# If source is anything other than "startup" (or empty/missing for backwards compat),
# skip this hook entirely. Empty source means older Claude Code version that doesn't
# send the source field - we treat that as an initial session to maintain backwards compat.
if [ -n "$SESSION_SOURCE" ] && [ "$SESSION_SOURCE" != "startup" ]; then
    # Non-initial session (resume, clear, etc.) - skip all checks
    echo '{}'
    exit 0
fi

# ============================================================================
# DEEPWORK INSTALLATION CHECK (BLOCKING)
# ============================================================================
# This check runs on initial session start because if deepwork is not installed,
# nothing else will work.

check_deepwork_installed() {
    # Run 'deepwork rules clear_queue' instead of just '--version' for double utility:
    # 1. Verifies that the 'deepwork' command is installed and directly invokable
    # 2. Clears any stale rules from the queue, ensuring a clean slate for the session
    if ! deepwork rules clear_queue >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

print_deepwork_error() {
    cat >&2 << 'EOF'

================================================================================
                    *** DEEPWORK NOT INSTALLED ***
================================================================================

  ERROR: The 'deepwork' command is not available or cannot be directly invoked.

  DeepWork must be installed such that running 'deepwork' directly works.
  For example, running 'deepwork rules clear_queue' should succeed.

  IMPORTANT: Do NOT use 'uv run deepwork' or similar wrappers.
  The command must be directly invokable as just 'deepwork'.

  ------------------------------------------------------------------------
  |                                                                      |
  |   Please fix your deepwork installation before proceeding.           |
  |                                                                      |
  |   Installation options:                                              |
  |     - pipx install deepwork                                          |
  |     - pip install --user deepwork (ensure ~/.local/bin is in PATH)   |
  |     - nix develop (if using the nix flake)                           |
  |                                                                      |
  ------------------------------------------------------------------------

================================================================================

EOF
}

output_deepwork_error_json() {
    cat << 'EOF'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"DEEPWORK INSTALLATION ERROR: The 'deepwork' command is not installed or cannot be directly invoked. DeepWork must be installed such that it can be directly invoked (e.g., 'deepwork', NOT 'uv run deepwork'). Please fix your deepwork installation before proceeding with anything else. DO NOT CONTINUE until this is resolved."},"error":"deepwork command not found - please install deepwork so it can be directly invoked"}
EOF
}

# Check deepwork installation FIRST (before any other checks)
if ! check_deepwork_installed; then
    print_deepwork_error
    output_deepwork_error_json
    exit 2  # Blocking error - prevent session from continuing
fi

# Note: We previously had a re-entry guard using DEEPWORK_VERSION_CHECK_DONE
# environment variable, but that was unreliable across session resumptions.
# Now we use the source field in the hook input JSON to detect initial sessions
# vs resumed/compacted sessions (see SKIP NON-INITIAL SESSIONS section above).

# ============================================================================
# MINIMUM VERSION CONFIGURATION
# ============================================================================
MINIMUM_VERSION="2.1.14"

# ============================================================================
# VERSION CHECK LOGIC
# ============================================================================

# Get current Claude Code version
get_current_version() {
    local version_output
    version_output=$(claude --version 2>/dev/null) || return 1
    # Extract version number (e.g., "2.1.1" from "2.1.1 (Claude Code)")
    echo "$version_output" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

# Compare two semantic versions
# Returns 0 if version1 >= version2, 1 otherwise
version_gte() {
    local version1="$1"
    local version2="$2"

    # Split versions into components
    local v1_major v1_minor v1_patch
    local v2_major v2_minor v2_patch

    IFS='.' read -r v1_major v1_minor v1_patch <<< "$version1"
    IFS='.' read -r v2_major v2_minor v2_patch <<< "$version2"

    # Default to 0 if component is missing
    v1_major=${v1_major:-0}
    v1_minor=${v1_minor:-0}
    v1_patch=${v1_patch:-0}
    v2_major=${v2_major:-0}
    v2_minor=${v2_minor:-0}
    v2_patch=${v2_patch:-0}

    # Compare major version
    if [ "$v1_major" -gt "$v2_major" ]; then
        return 0
    elif [ "$v1_major" -lt "$v2_major" ]; then
        return 1
    fi

    # Compare minor version
    if [ "$v1_minor" -gt "$v2_minor" ]; then
        return 0
    elif [ "$v1_minor" -lt "$v2_minor" ]; then
        return 1
    fi

    # Compare patch version
    if [ "$v1_patch" -ge "$v2_patch" ]; then
        return 0
    else
        return 1
    fi
}

# Generate warning message
get_warning_message() {
    local current_version="$1"

    cat << EOF
CLAUDE CODE VERSION WARNING: Your version (${current_version}) is below the minimum recommended (${MINIMUM_VERSION}). Older versions have known bugs that may cause issues with DeepWork. RECOMMENDED: Update your version of Claude Code. TELL THE USER ABOUT THIS ISSUE LOUDLY!!!
EOF
}

# Print visual warning to stderr for immediate user visibility
print_stderr_warning() {
    local current_version="$1"

    cat >&2 << EOF

================================================================================
                    *** CLAUDE CODE VERSION WARNING ***
================================================================================

  Your Claude Code version: ${current_version}
  Minimum recommended:      ${MINIMUM_VERSION}

  IMPORTANT: Versions below the minimum have known bugs that may cause
  issues with DeepWork functionality. You may experience unexpected
  behavior, errors, or incomplete operations.

  ------------------------------------------------------------------------
  |                                                                      |
  |   RECOMMENDED ACTION: Update your version of Claude Code             |
  |                                                                      |
  ------------------------------------------------------------------------

================================================================================

EOF
}

# Output JSON with additional context for Claude
output_json_with_context() {
    local context="$1"
    # Escape special characters for JSON
    local escaped_context
    escaped_context=$(echo "$context" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ')

    cat << EOF
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"${escaped_context}"}}
EOF
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local current_version
    local warning_message

    # Get current version (don't exit on failure)
    current_version=$(get_current_version) || current_version=""

    if [ -z "$current_version" ]; then
        # Could not determine version, output empty JSON and exit
        echo '{}'
        exit 0
    fi

    # Check if current version is below minimum
    if ! version_gte "$current_version" "$MINIMUM_VERSION"; then
        # Print visual warning to stderr
        print_stderr_warning "$current_version"

        # Output JSON with context for Claude
        warning_message=$(get_warning_message "$current_version")
        output_json_with_context "$warning_message"
    else
        # Version is OK, output empty JSON
        echo '{}'
    fi

    exit 0
}

main "$@"
