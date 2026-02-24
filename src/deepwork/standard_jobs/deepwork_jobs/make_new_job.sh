#!/usr/bin/env bash
#
# make_new_job.sh - Create directory structure for a new DeepWork job
#
# Usage: ./make_new_job.sh <job_name>
#
# Input:
#   job_name - Lowercase name using only letters, numbers, and underscores.
#              Must start with a letter.
#
# Output:
#   Creates .deepwork/jobs/<job_name>/ at the git repository root with
#   subdirectories: steps/, hooks/, templates/, scripts/, plus AGENTS.md
#   and optionally .deepreview (if template.deepreview exists alongside
#   this script).
#
# Exit codes:
#   0 - Success
#   1 - Usage error (missing args, invalid job name, job already exists,
#       not a git repository)
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

# Validate job name format
validate_job_name() {
    local name="$1"
    if [[ ! "$name" =~ ^[a-z][a-z0-9_]*$ ]]; then
        error "Invalid job name '$name'. Must be lowercase, start with a letter, and contain only letters, numbers, and underscores."
    fi
}

# Main script
main() {
    local script_dir
    script_dir="$(cd "$(dirname "$0")" && pwd)"

    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <job_name>"
        echo ""
        echo "Creates the directory structure for a new DeepWork job."
        echo ""
        echo "Arguments:"
        echo "  job_name    Name of the job (lowercase, underscores allowed)"
        echo ""
        echo "Example:"
        echo "  $0 competitive_research"
        exit 1
    fi

    local job_name="$1"
    validate_job_name "$job_name"

    # Determine the base path by anchoring to the git repository root
    local repo_root
    if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
        error "Not inside a git repository. Run this from within a git repo."
    fi
    local base_path="${repo_root}/.deepwork/jobs"
    mkdir -p "$base_path"

    local job_path="${base_path}/${job_name}"

    # Check if job already exists
    if [[ -d "$job_path" ]]; then
        error "Job '$job_name' already exists at $job_path"
    fi

    info "Creating job directory structure for '$job_name'..."

    # Create main job directory and subdirectories
    mkdir -p "$job_path"/{steps,hooks,templates,scripts}

    # Add .gitkeep files to empty directories
    touch "$job_path"/{hooks,templates,scripts}/.gitkeep

    # Create AGENTS.md file
    cat > "$job_path/AGENTS.md" << 'EOF'
# Job Management

This folder and its subfolders are managed using `deepwork_jobs` workflows.

## Recommended Workflows

- `deepwork_jobs/new_job` - Full lifecycle: define → implement → test → iterate
- `deepwork_jobs/learn` - Improve instructions based on execution learnings
- `deepwork_jobs/repair` - Clean up and migrate from prior DeepWork versions

## Directory Structure

```
.
├── .deepreview        # Review rules for the job itself using Deepwork Reviews
├── AGENTS.md          # This file - project context and guidance
├── job.yml            # Job specification (created by define step)
├── steps/             # Step instruction files (created by implement step)
│   └── *.md           # One file per step
├── hooks/             # Custom validation scripts and prompts
│   └── *.md|*.sh      # Hook files referenced in job.yml
├── scripts/           # Reusable scripts and utilities created during job execution
│   └── *.sh|*.py      # Helper scripts referenced in step instructions
└── templates/         # Example file formats and templates
    └── *.md|*.yml     # Templates referenced in step instructions
```

## Editing Guidelines

1. **Use workflows** for structural changes (adding steps, modifying job.yml)
2. **Direct edits** are fine for minor instruction tweaks
EOF

    # Copy .deepreview template if available
    if [[ -f "$script_dir/template.deepreview" ]]; then
        cp "$script_dir/template.deepreview" "$job_path/.deepreview"
    fi

    info "Created directory structure:"
    echo "  $job_path/"
    if [[ -f "$job_path/.deepreview" ]]; then
        echo "  ├── .deepreview"
    fi
    echo "  ├── AGENTS.md"
    echo "  ├── steps/"
    echo "  ├── hooks/.gitkeep"
    echo "  ├── scripts/.gitkeep"
    echo "  └── templates/.gitkeep"
}

main "$@"
