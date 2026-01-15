"""
Policy evaluation module for DeepWork hooks.

This module is called by the policy_stop_hook.sh script to evaluate which policies
should fire based on changed files and conversation context.

Usage:
    python -m deepwork.hooks.evaluate_policies \
        --policy-file .deepwork.policy.yml

The conversation context is read from stdin and checked for <promise> tags
that indicate policies have already been addressed.

Changed files are computed based on each policy's compare_to setting:
- base: Compare to merge-base with default branch (default)
- default_tip: Two-dot diff against default branch tip
- prompt: Compare to state captured at prompt submission

Output is JSON suitable for Claude Code Stop hooks:
    {"decision": "block", "reason": "..."}  # Block stop, policies need attention
    {}  # No policies fired, allow stop
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from deepwork.core.policy_parser import (
    DEFAULT_COMPARE_TO,
    Policy,
    PolicyParseError,
    evaluate_policy,
    parse_policy_file,
)


def get_default_branch() -> str:
    """
    Get the default branch name (main or master).

    Returns:
        Default branch name, or "main" if cannot be determined.
    """
    # Try to get the default branch from remote HEAD
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Output is like "refs/remotes/origin/main"
        return result.stdout.strip().split("/")[-1]
    except subprocess.CalledProcessError:
        pass

    # Try common default branch names
    for branch in ["main", "master"]:
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{branch}"],
                capture_output=True,
                check=True,
            )
            return branch
        except subprocess.CalledProcessError:
            continue

    # Fall back to main
    return "main"


def get_changed_files_base() -> list[str]:
    """
    Get files changed relative to the base of the current branch.

    This finds the merge-base between the current branch and the default branch,
    then returns all files changed since that point.

    Returns:
        List of changed file paths.
    """
    default_branch = get_default_branch()

    try:
        # Get the merge-base (where current branch diverged from default)
        result = subprocess.run(
            ["git", "merge-base", "HEAD", f"origin/{default_branch}"],
            capture_output=True,
            text=True,
            check=True,
        )
        merge_base = result.stdout.strip()

        # Stage all changes so they appear in diff
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        # Get files changed since merge-base (including staged)
        result = subprocess.run(
            ["git", "diff", "--name-only", merge_base, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Also get staged changes not yet committed
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        all_files = committed_files | staged_files | untracked_files
        return sorted([f for f in all_files if f])

    except subprocess.CalledProcessError:
        return []


def get_changed_files_default_tip() -> list[str]:
    """
    Get files changed compared to the tip of the default branch.

    This does a two-dot diff: what's different between HEAD and origin/default.

    Returns:
        List of changed file paths.
    """
    default_branch = get_default_branch()

    try:
        # Stage all changes so they appear in diff
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        # Two-dot diff against default branch tip
        result = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{default_branch}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Also get staged changes not yet committed
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        all_files = committed_files | staged_files | untracked_files
        return sorted([f for f in all_files if f])

    except subprocess.CalledProcessError:
        return []


def get_changed_files_prompt() -> list[str]:
    """
    Get files changed since the prompt was submitted.

    This compares against the baseline captured by capture_prompt_work_tree.sh.

    Returns:
        List of changed file paths.
    """
    baseline_path = Path(".deepwork/.last_work_tree")

    try:
        # Stage all changes
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        # Get current changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        all_current = current_files | untracked_files
        all_current = {f for f in all_current if f}

        if baseline_path.exists():
            # Read baseline and find new files
            baseline_files = set(baseline_path.read_text().strip().split("\n"))
            baseline_files = {f for f in baseline_files if f}
            # Return files that are in current but not in baseline
            new_files = all_current - baseline_files
            return sorted(new_files)
        else:
            # No baseline, return all current changes
            return sorted(all_current)

    except (subprocess.CalledProcessError, OSError):
        return []


def get_changed_files_for_mode(mode: str) -> list[str]:
    """
    Get changed files for a specific compare_to mode.

    Args:
        mode: One of 'base', 'default_tip', or 'prompt'

    Returns:
        List of changed file paths.
    """
    if mode == "base":
        return get_changed_files_base()
    elif mode == "default_tip":
        return get_changed_files_default_tip()
    elif mode == "prompt":
        return get_changed_files_prompt()
    else:
        # Unknown mode, fall back to base
        return get_changed_files_base()


def extract_promise_tags(text: str) -> set[str]:
    """
    Extract policy names from <promise> tags in text.

    Supported format:
    - <promise>✓ Policy Name</promise>

    Args:
        text: Text to search for promise tags

    Returns:
        Set of policy names that have been promised/addressed
    """
    # Match <promise>✓ Policy Name</promise> and extract the policy name
    pattern = r"<promise>✓\s*([^<]+)</promise>"
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
    return {m.strip() for m in matches}


def format_policy_message(policies: list) -> str:
    """
    Format triggered policies into a message for the agent.

    Args:
        policies: List of Policy objects that fired

    Returns:
        Formatted message with all policy instructions
    """
    lines = ["## DeepWork Policies Triggered", ""]
    lines.append(
        "Comply with the following policies. "
        "To mark a policy as addressed, include `<promise>✓ Policy Name</promise>` "
        "in your response (replace Policy Name with the actual policy name)."
    )
    lines.append("")

    for policy in policies:
        lines.append(f"### Policy: {policy.name}")
        lines.append("")
        lines.append(policy.instructions.strip())
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Main entry point for policy evaluation CLI."""
    parser = argparse.ArgumentParser(
        description="Evaluate DeepWork policies based on changed files"
    )
    parser.add_argument(
        "--policy-file",
        type=str,
        required=True,
        help="Path to .deepwork.policy.yml file",
    )

    args = parser.parse_args()

    # Check if policy file exists
    policy_path = Path(args.policy_file)
    if not policy_path.exists():
        # No policy file, nothing to evaluate
        print("{}")
        return

    # Read conversation context from stdin (if available)
    conversation_context = ""
    if not sys.stdin.isatty():
        try:
            conversation_context = sys.stdin.read()
        except Exception:
            pass

    # Extract promise tags from conversation
    promised_policies = extract_promise_tags(conversation_context)

    # Parse policies
    try:
        policies = parse_policy_file(policy_path)
    except PolicyParseError as e:
        # Log error to stderr, return empty result
        print(f"Error parsing policy file: {e}", file=sys.stderr)
        print("{}")
        return

    if not policies:
        # No policies defined
        print("{}")
        return

    # Group policies by compare_to mode to minimize git calls
    policies_by_mode: dict[str, list[Policy]] = {}
    for policy in policies:
        mode = policy.compare_to
        if mode not in policies_by_mode:
            policies_by_mode[mode] = []
        policies_by_mode[mode].append(policy)

    # Get changed files for each mode and evaluate policies
    fired_policies: list[Policy] = []
    for mode, mode_policies in policies_by_mode.items():
        changed_files = get_changed_files_for_mode(mode)
        if not changed_files:
            continue

        for policy in mode_policies:
            # Skip if already promised
            if policy.name in promised_policies:
                continue
            # Evaluate this policy
            if evaluate_policy(policy, changed_files):
                fired_policies.append(policy)

    if not fired_policies:
        # No policies fired
        print("{}")
        return

    # Format output for Claude Code Stop hooks
    # Use "decision": "block" to prevent Claude from stopping
    message = format_policy_message(fired_policies)
    result = {
        "decision": "block",
        "reason": message,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
