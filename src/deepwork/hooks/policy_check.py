"""
Policy check hook for DeepWork.

This hook evaluates policies when the agent finishes (after_agent event).
It uses the wrapper system for cross-platform compatibility.

Usage (via shell wrapper):
    claude_hook.sh deepwork.hooks.policy_check
    gemini_hook.sh deepwork.hooks.policy_check

Or directly with platform environment variable:
    DEEPWORK_HOOK_PLATFORM=claude python -m deepwork.hooks.policy_check
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from deepwork.core.policy_parser import (
    Policy,
    PolicyParseError,
    evaluate_policy,
    parse_policy_file,
)
from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    run_hook,
)


def get_default_branch() -> str:
    """Get the default branch name (main or master)."""
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("/")[-1]
    except subprocess.CalledProcessError:
        pass

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

    return "main"


def get_changed_files_base() -> list[str]:
    """Get files changed relative to branch base."""
    default_branch = get_default_branch()

    try:
        result = subprocess.run(
            ["git", "merge-base", "HEAD", f"origin/{default_branch}"],
            capture_output=True,
            text=True,
            check=True,
        )
        merge_base = result.stdout.strip()

        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        result = subprocess.run(
            ["git", "diff", "--name-only", merge_base, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

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
    """Get files changed compared to default branch tip."""
    default_branch = get_default_branch()

    try:
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        result = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{default_branch}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

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
    """Get files changed since prompt was submitted."""
    baseline_path = Path(".deepwork/.last_work_tree")

    try:
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        current_files = {f for f in current_files if f}

        if baseline_path.exists():
            baseline_files = set(baseline_path.read_text().strip().split("\n"))
            baseline_files = {f for f in baseline_files if f}
            new_files = current_files - baseline_files
            return sorted(new_files)
        else:
            return sorted(current_files)

    except (subprocess.CalledProcessError, OSError):
        return []


def get_changed_files_for_mode(mode: str) -> list[str]:
    """Get changed files for a specific compare_to mode."""
    if mode == "base":
        return get_changed_files_base()
    elif mode == "default_tip":
        return get_changed_files_default_tip()
    elif mode == "prompt":
        return get_changed_files_prompt()
    else:
        return get_changed_files_base()


def extract_promise_tags(text: str) -> set[str]:
    """Extract policy names from <promise> tags in text."""
    pattern = r"<promise>✓\s*([^<]+)</promise>"
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
    return {m.strip() for m in matches}


def extract_conversation_from_transcript(transcript_path: str, platform: Platform) -> str:
    """
    Extract conversation text from a transcript file.

    Handles platform-specific transcript formats.
    """
    if not transcript_path or not Path(transcript_path).exists():
        return ""

    try:
        content = Path(transcript_path).read_text()

        if platform == Platform.CLAUDE:
            # Claude uses JSONL format - each line is a JSON object
            conversation_parts = []
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("role") == "assistant":
                        message_content = entry.get("message", {}).get("content", [])
                        for part in message_content:
                            if part.get("type") == "text":
                                conversation_parts.append(part.get("text", ""))
                except json.JSONDecodeError:
                    continue
            return "\n".join(conversation_parts)

        elif platform == Platform.GEMINI:
            # Gemini uses JSON format
            try:
                data = json.loads(content)
                # Extract text from messages
                conversation_parts = []
                messages = data.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "model":
                        parts = msg.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                conversation_parts.append(part["text"])
                            elif isinstance(part, str):
                                conversation_parts.append(part)
                return "\n".join(conversation_parts)
            except json.JSONDecodeError:
                return ""

        return ""
    except Exception:
        return ""


def format_policy_message(policies: list[Policy]) -> str:
    """Format triggered policies into a message for the agent."""
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


def policy_check_hook(hook_input: HookInput) -> HookOutput:
    """
    Main hook logic for policy evaluation.

    This is called for after_agent events to check if policies need attention
    before allowing the agent to complete.
    """
    # Only process after_agent events
    if hook_input.event != NormalizedEvent.AFTER_AGENT:
        return HookOutput()

    # Check if policy file exists
    policy_path = Path(".deepwork.policy.yml")
    if not policy_path.exists():
        return HookOutput()

    # Extract conversation context from transcript
    conversation_context = extract_conversation_from_transcript(
        hook_input.transcript_path, hook_input.platform
    )

    # Extract promise tags
    promised_policies = extract_promise_tags(conversation_context)

    # Parse policies
    try:
        policies = parse_policy_file(policy_path)
    except PolicyParseError as e:
        print(f"Error parsing policy file: {e}", file=sys.stderr)
        return HookOutput()

    if not policies:
        return HookOutput()

    # Group policies by compare_to mode
    policies_by_mode: dict[str, list[Policy]] = {}
    for policy in policies:
        mode = policy.compare_to
        if mode not in policies_by_mode:
            policies_by_mode[mode] = []
        policies_by_mode[mode].append(policy)

    # Evaluate policies
    fired_policies: list[Policy] = []
    for mode, mode_policies in policies_by_mode.items():
        changed_files = get_changed_files_for_mode(mode)
        if not changed_files:
            continue

        for policy in mode_policies:
            if policy.name in promised_policies:
                continue
            if evaluate_policy(policy, changed_files):
                fired_policies.append(policy)

    if not fired_policies:
        return HookOutput()

    # Format message and return blocking response
    message = format_policy_message(fired_policies)
    return HookOutput(decision="block", reason=message)


def main() -> None:
    """Entry point for the policy check hook."""
    # Determine platform from environment
    platform_str = os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude")
    try:
        platform = Platform(platform_str)
    except ValueError:
        platform = Platform.CLAUDE

    # Run the hook with the wrapper
    exit_code = run_hook(policy_check_hook, platform)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
