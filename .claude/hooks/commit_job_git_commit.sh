#!/bin/bash
# commit_job_git_commit.sh - Wrapper for git commit invoked via the /commit skill

exec git commit "$@"
