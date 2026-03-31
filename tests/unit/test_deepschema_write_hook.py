"""Tests for the deepschema_write post-tool hook.

Covers validation logic, error paths, and the main/entry-point flow.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

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
        """Empty file_path triggers early return."""
        inp = _make_hook_input(file_path="")
        assert deepschema_write_hook(inp) == HookOutput()

    def test_relative_file_path_used_directly(self) -> None:
        """Non-absolute path is passed as-is to the schema matcher."""
        inp = _make_hook_input(file_path="src/foo.py")
        with patch(_MATCHER_PATCH, return_value=[]) as mock_get:
            result = deepschema_write_hook(inp)
        mock_get.assert_called_once_with("src/foo.py", Path("/project"))
        assert result == HookOutput()

    def test_value_error_on_relative_to_returns_empty(self) -> None:
        """Absolute path outside project_root raises ValueError, producing empty output."""
        # /other/root/file.py is absolute but not under /project, so
        # Path.relative_to raises ValueError which is caught and suppressed.
        inp = _make_hook_input(file_path="/other/root/file.py", cwd="/project")
        result = deepschema_write_hook(inp)
        assert result == HookOutput()

    def test_matcher_exception_returns_empty(self) -> None:
        """Exception in get_schemas_for_file_fast produces empty output."""
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
        """resolve_all raising does not abort the hook — it continues with unresolved schemas."""
        schema = _make_schema(source_path=Path("/project/.deepschema/test/deepschema.yml"))
        with (
            patch(_MATCHER_PATCH, return_value=[schema]),
            patch(_RESOLVER_PATCH, side_effect=RuntimeError("resolve fail")),
        ):
            result = deepschema_write_hook(_make_hook_input())
        assert result.context is not None
        assert "conform" in result.context.lower()

    def test_conformance_note_only_when_no_errors(self) -> None:
        """Returns a conformance-note context (no CRITICAL) when there are no validation errors."""
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
        """JSON schema validation errors produce a CRITICAL context message."""
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
        """A failing bash verification command appends a CRITICAL error to the context."""
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
        """A passing verification command produces only the conformance note, no CRITICAL."""
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
        """Falls back to the absolute string path when the file is outside project root."""
        result = _relative_path(Path("/other/foo.py"), Path("/project"))
        assert result == "/other/foo.py"


# ---------------------------------------------------------------------------
# _validate_json_schema
# ---------------------------------------------------------------------------


class TestValidateJsonSchema:
    def test_schema_file_not_found(self, tmp_path: Path) -> None:
        """Returns an error string when the JSON schema file does not exist."""
        result = _validate_json_schema(tmp_path / "data.json", tmp_path / "no.json")
        assert result is not None
        assert "not found" in result

    def test_invalid_json_file(self, tmp_path: Path) -> None:
        """Returns an error string when the data file is not valid JSON."""
        data_file = tmp_path / "data.json"
        data_file.write_text("not json")
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{}")
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "not valid JSON" in result

    def test_generic_parse_error(self, tmp_path: Path) -> None:
        """Returns a 'Cannot parse file' error when reading the data file raises a decode error."""
        data_file = tmp_path / "data.yml"
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{}")
        # Patch read_text to raise a generic exception
        with patch.object(
            Path, "read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad")
        ):
            result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "Cannot parse file" in result

    def test_invalid_schema_file_json(self, tmp_path: Path) -> None:
        """Returns a 'Cannot read JSON Schema' error when the schema file is not valid JSON."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"key": "value"}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("not json schema")
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "Cannot read JSON Schema" in result

    def test_schema_file_oserror(self, tmp_path: Path) -> None:
        """Returns a 'Cannot read JSON Schema' error when an OSError occurs reading the schema file."""
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
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            )
        )
        result = _validate_json_schema(data_file, schema_file)
        assert result is None

    def test_json_schema_validation_failure(self, tmp_path: Path) -> None:
        """Data doesn't match schema."""
        data_file = tmp_path / "data.json"
        data_file.write_text('{"name": 123}')
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            )
        )
        result = _validate_json_schema(data_file, schema_file)
        assert result is not None
        assert "validation failed" in result.lower()

    def test_yaml_file_validated(self, tmp_path: Path) -> None:
        """YAML files are parsed with yaml.safe_load before validation."""
        data_file = tmp_path / "data.yml"
        data_file.write_text("name: test\n")
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            )
        )
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
        """Non-zero exit code produces an error string that includes captured stdout/stderr."""
        filepath = tmp_path / "file.txt"
        filepath.write_text("hello")
        result = _run_verification_command("echo fail && exit 1", filepath, tmp_path)
        assert result is not None
        assert "failed" in result
        assert "exit 1" in result
        assert "fail" in result  # stdout captured

    def test_timeout(self) -> None:
        """TimeoutExpired produces an error string mentioning 'timed out' and the timeout value."""
        with patch(
            "deepwork.hooks.deepschema_write.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=30),
        ):
            result = _run_verification_command("sleep 999", Path("/f"), Path("/"))
        assert result is not None
        assert "timed out" in result
        assert "30s" in result

    def test_oserror(self) -> None:
        """OSError while running the command produces a 'Failed to run' error string."""
        with patch(
            "deepwork.hooks.deepschema_write.subprocess.run",
            side_effect=OSError("No such file"),
        ):
            result = _run_verification_command("nonexistent", Path("/f"), Path("/"))
        assert result is not None
        assert "Failed to run" in result

    def test_returns_none_on_zero_exit(self, tmp_path: Path) -> None:
        """Returns None when the command exits successfully."""
        filepath = tmp_path / "file.txt"
        filepath.write_text("ok")
        result = _run_verification_command("exit 0", filepath, tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# main() and __main__ block
# ---------------------------------------------------------------------------


class TestMainEntryPoint:
    def test_main_delegates_to_run_hook(self) -> None:
        """main() reads DEEPWORK_HOOK_PLATFORM env var and delegates to run_hook."""
        with patch("deepwork.hooks.deepschema_write.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {"DEEPWORK_HOOK_PLATFORM": "gemini"}):
                ret = main()
        assert ret == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] == Platform("gemini")

    def test_main_defaults_to_claude(self) -> None:
        """Missing DEEPWORK_HOOK_PLATFORM env var defaults platform to 'claude'."""
        with patch("deepwork.hooks.deepschema_write.run_hook", return_value=0) as mock_run:
            with patch.dict("os.environ", {}, clear=True):
                main()
        assert mock_run.call_args[0][1] == Platform.CLAUDE

    def test_dunder_main_runs_as_script(self) -> None:
        """Running the module as __main__ invokes main() and exits cleanly."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "deepwork.hooks.deepschema_write",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            input="{}",
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        # Hook reads stdin JSON; empty {} means no meaningful event, so it
        # should exit 0 with an allow response (empty JSON or {}).
        assert result.returncode == 0
