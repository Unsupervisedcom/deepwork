#!/usr/bin/env bash
#
# make_new_job.sh - Create directory structure for a new investigation
#
# Usage: ./make_new_job.sh <investigation_name>
#

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Validate investigation name format
validate_investigation_name() {
    local name="$1"
    if [[ ! "$name" =~ ^[a-z][a-z0-9_-]*$ ]]; then
        error "Invalid investigation name '$name'. Must be lowercase, start with a letter, and contain only letters, numbers, underscores, and hyphens."
    fi
}

# Main script
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <investigation_name>"
        echo ""
        echo "Creates the directory structure for a new production investigation."
        echo ""
        echo "Arguments:"
        echo "  investigation_name    Name of the investigation (lowercase, hyphens/underscores allowed)"
        echo ""
        echo "Example:"
        echo "  $0 api-outage-2026-01-16"
        exit 1
    fi

    local investigation_name="$1"
    validate_investigation_name "$investigation_name"

    # Determine base directory
    local base_dir
    if [[ -d ".deepwork/jobs" ]]; then
        base_dir=".deepwork/jobs"
    elif [[ -d "../.." && -d "../../.deepwork/jobs" ]]; then
        base_dir="../../.deepwork/jobs"
    else
        error "Could not find .deepwork/jobs directory. Run this from project root or env_investigate directory."
    fi

    local investigation_dir="${base_dir}/${investigation_name}"

    # Check if directory exists
    if [[ -d "$investigation_dir" ]]; then
        error "Investigation directory already exists: $investigation_dir"
    fi

    # Create directory structure
    info "Creating investigation directory structure..."
    mkdir -p "${investigation_dir}"
    mkdir -p "${investigation_dir}/artifacts"
    
    info "Created: ${investigation_dir}/"
    info "Created: ${investigation_dir}/artifacts/"

    # Create README with investigation tracking
    cat > "${investigation_dir}/README.md" << EOFREADME
# Investigation: ${investigation_name}

## Status
- **Created**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- **Status**: In Progress
- **Investigator**: [Name]

## Quick Links
- [Triage Document](artifacts/triage.md)
- [Alerts Analysis](artifacts/alerts.md)
- [Metrics Analysis](artifacts/metrics.md)
- [Log Investigation](artifacts/logs.md)
- [Root Cause](artifacts/root_cause.md)
- [Remediation Plan](artifacts/remediation.md)

## Investigation Steps

### 1. Triage & Scope
\`\`\`bash
/env_investigate.triage
\`\`\`
Creates: \`artifacts/triage.md\`

### 2. Check Alerts
\`\`\`bash
/env_investigate.alert_check
\`\`\`
Creates: \`artifacts/alerts.md\`

### 3. Analyze Metrics
\`\`\`bash
/env_investigate.metrics_analysis
\`\`\`
Creates: \`artifacts/metrics.md\`

### 4. Investigate Logs
\`\`\`bash
/env_investigate.log_investigation
\`\`\`
Creates: \`artifacts/logs.md\`

### 5. Root Cause Analysis
\`\`\`bash
/env_investigate.root_cause
\`\`\`
Creates: \`artifacts/root_cause.md\`, \`artifacts/timeline.md\`

### 6. Remediation Plan
\`\`\`bash
/env_investigate.remediation
\`\`\`
Creates: \`artifacts/remediation.md\`

## Notes
[Add investigation-specific notes here]
EOFREADME

    info "Created: ${investigation_dir}/README.md"

    # Success message
    echo ""
    info "Investigation directory created successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. cd ${investigation_dir}"
    echo "  2. Run: /env_investigate.triage"
    echo "  3. Follow the 6-step investigation workflow"
    echo ""
    echo "All artifacts will be created in: ${investigation_dir}/artifacts/"
}

main "$@"
