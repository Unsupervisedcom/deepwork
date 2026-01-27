#!/bin/bash
# commit_job_git_commit.sh - Wrapper for git commit invoked via the /commit skill
#
# This script bypasses the PreToolUse hook that blocks direct `git commit` commands.
# It allows the commit job to perform the actual commit after all quality checks pass.

exec git commit "$@"
