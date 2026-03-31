"""Tests for the deepschema_write post-tool hook.

Covers validation logic, error paths, and the main/entry-point flow.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from deepwork.deepschema.config import DeepSchema
from deepwork.hooks.deepschema_write import (
    _relative_path,
    _run_verification_command,
    _validate_json_schema,
    deepschema_write_hook,
    main,
)
from deepwork.hooks.wrapper import HookInput, HookOutput, NormalizedEvent, Platform


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hook_input(
    event: NormalizedEvent = NormalizedEvent.AFTER_TOOL,
    tool_name: str = "write_file",
    file_path: str = "/project/src/foo.py",
    cwd: str = "/project",
) -> HookInput:
    """Build a HookInput for deepschema_write_hook tests."""
    return HookInput(
        platform=Platform.CLAUDE,
        event=event,
        session_id="sess1",
        transcript_path="",
        cwd=cwd,
        tool_name=tool_name,
        tool_input={"file_path": file_path},
        prompt="",
        raw_input={},
    )


def _make_schema(
    source_path: Path,
    json_schema_path: str | None = None,
    verification_bash_command: list[str] | None = None,
) -> DeepSchema:
    return DeepSchema(
        name="test",
        schema_type="named",
        source_path=source_path,
        json_schema_path=json_schema_path,
        verification_bash_command=verification_bash_command or [],
    )


# Patch targets — these are lazy-imported inside the hook function, so we
# patch the canonical module, not the hook module.
_MATCHER_PATCH = "deepwork.deepschema.matcher.get_schemas_for_file_fast"
_RESOLVER_PATCH = "deepwork.deepschema.resolver.resolve_all"


# ---------------------------------------------------------------------------
# deepschema_write_hook — early returns
# ---------------------------------------------------------------------------

class TestDeepschemaWriteHookEarlyReturns:
    """Tests for early-return branches in deepschema_write_hook."""

    def test_ignores_non_after_tool_event(self) -> None:
        inp = _make_hook_input(event=NormalizedEvent.BEFORE_TOOL)
        assert deepschema_write_hook(inp) == HookOutput()

    def test_ignores_non_write_edit_tool(self) -> None:
        inp = _make_hook_input(tool_name="shell")
        assert deepschema_write_hook(inp) == HookOutput()

    def test_ignores_empty_file_path(self) -> None:
        """Line 36: empty file_path returns early."""
        inp = _make_hook_input(file_path="")
        assert deepschema_write_hook(inp) == HookOutput()

    def test_relative_file_path_used_directly(self) -> None:
        """Lines 47-48: non-absolute path is used as-is for rel_path."""
        inp = _make_hook_input(file_path="src/foo.py")
        with patch(_MATCHER_PATCH, return_value=[]) as mock_get:
            result = deepschema_write_hook(inp)
        mock_get.assert_called_once_with("src/foo.py", Path("/project"))
        assert result == HookOutput()

    def test_value_error_on_relative_to_returns_empty(self) -> None:
        """Lines 48-49: file outside project_root triggers ValueError -> empty output."""
        # /other/root/file.py is absolute but not under /project, so
        # Path.relative_to raises ValueError, caught at line 48-49.
        inp = _make_hook_input(file_path="/other/root/file.py", cwd="/project")
        result = deepschema_write_hook(inp)
        assert result == HookOutput()

    def test_matcher_exception_returns_empty(self) -> None:
        """Lines 56-57: exception in get_schemas_for_file_fast -> empty output."""
        inp = _make_hook_input()
        with patch(_MATCHER_PATCH, side_effect=RuntimeError("boom")):
            result = deepschema_write_hook(inp)
        assert result == HookOutput()

    def test_no_schemas_returns_empty(self) -> None:
        inp = _make_hook_input()
        with patch(_MATCHER_PATCH, return_value=[]):
            result = deepschema_write_hook(inp)
        assert result == HookOutput()


# ---------------------------------------------------------------------------
# deepschema_write_hook — schema found paths
# ---------------------------------------------------------------------------

class TestDeepschemaWriteHookWithSchemas:
    """Tests when schemas are found — conformance notes and validation."""

    def test_resolve_all_failure_continues(self) -> None:
        """Lines 67-68: resolve_all raises -> hook continues with unresolved schemas."""
        schema = _make_schema(source_path=Path("/project/.deepschema/test/deepschema.yml"))
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, side_effect=RuntimeError("resolve fail")),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        assert "conform" in result.context.lower()

    def test_conformance_note_only_when_no_errors(self) -> None:
        """Line 101: returns conformance note context when no validation errors."""
        schema = _make_schema(source_path=Path("/project/schemas/deepschema.yml"))
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, return_value=([schema], {})),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        assert "DeepSchema" in result.context
        assert "CRITICAL" not in result.context

    def test_returns_error_context_on_json_schema_failure(self) -> None:
        """Lines 95-99: json schema errors produce CRITICAL context."""
        schema = _make_schema(
            source_path=Path("/project/schemas/deepschema.yml"),
            json_schema_path="schema.json",
        )
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, return_value=([schema], {})),
            patch(
                "deepwork.hooks.deepschema_write._validate_json_schema",
                return_value="validation failed",
            ),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        assert "CRITICAL" in result.context
        assert "validation failed" in result.context

    def test_verification_command_error_included(self) -> None:
        """Lines 89-92: bash verification error is appended."""
        schema = _make_schema(
            source_path=Path("/project/schemas/deepschema.yml"),
            verification_bash_command=["check.sh"],
        )
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, return_value=([schema], {})),
            patch(
                "deepwork.hooks.deepschema_write._run_verification_command",
                return_value="cmd failed",
            ),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        assert "CRITICAL" in result.context
        assert "cmd failed" in result.context

    def test_verification_command_success_no_error(self) -> None:
        """Line 91->89: verification command succeeds -> no error appended."""
        schema = _make_schema(
            source_path=Path("/project/schemas/deepschema.yml"),
            verification_bash_command=["true"],
        )
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, return_value=([schema], {})),
            patch(
                "deepwork.hooks.deepschema_write._run_verification_command",
                return_value=None,
            ),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        # Only conformance note, no CRITICAL
        assert "CRITICAL" not in result.context

    def test_edit_file_tool_also_triggers(self) -> None:
        """edit_file is also a valid trigger tool."""
        schema = _make_schema(source_path=Path("/project/schemas/deepschema.yml"))
        inp = _make_hook_input(tool_name="edit_file")
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, return_value=([schema], {})),
        ):
            result = deepschema_write_hook(inp)
        assert result.context is not None
        assert "DeepSchema" in result.context


# ---------------------------------------------------------------------------
# _relative_path
# ---------------------------------------------------------------------------

class TestRelativePath:
    def test_relative_when_inside_root(self) -> None:
        result = _relative_path(Path("/project/src/foo.py"), Path("/project"))
        assert result == "src/foo.py"

    def test_falls_back_to_str_when_outside_root(self) -> None:
        """Lines 110-111: ValueError fallback."""
        result = _relative_path(Path("/other/foo.py"), Path("/project"))
        assert result == "/other/foo.py"


# ---------------------------------------------------------------------------
# _validate_json_schema
# ---------------------------------------------------------------------------

class TestValidateJsonSchema:
    def test_schema_file_not_found(self, tmp_path: Path) -> None:
        """Line 121: schema file doesn't exist."""
        result = _validate_json_schema(tmp_path / "data.json", tmp_path / "no.json")
        assert result is not None
        assert "not found" in result

    def test_invalid_json_file(self, tmp_path: Path) -> None:
        """Lines 131-132: file is not valid JSON."""
        data_file = tmp_path / "data.json"
        data_file.write_text("not json")
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{}")
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "not valid JSON" in result

    def test_generic_parse_error(self, tmp_path: Path) -> None:
        """Lines 133-134: generic parse error (non-JSON, non-YAML read failure)."""
        data_file = tmp_path / "data.yml"
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{}")
        # Patch read_text to raise a generic exception
        with patch.object(Path, "read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad")):
            result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "Cannot parse file" in result

    def test_invalid_schema_file_json(self, tmp_path: Path) -> None:
        """Lines 138-139: schema file is not valid JSON."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"key": "value"}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("not json schema")
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "Cannot read JSON Schema" in result

    def test_schema_file_oserror(self, tmp_path: Path) -> None:
        """Lines 138-139: OSError reading schema file."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"key": "value"}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{}")
        # Patch only the second read_text call (schema file)
        original_read = Path.read_text
        call_count = 0
        def patched_read(self_path: Path, *args: object, **kwargs: object) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise OSError("permission denied")
            return original_read(self_path, *args, **kwargs)  # type: ignore[arg-type]
        with patch.object(Path, "read_text", patched_read):
            result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "Cannot read JSON Schema" in result

    def test_valid_json_against_schema(self, tmp_path: Path) -> None:
        """Happy path: valid data passes schema validation."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"name": "test"}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps({
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }))
        result = _validate_json_schema(data_file, schema_file)
        assert result is None

    def test_json_schema_validation_failure(self, tmp_path: Path) -> None:
        """Data doesn't match schema."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"name": 123}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps({
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }))
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "validation failed" in result.lower()

    def test_yaml_file_validated(self, tmp_path: Path) -> None:
        """YAML files are parsed with yaml.safe_load before validation."""
        data_file = tmp_path / "data.yml"
        data_file.write_text("name: test\n")
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps({
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }))
        result = _validate_json_schema(data_file, schema_file)
        assert result is None


# ---------------------------------------------------------------------------
# _run_verification_command
# ---------------------------------------------------------------------------

class TestRunVerificationCommand:
    def test_successful_command(self, tmp_path: Path) -> None:
        filepath = tmp_path / "file.txt"
        filepath.write_text("hello")
        result = _run_verification_command("true", filepath, tmp_path)
        assert result is None

    def test_failing_command_includes_output(self, tmp_path: Path) -> None:
        """Lines 165-166: non-zero exit code includes stdout+stderr."""
        filepath = tmp_path / "file.txt"
        filepath.write_text("hello")
        result = _run_verification_command("echo fail && exit 1", filepath, tmp_path)
        assert result is not None
        assert "failed" in result
        assert "exit 1" in result
        assert "fail" in result  # stdout captured

    def test_timeout(self) -> None:
        """Lines 167-168: command times out."""
        with patch(
            "deepwork.hooks.deepschema_write.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=30),
        ):
            result = _run_verification_command("sleep 999", Path("/f"), Path("/"))
        assert result is not None
        assert "timed out" in result
        assert "30s" in result

    def test_oserror(self) -> None:
        """Lines 169-170: OS error running command."""
        with patch(
            "deepwork.hooks.deepschema_write.subprocess.run",
            side_effect=OSError("No such file"),
        ):
            result = _run_verification_command("nonexistent", Path("/f"), Path("/"))
        assert result is not None
        assert "Failed to run" in result

    def test_returns_none_on_zero_exit(self, tmp_path: Path) -> None:
        """Line 172: explicit None return on success."""
        filepath = tmp_path / "file.txt"
        filepath.write_text("ok")
        result = _run_verification_command("exit 0", filepath, tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# main() and __main__ block
# ---------------------------------------------------------------------------

class TestMainEntryPoint:
    def test_main_delegates_to_run_hook(self) -> None:
        """Lines 177-178: main() creates Platform and calls run_hook."""
        with patch("deepwork.hooks.deepschema_write.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {"DEEPWORK_HOOK_PLATFORM": "gemini"}):
                ret = main()
        assert ret == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] == Platform("gemini")

    def test_main_defaults_to_claude(self) -> None:
        """Line 177: missing env var defaults to 'claude'."""
        with patch("deepwork.hooks.deepschema_write.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {}, clear=True):
                main()
        assert mock_run.call_args[0][1] == Platform.CLAUDE

    def test_dunder_main_runs_as_script(self) -> None:
        """Lines 182-186: running module as __main__ invokes main() and exits."""
        result = subprocess.run(
            [
                sys.executable, "-m", "deepwork.hooks.deepschema_write",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            input="{}",
            cwd="/Users/noah/Documents/GitHub/deep-work",
        )
        # Hook reads stdin JSON; empty {} means no meaningful event, so it
        # should exit 0 with an allow response (empty JSON or {}).
        assert result.returncode == 0
