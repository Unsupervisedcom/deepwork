#!/usr/bin/env bash
#
# install_remote_job.sh - Install a DeepWork job from a remote GitHub repository
#
# Usage: ./install_remote_job.sh <github_url>
#
# Example:
#   ./install_remote_job.sh https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development
#

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

debug() {
    if [[ "${DEBUG:-}" == "1" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Check for required commands
check_dependencies() {
    local missing=()

    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi

    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required commands: ${missing[*]}. Please install them and try again."
    fi
}

# Parse GitHub URL to extract owner, repo, branch, and path
# Supports formats:
#   https://github.com/owner/repo/tree/branch/path/to/dir
#   https://github.com/owner/repo/tree/branch
parse_github_url() {
    local url="$1"

    # Remove trailing slash if present
    url="${url%/}"

    # Extract components using regex
    if [[ "$url" =~ ^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(/.*)?$ ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        BRANCH="${BASH_REMATCH[3]}"
        PATH_IN_REPO="${BASH_REMATCH[4]:-}"
        # Remove leading slash from path
        PATH_IN_REPO="${PATH_IN_REPO#/}"
    else
        error "Invalid GitHub URL format. Expected: https://github.com/owner/repo/tree/branch/path/to/dir"
    fi

    debug "Parsed URL: owner=$OWNER, repo=$REPO, branch=$BRANCH, path=$PATH_IN_REPO"
}

# Extract job name from the path (last component)
get_job_name() {
    local path="$1"
    # Get the last component of the path
    local job_name="${path##*/}"

    if [[ -z "$job_name" ]]; then
        error "Could not determine job name from path: $path"
    fi

    # Validate job name format
    if [[ ! "$job_name" =~ ^[a-z][a-z0-9_]*$ ]]; then
        error "Invalid job name '$job_name'. Job names must be lowercase, start with a letter, and contain only letters, numbers, and underscores."
    fi

    echo "$job_name"
}

# Fetch directory contents from GitHub API
fetch_directory_contents() {
    local owner="$1"
    local repo="$2"
    local branch="$3"
    local path="$4"

    local api_url="https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=${branch}"
    debug "Fetching: $api_url"

    local response
    local http_code

    # Fetch with error handling
    response=$(curl -sS -w "\n%{http_code}" "$api_url" 2>&1) || {
        error "Failed to connect to GitHub API"
    }

    # Extract HTTP code (last line)
    http_code=$(echo "$response" | tail -n1)
    # Extract body (everything except last line)
    response=$(echo "$response" | sed '$d')

    if [[ "$http_code" != "200" ]]; then
        if [[ "$http_code" == "404" ]]; then
            error "Path not found: $path (in $owner/$repo branch $branch)"
        elif [[ "$http_code" == "403" ]]; then
            error "Rate limited by GitHub API. Try again later or set GITHUB_TOKEN environment variable."
        else
            error "GitHub API returned HTTP $http_code: $response"
        fi
    fi

    echo "$response"
}

# Download a single file
download_file() {
    local download_url="$1"
    local dest_path="$2"

    debug "Downloading: $download_url -> $dest_path"

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest_path")"

    if ! curl -sS -L -o "$dest_path" "$download_url"; then
        error "Failed to download: $download_url"
    fi
}

# Recursively download all files in a directory
download_directory() {
    local owner="$1"
    local repo="$2"
    local branch="$3"
    local remote_path="$4"
    local local_base="$5"
    local relative_path="${6:-}"

    local contents
    contents=$(fetch_directory_contents "$owner" "$repo" "$branch" "$remote_path")

    # Check if contents is an array (directory) or object (single file)
    local content_type
    content_type=$(echo "$contents" | jq -r 'type')

    if [[ "$content_type" == "object" ]]; then
        # Single file
        local name download_url
        name=$(echo "$contents" | jq -r '.name')
        download_url=$(echo "$contents" | jq -r '.download_url')

        if [[ "$download_url" != "null" ]]; then
            local dest_path="${local_base}/${relative_path}${name}"
            download_file "$download_url" "$dest_path"
            info "  Downloaded: ${relative_path}${name}"
        fi
    else
        # Directory listing
        local items
        items=$(echo "$contents" | jq -c '.[]')

        while IFS= read -r item; do
            local name type download_url item_path
            name=$(echo "$item" | jq -r '.name')
            type=$(echo "$item" | jq -r '.type')
            download_url=$(echo "$item" | jq -r '.download_url')
            item_path=$(echo "$item" | jq -r '.path')

            if [[ "$type" == "file" ]]; then
                local dest_path="${local_base}/${relative_path}${name}"
                download_file "$download_url" "$dest_path"
                info "  Downloaded: ${relative_path}${name}"
            elif [[ "$type" == "dir" ]]; then
                # Recursively download subdirectory
                mkdir -p "${local_base}/${relative_path}${name}"
                download_directory "$owner" "$repo" "$branch" "$item_path" "$local_base" "${relative_path}${name}/"
            fi
        done <<< "$items"
    fi
}

# Main script
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <github_url>"
        echo ""
        echo "Install a DeepWork job from a remote GitHub repository."
        echo ""
        echo "Arguments:"
        echo "  github_url    URL to a job directory on GitHub"
        echo ""
        echo "Example:"
        echo "  $0 https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development"
        echo ""
        echo "Environment variables:"
        echo "  GITHUB_TOKEN  (optional) GitHub personal access token for higher rate limits"
        echo "  DEBUG=1       (optional) Enable debug output"
        exit 1
    fi

    local github_url="$1"

    # Check dependencies
    check_dependencies

    # Parse the GitHub URL
    parse_github_url "$github_url"

    # Get job name from path
    local job_name
    job_name=$(get_job_name "$PATH_IN_REPO")

    info "Installing remote job: $job_name"
    info "  From: $OWNER/$REPO (branch: $BRANCH)"
    info "  Path: $PATH_IN_REPO"

    # Determine the base path - look for .deepwork directory
    local base_path
    if [[ -d ".deepwork/jobs" ]]; then
        base_path=".deepwork/jobs"
    elif [[ -d "../.deepwork/jobs" ]]; then
        base_path="../.deepwork/jobs"
    else
        # Create from current directory
        base_path=".deepwork/jobs"
        mkdir -p "$base_path"
        info "Created .deepwork/jobs directory"
    fi

    local job_path="${base_path}/${job_name}"

    # Check if job already exists
    if [[ -d "$job_path" ]]; then
        warn "Job '$job_name' already exists at $job_path"
        read -p "Do you want to overwrite it? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Installation cancelled."
            exit 0
        fi
        rm -rf "$job_path"
    fi

    # Create job directory
    mkdir -p "$job_path"

    info "Downloading job files..."

    # Download all files from the remote directory
    download_directory "$OWNER" "$REPO" "$BRANCH" "$PATH_IN_REPO" "$job_path"

    echo ""
    info "Successfully installed job '$job_name' to $job_path"
    echo ""

    # Check for readme and customization instructions
    if [[ -f "$job_path/readme.md" ]] || [[ -f "$job_path/README.md" ]]; then
        warn "This job may require customization!"
        info "Please review the readme file for setup instructions:"
        if [[ -f "$job_path/readme.md" ]]; then
            echo "  $job_path/readme.md"
        else
            echo "  $job_path/README.md"
        fi
    fi

    echo ""
    info "Next steps:"
    echo "  1. Review the job's readme for any required customization"
    echo "  2. Run 'deepwork sync' to generate slash commands"
    echo "  3. Use the job with /${job_name}.<step_name>"
}

main "$@"
