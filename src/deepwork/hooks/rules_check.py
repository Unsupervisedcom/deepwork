"""
Rules check hook for DeepWork (v2).

This hook evaluates rules when the agent finishes (after_agent event).
It uses the wrapper system for cross-platform compatibility.

Rule files are loaded from .deepwork/rules/ directory as frontmatter markdown files.

Usage (via shell wrapper):
    claude_hook.sh deepwork.hooks.rules_check
    gemini_hook.sh deepwork.hooks.rules_check

Or directly with platform environment variable:
    DEEPWORK_HOOK_PLATFORM=claude python -m deepwork.hooks.rules_check
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from deepwork.core.command_executor import (
    all_commands_succeeded,
    format_command_errors,
    run_command_action,
)
from deepwork.core.rules_parser import (
    ActionType,
    DetectionMode,
    Rule,
    RuleEvaluationResult,
    RulesParseError,
    evaluate_rules,
    load_rules_from_directory,
)
from deepwork.core.rules_queue import (
    ActionResult,
    QueueEntryStatus,
    RulesQueue,
    compute_trigger_hash,
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


def get_baseline_ref(mode: str) -> str:
    """Get the baseline reference for a compare_to mode."""
    if mode == "base":
        try:
            default_branch = get_default_branch()
            result = subprocess.run(
                ["git", "merge-base", "HEAD", f"origin/{default_branch}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "base"
    elif mode == "default_tip":
        try:
            default_branch = get_default_branch()
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{default_branch}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "default_tip"
    elif mode == "prompt":
        baseline_path = Path(".deepwork/.last_work_tree")
        if baseline_path.exists():
            # Use file modification time as reference
            return str(int(baseline_path.stat().st_mtime))
        return "prompt"
    return mode


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
    """Get files changed since prompt was submitted.

    Returns files that changed since the prompt was submitted, including:
    - Committed changes (compared to captured HEAD ref)
    - Staged changes (not yet committed)
    - Untracked files

    This is used by trigger/safety, set, and pair mode rules to detect
    file modifications during the agent response.
    """
    baseline_ref_path = Path(".deepwork/.last_head_ref")
    changed_files: set[str] = set()

    try:
        # Stage all changes first
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        # If we have a captured HEAD ref, compare committed changes against it
        if baseline_ref_path.exists():
            baseline_ref = baseline_ref_path.read_text().strip()
            if baseline_ref:
                # Get files changed in commits since the baseline
                result = subprocess.run(
                    ["git", "diff", "--name-only", baseline_ref, "HEAD"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    committed_files = set(result.stdout.strip().split("\n"))
                    changed_files.update(f for f in committed_files if f)

        # Also get currently staged changes (in case not everything is committed)
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip():
            staged_files = set(result.stdout.strip().split("\n"))
            changed_files.update(f for f in staged_files if f)

        # Include untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip():
            untracked_files = set(result.stdout.strip().split("\n"))
            changed_files.update(f for f in untracked_files if f)

        return sorted(changed_files)

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


def get_created_files_base() -> list[str]:
    """Get files created (added) relative to branch base."""
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

        # Get only added files (not modified) using --diff-filter=A
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", merge_base, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_added = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Staged new files that don't exist in merge_base
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", "--cached", merge_base],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_added = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Untracked files are by definition "created"
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        all_created = committed_added | staged_added | untracked_files
        return sorted([f for f in all_created if f])

    except subprocess.CalledProcessError:
        return []


def get_created_files_default_tip() -> list[str]:
    """Get files created compared to default branch tip."""
    default_branch = get_default_branch()

    try:
        subprocess.run(["git", "add", "-A"], capture_output=True, check=False)

        # Get only added files using --diff-filter=A
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", f"origin/{default_branch}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        committed_added = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=A",
                "--cached",
                f"origin/{default_branch}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        staged_added = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        # Untracked files are by definition "created"
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

        all_created = committed_added | staged_added | untracked_files
        return sorted([f for f in all_created if f])

    except subprocess.CalledProcessError:
        return []


def get_created_files_prompt() -> list[str]:
    """Get files created since prompt was submitted."""
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

        # Untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_files = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        untracked_files = {f for f in untracked_files if f}

        all_current = current_files | untracked_files

        if baseline_path.exists():
            baseline_files = set(baseline_path.read_text().strip().split("\n"))
            baseline_files = {f for f in baseline_files if f}
            # Created files are those that didn't exist at baseline
            created_files = all_current - baseline_files
            return sorted(created_files)
        else:
            # No baseline means all current files are "new" to this prompt
            return sorted(all_current)

    except (subprocess.CalledProcessError, OSError):
        return []


def get_created_files_for_mode(mode: str) -> list[str]:
    """Get created files for a specific compare_to mode."""
    if mode == "base":
        return get_created_files_base()
    elif mode == "default_tip":
        return get_created_files_default_tip()
    elif mode == "prompt":
        return get_created_files_prompt()
    else:
        return get_created_files_base()


def extract_promise_tags(text: str) -> set[str]:
    """
    Extract rule names from <promise> tags in text.

    Supports both:
    - <promise>Rule Name</promise>
    - <promise>✓ Rule Name</promise>
    """
    # Match with optional checkmark prefix (✓ or ✓ with space)
    pattern = r"<promise>(?:\s*)?(?:✓\s*)?([^<]+)</promise>"
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


def format_rules_message(results: list[RuleEvaluationResult]) -> str:
    """
    Format triggered rules into a concise message for the agent.

    Groups rules by name and uses minimal formatting.
    """
    lines = ["## DeepWork Rules Triggered", ""]
    lines.append(
        "Comply with the following rules. "
        "To mark a rule as addressed, include `<promise>Rule Name</promise>` "
        "in your response."
    )
    lines.append("")

    # Group results by rule name
    by_name: dict[str, list[RuleEvaluationResult]] = {}
    for result in results:
        name = result.rule.name
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(result)

    for name, rule_results in by_name.items():
        rule = rule_results[0].rule
        lines.append(f"## {name}")
        lines.append("")

        # For set/pair modes, show the correspondence violations concisely
        if rule.detection_mode in (DetectionMode.SET, DetectionMode.PAIR):
            for result in rule_results:
                for trigger_file in result.trigger_files:
                    for missing_file in result.missing_files:
                        lines.append(f"{trigger_file} -> {missing_file}")
            lines.append("")

        # Show instructions
        if rule.instructions:
            lines.append(rule.instructions.strip())
            lines.append("")

    return "\n".join(lines)


def rules_check_hook(hook_input: HookInput) -> HookOutput:
    """
    Main hook logic for rules evaluation (v2).

    This is called for after_agent events to check if rules need attention
    before allowing the agent to complete.
    """
    # Only process after_agent events
    if hook_input.event != NormalizedEvent.AFTER_AGENT:
        return HookOutput()

    # Check if rules directory exists
    rules_dir = Path(".deepwork/rules")
    if not rules_dir.exists():
        return HookOutput()

    # Extract conversation context from transcript
    conversation_context = extract_conversation_from_transcript(
        hook_input.transcript_path, hook_input.platform
    )

    # Extract promise tags (case-insensitive)
    promised_rules = extract_promise_tags(conversation_context)

    # Load rules
    try:
        rules = load_rules_from_directory(rules_dir)
    except RulesParseError as e:
        print(f"Error loading rules: {e}", file=sys.stderr)
        return HookOutput()

    if not rules:
        return HookOutput()

    # Initialize queue
    queue = RulesQueue()

    # Group rules by compare_to mode
    rules_by_mode: dict[str, list[Rule]] = {}
    for rule in rules:
        mode = rule.compare_to
        if mode not in rules_by_mode:
            rules_by_mode[mode] = []
        rules_by_mode[mode].append(rule)

    # Evaluate rules and collect results
    prompt_results: list[RuleEvaluationResult] = []
    command_errors: list[str] = []

    for mode, mode_rules in rules_by_mode.items():
        changed_files = get_changed_files_for_mode(mode)
        created_files = get_created_files_for_mode(mode)

        # Skip if no changed or created files
        if not changed_files and not created_files:
            continue

        baseline_ref = get_baseline_ref(mode)

        # Evaluate which rules fire
        results = evaluate_rules(mode_rules, changed_files, promised_rules, created_files)

        for result in results:
            rule = result.rule

            # Compute trigger hash for queue deduplication
            trigger_hash = compute_trigger_hash(
                rule.name,
                result.trigger_files,
                baseline_ref,
            )

            # Check if already in queue (passed/skipped)
            existing = queue.get_entry(trigger_hash)
            if existing and existing.status in (
                QueueEntryStatus.PASSED,
                QueueEntryStatus.SKIPPED,
            ):
                continue

            # Create queue entry if new
            if not existing:
                queue.create_entry(
                    rule_name=rule.name,
                    rule_file=f"{rule.filename}.md",
                    trigger_files=result.trigger_files,
                    baseline_ref=baseline_ref,
                    expected_files=result.missing_files,
                )

            # Handle based on action type
            if rule.action_type == ActionType.COMMAND:
                # Run command action
                if rule.command_action:
                    repo_root = Path.cwd()
                    cmd_results = run_command_action(
                        rule.command_action,
                        result.trigger_files,
                        repo_root,
                    )

                    if all_commands_succeeded(cmd_results):
                        # Command succeeded, mark as passed
                        queue.update_status(
                            trigger_hash,
                            QueueEntryStatus.PASSED,
                            ActionResult(
                                type="command",
                                output=cmd_results[0].stdout if cmd_results else None,
                                exit_code=0,
                            ),
                        )
                    else:
                        # Command failed
                        error_msg = format_command_errors(cmd_results)
                        skip_hint = f"To skip, include `<promise>✓ {rule.name}</promise>` in your response.\n"
                        command_errors.append(f"## {rule.name}\n{error_msg}{skip_hint}")
                        queue.update_status(
                            trigger_hash,
                            QueueEntryStatus.FAILED,
                            ActionResult(
                                type="command",
                                output=error_msg,
                                exit_code=cmd_results[0].exit_code if cmd_results else -1,
                            ),
                        )

            elif rule.action_type == ActionType.PROMPT:
                # Collect for prompt output
                prompt_results.append(result)

    # Build response
    messages: list[str] = []

    # Add command errors if any
    if command_errors:
        messages.append("## Command Rule Errors\n")
        messages.append("The following command rules failed.\n")
        messages.extend(command_errors)
        messages.append("")

    # Add prompt rules if any
    if prompt_results:
        messages.append(format_rules_message(prompt_results))

    if messages:
        return HookOutput(decision="block", reason="\n".join(messages))

    return HookOutput()


def main() -> None:
    """Entry point for the rules check hook."""
    # Determine platform from environment
    platform_str = os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude")
    try:
        platform = Platform(platform_str)
    except ValueError:
        platform = Platform.CLAUDE

    # Run the hook with the wrapper
    exit_code = run_hook(rules_check_hook, platform)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
