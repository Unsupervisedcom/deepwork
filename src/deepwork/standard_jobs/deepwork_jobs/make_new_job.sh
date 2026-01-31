#!/usr/bin/env bash
#
# make_new_job.sh - Create directory structure for a new DeepWork job
#
# Usage: ./make_new_job.sh <job_name>
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
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <job_name> [--scope local|global]"
        echo ""
        echo "Creates the directory structure for a new DeepWork job."
        echo ""
        echo "Arguments:"
        echo "  job_name    Name of the job (lowercase, underscores allowed)"
        echo "  --scope     Installation scope: 'local' (project) or 'global' (XDG config)"
        echo "              Default: local"
        echo ""
        echo "Examples:"
        echo "  $0 competitive_research"
        echo "  $0 competitive_research --scope global"
        exit 1
    fi

    local job_name="$1"
    local scope="local"
    
    # Parse optional --scope argument
    if [[ $# -ge 2 ]] && [[ "$2" == "--scope" ]]; then
        if [[ $# -ge 3 ]]; then
            scope="$3"
            if [[ "$scope" != "local" && "$scope" != "global" ]]; then
                error "Invalid scope '$scope'. Must be 'local' or 'global'."
            fi
        else
            error "--scope requires a value (local or global)"
        fi
    fi
    
    validate_job_name "$job_name"

    # Determine the base path based on scope
    local base_path
    if [[ "$scope" == "global" ]]; then
        # Use XDG config directory for global jobs
        local xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
        base_path="${xdg_config}/deepwork/jobs"
        mkdir -p "$base_path"
        info "Creating global job in $base_path"
    else
        # Local scope - look for .deepwork directory
        if [[ -d ".deepwork/jobs" ]]; then
            base_path=".deepwork/jobs"
        elif [[ -d "../.deepwork/jobs" ]]; then
            base_path="../.deepwork/jobs"
        else
            # Create from current directory
            base_path=".deepwork/jobs"
            mkdir -p "$base_path"
        fi
        info "Creating local job in $base_path"
    fi

    local job_path="${base_path}/${job_name}"

    # Check if job already exists
    if [[ -d "$job_path" ]]; then
        error "Job '$job_name' already exists at $job_path"
    fi

    info "Creating job directory structure for '$job_name'..."

    # Create main job directory and subdirectories
    mkdir -p "$job_path"
    mkdir -p "$job_path/steps"
    mkdir -p "$job_path/hooks"
    mkdir -p "$job_path/templates"

    # Add .gitkeep files to empty directories
    touch "$job_path/hooks/.gitkeep"
    touch "$job_path/templates/.gitkeep"

    # Create AGENTS.md file
    cat > "$job_path/AGENTS.md" << 'EOF'
# Job Management

This folder and its subfolders are managed using the `deepwork_jobs` slash commands.

## Recommended Commands

- `/deepwork_jobs.define` - Create or modify the job.yml specification
- `/deepwork_jobs.implement` - Generate step instruction files from the specification
- `/deepwork_jobs.learn` - Improve instructions based on execution learnings

## Directory Structure

```
.
├── AGENTS.md          # This file - project context and guidance
├── job.yml            # Job specification (created by /deepwork_jobs.define)
├── steps/             # Step instruction files (created by /deepwork_jobs.implement)
│   └── *.md           # One file per step
├── hooks/             # Custom validation scripts and prompts
│   └── *.md|*.sh      # Hook files referenced in job.yml
└── templates/         # Example file formats and templates
    └── *.md|*.yml     # Templates referenced in step instructions
```

## Editing Guidelines

1. **Use slash commands** for structural changes (adding steps, modifying job.yml)
2. **Direct edits** are fine for minor instruction tweaks
3. **Run `/deepwork_jobs.learn`** after executing job steps to capture improvements
4. **Run `deepwork sync`** after any changes to regenerate commands
EOF

    info "Created directory structure:"
    echo "  $job_path/"
    echo "  ├── AGENTS.md"
    echo "  ├── steps/"
    echo "  ├── hooks/.gitkeep"
    echo "  └── templates/.gitkeep"

    echo ""
    info "Next steps:"
    echo "  1. Run '/deepwork_jobs.define' to create the job.yml specification"
    echo "  2. Run '/deepwork_jobs.implement' to generate step instructions"
    echo "  3. Run 'deepwork sync' to create slash commands"
}

main "$@"
