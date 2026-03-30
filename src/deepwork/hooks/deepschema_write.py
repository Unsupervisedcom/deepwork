"""PostToolUse hook for Write/Edit — DeepSchema validation.

Fires after a file is written or edited. Finds applicable DeepSchemas,
injects a conformance note, and runs verification_bash_command and
json_schema_path validation. Reports errors via additionalContext.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    output_hook_error,
    run_hook,
)


def deepschema_write_hook(hook_input: HookInput) -> HookOutput:
    """Post-write hook: validate against applicable DeepSchemas."""
    if hook_input.event != NormalizedEvent.AFTER_TOOL:
        return HookOutput()

    if hook_input.tool_name not in ("write_file", "edit_file"):
        return HookOutput()

    file_path = hook_input.tool_input.get("file_path", "")
    if not file_path:
        return HookOutput()

    cwd = hook_input.cwd or os.getcwd()
    project_root = Path(cwd)

    # Compute relative path
    try:
        abs_path = Path(file_path)
        if abs_path.is_absolute():
            rel_path = str(abs_path.relative_to(project_root))
        else:
            rel_path = file_path
    except ValueError:
        return HookOutput()

    # Find applicable schemas (fast path — no full tree walk)
    try:
        from deepwork.deepschema.matcher import get_schemas_for_file_fast

        schemas = get_schemas_for_file_fast(rel_path, project_root)
    except Exception:
        return HookOutput()

    if not schemas:
        return HookOutput()

    # Resolve inheritance for richer validation
    try:
        from deepwork.deepschema.resolver import resolve_all

        schemas, _ = resolve_all(schemas)
    except Exception:
        pass  # Continue with unresolved schemas

    messages: list[str] = []
    errors: list[str] = []

    # Conformance notes
    for schema in schemas:
        schema_rel = _relative_path(schema.source_path, project_root)
        messages.append(f"Note: this file must conform to the DeepSchema at {schema_rel}")

    # Run validations
    abs_file = project_root / rel_path
    for schema in schemas:
        # JSON Schema validation
        if schema.json_schema_path:
            json_schema_abs = schema.source_path.parent / schema.json_schema_path
            err = _validate_json_schema(abs_file, json_schema_abs)
            if err:
                errors.append(err)

        # Bash verification commands
        for cmd in schema.verification_bash_command:
            err = _run_verification_command(cmd, abs_file, project_root)
            if err:
                errors.append(err)

    # Build output
    if errors:
        error_text = "\n".join(errors)
        note_text = "\n".join(messages)
        context = f"{note_text}\n\nCRITICAL: DeepSchema validation failed when it tried to verify this change.\n\n{error_text}"
        return HookOutput(context=context)
    elif messages:
        return HookOutput(context="\n".join(messages))

    return HookOutput()


def _relative_path(path: Path, project_root: Path) -> str:
    """Get a project-relative path string."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _validate_json_schema(filepath: Path, schema_path: Path) -> str | None:
    """Validate a file against a JSON Schema.

    Parses the file as YAML if it has a .yml/.yaml extension, otherwise as JSON.
    Returns error message or None on success.
    """
    if not schema_path.exists():
        return f"JSON Schema file not found: {schema_path}"

    try:
        content = filepath.read_text(encoding="utf-8")
        if filepath.suffix in (".yml", ".yaml"):
            import yaml

            parsed = yaml.safe_load(content)
        else:
            parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return f"File is not valid JSON: {e}"
    except Exception as e:
        return f"Cannot parse file: {e}"

    try:
        schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return f"Cannot read JSON Schema: {e}"

    try:
        from deepwork.utils.validation import ValidationError, validate_against_schema

        validate_against_schema(parsed, schema_data)
    except ValidationError as e:
        return f"JSON Schema validation failed: {e}"

    return None


def _run_verification_command(cmd: str, filepath: Path, project_root: Path) -> str | None:
    """Run a verification bash command on the file.

    The command receives the file path as $1. Returns error message or None.
    """
    try:
        result = subprocess.run(
            ["bash", "-c", cmd, "--", str(filepath)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            return f"Command `{cmd}` failed (exit {result.returncode}): {output}"
    except subprocess.TimeoutExpired:
        return f"Command `{cmd}` timed out after 30s"
    except OSError as e:
        return f"Failed to run command `{cmd}`: {e}"

    return None


def main() -> int:
    """Entry point for the hook CLI."""
    platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
    return run_hook(deepschema_write_hook, platform)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        output_hook_error(e, context="deepschema_write hook")
        sys.exit(0)
