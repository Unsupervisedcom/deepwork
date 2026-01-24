#!/bin/bash
# commit_job_git_commit.sh - Wrapper for git commit used by the commit job
#
# This script is used by the commit job's commit_and_push step to perform
# git commits. It passes all arguments through to git commit.
#
# This script exists to allow the commit job to bypass the git commit block
# that is enforced for regular tool use. The block ensures that all commits
# go through the /commit skill workflow, but the commit job itself needs
# to be able to perform the actual commit.
#
# Usage:
#   commit_job_git_commit.sh [git commit arguments...]
#
# Examples:
#   commit_job_git_commit.sh -m "feat: add new feature"
#   commit_job_git_commit.sh -m "$(cat <<'EOF'
#   Multi-line commit message
#   EOF
#   )"

exec git commit "$@"
