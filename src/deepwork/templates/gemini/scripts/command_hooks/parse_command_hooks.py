#!/usr/bin/env python3
"""
parse_command_hooks.py - Helper for Gemini command hook emulation

This module provides utilities for emulating Claude's command-level hooks
in Gemini CLI, which doesn't natively support per-command hooks.

The approach:
1. BeforeAgent hook captures the slash command from user prompt
2. State is stored in .deepwork/.command_hook_state.json
3. Hooks are looked up from job.yml definitions
4. AfterAgent hook reads state and runs post-execution hooks

Usage:
    # Detect slash command and save state
    python parse_command_hooks.py detect --prompt "User said /deepwork_jobs:define"

    # Get hooks for a lifecycle event
    python parse_command_hooks.py get-hooks --event before_prompt
    python parse_command_hooks.py get-hooks --event after_agent

    # Execute hooks for an event
    python parse_command_hooks.py run-hooks --event after_agent [--transcript-path /path/to/transcript]

    # Clear state (for cleanup)
    python parse_command_hooks.py clear
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# State file location - in the .deepwork directory (gitignored)
STATE_FILE = Path(".deepwork/.command_hook_state.json")

# Pattern to match Gemini slash commands: /job_name:step_id
# Supports both formats: /job_name:step_id and /job_name/step_id
SLASH_COMMAND_PATTERN = re.compile(r"(?:^|\s)/([a-z][a-z0-9_]*)[:/]([a-z][a-z0-9_]*)\b", re.IGNORECASE)


def find_project_root() -> Path:
    """Find the project root by looking for .deepwork or .gemini directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".deepwork").exists() or (current / ".gemini").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_state_file_path() -> Path:
    """Get the full path to the state file."""
    root = find_project_root()
    return root / STATE_FILE


def load_state() -> dict[str, Any]:
    """Load the current command hook state."""
    state_path = get_state_file_path()
    if state_path.exists():
        try:
            with open(state_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"slash_command": None, "job_name": None, "step_id": None, "hooks": {}}


def save_state(state: dict[str, Any]) -> None:
    """Save the command hook state."""
    state_path = get_state_file_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_state() -> None:
    """Clear the command hook state."""
    state_path = get_state_file_path()
    if state_path.exists():
        state_path.unlink()


def detect_slash_command(prompt: str) -> tuple[str | None, str | None, str | None]:
    """
    Detect a slash command in the user prompt.

    Returns:
        Tuple of (full_command, job_name, step_id) or (None, None, None)
    """
    match = SLASH_COMMAND_PATTERN.search(prompt)
    if match:
        job_name = match.group(1).lower()
        step_id = match.group(2).lower()
        # Reconstruct with colon separator (Gemini convention)
        full_command = f"{job_name}:{step_id}"
        return full_command, job_name, step_id
    return None, None, None


def find_job_yml(job_name: str) -> Path | None:
    """
    Find the job.yml file for a given job name.

    Searches in:
    1. .deepwork/jobs/{job_name}/job.yml (user-defined jobs)
    2. Standard jobs bundled with deepwork (via deepwork module)
    """
    root = find_project_root()

    # Check user-defined jobs first
    user_job = root / ".deepwork" / "jobs" / job_name / "job.yml"
    if user_job.exists():
        return user_job

    # Check standard jobs via deepwork package
    try:
        import deepwork
        pkg_root = Path(deepwork.__file__).parent
        standard_job = pkg_root / "standard_jobs" / job_name / "job.yml"
        if standard_job.exists():
            return standard_job
    except ImportError:
        pass

    return None


def parse_job_hooks(job_yml_path: Path, step_id: str) -> dict[str, list[dict[str, Any]]]:
    """
    Parse hooks from a job.yml file for a specific step.

    Returns:
        Dict mapping lifecycle events to lists of hook actions
    """
    import yaml

    try:
        with open(job_yml_path, encoding="utf-8") as f:
            job_def = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        print(f"Warning: Could not parse job.yml: {e}", file=sys.stderr)
        return {}

    hooks: dict[str, list[dict[str, Any]]] = {}

    # Find the step
    steps = job_def.get("steps", [])
    step = None
    for s in steps:
        if s.get("id") == step_id:
            step = s
            break

    if not step:
        return hooks

    # Handle new hooks format: hooks: { event: [actions] }
    if "hooks" in step and isinstance(step["hooks"], dict):
        for event, actions in step["hooks"].items():
            if isinstance(actions, list):
                hooks[event] = actions

    # Handle deprecated stop_hooks (maps to after_agent)
    if "stop_hooks" in step:
        stop_hooks = step["stop_hooks"]
        if isinstance(stop_hooks, list):
            hooks["after_agent"] = stop_hooks

    return hooks


def build_hook_context(hook_action: dict[str, Any], job_yml_path: Path) -> dict[str, Any]:
    """
    Build a hook execution context from a hook action definition.

    Hook actions can be:
    - {"prompt": "inline prompt text"}
    - {"prompt_file": "path/to/prompt.md"}
    - {"script": "path/to/script.sh"}
    """
    context: dict[str, Any] = {"type": "unknown", "content": ""}
    job_dir = job_yml_path.parent

    if "prompt" in hook_action:
        context["type"] = "prompt"
        context["content"] = hook_action["prompt"]
    elif "prompt_file" in hook_action:
        context["type"] = "prompt"
        prompt_path = job_dir / hook_action["prompt_file"]
        if prompt_path.exists():
            context["content"] = prompt_path.read_text(encoding="utf-8")
        else:
            context["content"] = f"[Hook prompt file not found: {hook_action['prompt_file']}]"
    elif "script" in hook_action:
        context["type"] = "script"
        context["script"] = str(job_dir / hook_action["script"])
        context["content"] = hook_action["script"]

    return context


def execute_hook(hook_context: dict[str, Any], transcript_path: str | None = None) -> dict[str, Any]:
    """
    Execute a single hook and return the result.

    For script hooks: Runs the script with optional transcript path
    For prompt hooks: Returns the prompt content (to be injected into conversation)

    Returns:
        Dict with 'success', 'output', and optionally 'inject_prompt'
    """
    result: dict[str, Any] = {"success": True, "output": "", "type": hook_context["type"]}

    if hook_context["type"] == "script":
        script_path = hook_context.get("script", "")
        if not script_path or not Path(script_path).exists():
            result["success"] = False
            result["output"] = f"Script not found: {script_path}"
            return result

        try:
            # Build environment with transcript path if available
            env = os.environ.copy()
            if transcript_path:
                env["TRANSCRIPT_PATH"] = transcript_path

            proc = subprocess.run(
                ["/bin/bash", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                cwd=find_project_root(),
            )
            result["output"] = proc.stdout
            if proc.returncode == 2:
                # Exit code 2 = blocking error
                result["success"] = False
                result["output"] = proc.stderr or proc.stdout
            elif proc.returncode != 0:
                # Non-zero but not 2 = warning
                result["output"] = proc.stderr or proc.stdout
        except subprocess.TimeoutExpired:
            result["success"] = False
            result["output"] = "Hook script timed out"
        except OSError as e:
            result["success"] = False
            result["output"] = f"Failed to run hook script: {e}"

    elif hook_context["type"] == "prompt":
        # Prompt hooks inject text back into the conversation
        result["inject_prompt"] = hook_context["content"]
        result["output"] = "[Prompt hook content ready for injection]"

    return result


def cmd_detect(args: argparse.Namespace) -> int:
    """Handle the 'detect' command."""
    prompt = args.prompt or ""

    # If no prompt provided, try reading from stdin
    if not prompt and not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            # Try to parse as JSON (Gemini hook input format)
            try:
                hook_input = json.loads(stdin_data)
                # Gemini BeforeAgent hook might have prompt in different fields
                prompt = hook_input.get("prompt", "") or hook_input.get("user_prompt", "") or hook_input.get("input", "") or stdin_data
            except json.JSONDecodeError:
                prompt = stdin_data
        except Exception:
            prompt = ""

    slash_command, job_name, step_id = detect_slash_command(prompt)

    # Initialize state
    state: dict[str, Any] = {
        "slash_command": slash_command,
        "job_name": job_name,
        "step_id": step_id,
        "hooks": {},
    }

    # If we found a command, look up its hooks
    if job_name and step_id:
        job_yml = find_job_yml(job_name)
        if job_yml:
            hooks = parse_job_hooks(job_yml, step_id)
            # Convert hook actions to executable contexts
            state["hooks"] = {}
            state["job_yml_path"] = str(job_yml)
            for event, actions in hooks.items():
                state["hooks"][event] = [
                    build_hook_context(action, job_yml) for action in actions
                ]

    save_state(state)

    # Output the detected command info
    output = {
        "slash_command": slash_command,
        "job_name": job_name,
        "step_id": step_id,
        "has_hooks": bool(state["hooks"]),
    }
    print(json.dumps(output))
    return 0


def cmd_get_hooks(args: argparse.Namespace) -> int:
    """Handle the 'get-hooks' command."""
    state = load_state()
    event = args.event

    hooks = state.get("hooks", {}).get(event, [])
    print(json.dumps(hooks, indent=2))
    return 0


def cmd_run_hooks(args: argparse.Namespace) -> int:
    """Handle the 'run-hooks' command."""
    state = load_state()
    event = args.event
    transcript_path = args.transcript_path

    hooks = state.get("hooks", {}).get(event, [])

    if not hooks:
        # No hooks to run
        print(json.dumps({"executed": 0, "results": []}))
        return 0

    results = []
    all_success = True
    prompt_injections = []

    for hook_context in hooks:
        result = execute_hook(hook_context, transcript_path)
        results.append(result)
        if not result.get("success", True):
            all_success = False
        if "inject_prompt" in result:
            prompt_injections.append(result["inject_prompt"])

    output = {
        "executed": len(hooks),
        "success": all_success,
        "results": results,
    }

    # For prompt hooks, include the combined injection text
    if prompt_injections:
        output["inject_prompt"] = "\n\n".join(prompt_injections)

    print(json.dumps(output, indent=2))

    # Return exit code 2 if any hook failed (blocking)
    return 0 if all_success else 2


def cmd_clear(args: argparse.Namespace) -> int:
    """Handle the 'clear' command."""
    clear_state()
    print(json.dumps({"cleared": True}))
    return 0


def cmd_get_state(args: argparse.Namespace) -> int:
    """Handle the 'get-state' command - output current state."""
    state = load_state()
    print(json.dumps(state, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Helper for Gemini command hook emulation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # detect command
    detect_parser = subparsers.add_parser(
        "detect", help="Detect slash command in prompt and save state"
    )
    detect_parser.add_argument(
        "--prompt", "-p", help="The user prompt to analyze"
    )
    detect_parser.set_defaults(func=cmd_detect)

    # get-hooks command
    get_hooks_parser = subparsers.add_parser(
        "get-hooks", help="Get hooks for a lifecycle event"
    )
    get_hooks_parser.add_argument(
        "--event", "-e", required=True,
        help="Lifecycle event (before_prompt, after_agent, etc.)"
    )
    get_hooks_parser.set_defaults(func=cmd_get_hooks)

    # run-hooks command
    run_hooks_parser = subparsers.add_parser(
        "run-hooks", help="Execute hooks for a lifecycle event"
    )
    run_hooks_parser.add_argument(
        "--event", "-e", required=True,
        help="Lifecycle event to run hooks for"
    )
    run_hooks_parser.add_argument(
        "--transcript-path", "-t",
        help="Path to session transcript file"
    )
    run_hooks_parser.set_defaults(func=cmd_run_hooks)

    # clear command
    clear_parser = subparsers.add_parser(
        "clear", help="Clear the command hook state"
    )
    clear_parser.set_defaults(func=cmd_clear)

    # get-state command
    state_parser = subparsers.add_parser(
        "get-state", help="Get current command hook state"
    )
    state_parser.set_defaults(func=cmd_get_state)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
