#!/bin/bash
# check_version.sh - SessionStart hook to check Claude Code version
#
# Warns users if their Claude Code version is below the minimum required
# version, as older versions may have bugs that affect DeepWork functionality.
#
# Uses hookSpecificOutput.additionalContext to pass the warning to Claude's
# context so it can inform the user appropriately.

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
CLAUDE CODE VERSION WARNING: Your version (${current_version}) is below the minimum recommended (${MINIMUM_VERSION}). Older versions have known bugs that may cause issues with DeepWork. RECOMMENDED: Run /update to update Claude Code.
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
  |   RECOMMENDED ACTION: Run /update to update Claude Code              |
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
