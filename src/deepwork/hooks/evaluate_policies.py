"""
Policy evaluation module for DeepWork hooks.

This module is called by the policy_stop_hook.sh script to evaluate which policies
should fire based on changed files and conversation context.

Usage:
    python -m deepwork.hooks.evaluate_policies \
        --policy-file .deepwork.policy.yml \
        --changed-files "file1.py\nfile2.py"

The conversation context is read from stdin and checked for <promise> tags
that indicate policies have already been addressed.

Output is JSON suitable for Claude Code Stop hooks:
    {"decision": "block", "reason": "..."}  # Block stop, policies need attention
    {}  # No policies fired, allow stop
"""

import argparse
import json
import re
import sys
from pathlib import Path

from deepwork.core.policy_parser import (
    PolicyParseError,
    evaluate_policies,
    parse_policy_file,
)


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
    parser.add_argument(
        "--changed-files",
        type=str,
        required=True,
        help="Newline-separated list of changed files",
    )

    args = parser.parse_args()

    # Parse changed files (newline-separated)
    changed_files = [f.strip() for f in args.changed_files.split("\n") if f.strip()]

    if not changed_files:
        # No files changed, nothing to evaluate
        print("{}")
        return

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

    # Parse and evaluate policies
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

    # Evaluate which policies fire
    fired_policies = evaluate_policies(policies, changed_files, promised_policies)

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
