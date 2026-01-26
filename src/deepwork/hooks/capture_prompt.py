#!/usr/bin/env python3
"""
capture_prompt.py - Captures the git work tree state at prompt submission.

This is the cross-platform Python equivalent of capture_prompt_work_tree.sh.

This script creates a snapshot of ALL tracked files at the time the prompt
is submitted. This baseline is used for rules with compare_to: prompt and
created: mode to detect truly NEW files (not modifications to existing ones).

The baseline contains ALL tracked files (not just changed files) so that
the rules_check hook can determine which files are genuinely new vs which
files existed before and were just modified.

It also captures the HEAD commit ref so that committed changes can be detected
by comparing HEAD at Stop time to the captured ref.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def capture_work_tree(project_dir: Path | None = None) -> int:
    """
    Capture the current git work tree state.

    Args:
        project_dir: Project directory (default: current directory)

    Returns:
        0 on success, non-zero on error
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir)

    deepwork_dir = project_dir / ".deepwork"

    # Ensure .deepwork directory exists
    deepwork_dir.mkdir(parents=True, exist_ok=True)

    # Save the current HEAD commit ref for detecting committed changes
    head_ref_file = deepwork_dir / ".last_head_ref"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            check=False,
        )
        head_ref = result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        head_ref = ""

    head_ref_file.write_text(head_ref + "\n", encoding="utf-8")

    # Get all tracked files
    tracked_files: set[str] = set()
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            check=False,
        )
        if result.returncode == 0:
            tracked_files.update(line for line in result.stdout.strip().split("\n") if line)
    except Exception:
        pass

    # Also include untracked files that exist at prompt time
    # These are files the user may have created before submitting the prompt
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            check=False,
        )
        if result.returncode == 0:
            tracked_files.update(line for line in result.stdout.strip().split("\n") if line)
    except Exception:
        pass

    # Sort and write to file
    work_tree_file = deepwork_dir / ".last_work_tree"
    sorted_files = sorted(tracked_files)
    work_tree_file.write_text("\n".join(sorted_files) + "\n" if sorted_files else "", encoding="utf-8")

    return 0


def main() -> int:
    """Main entry point for the capture_prompt hook."""
    import json
    import os

    # Try to get project directory from environment or stdin
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("GEMINI_PROJECT_DIR")

    # Also try to read from stdin (hook input JSON)
    if not sys.stdin.isatty():
        try:
            input_data = json.load(sys.stdin)
            if not project_dir:
                project_dir = input_data.get("cwd")
        except (json.JSONDecodeError, EOFError):
            pass

    if project_dir:
        return capture_work_tree(Path(project_dir))
    else:
        return capture_work_tree()


if __name__ == "__main__":
    sys.exit(main())
