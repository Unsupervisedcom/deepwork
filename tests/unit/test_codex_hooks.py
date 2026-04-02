"""Tests for Codex hook setup and hook outputs."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from deepwork.codex_hooks import (
    build_deepschema_output,
    build_post_tool_use_output,
    build_session_start_output,
    ensure_codex_hook_entries,
    ensure_codex_hooks_enabled,
    setup_codex_hooks,
)
from deepwork.hooks.wrapper import HookOutput
from deepwork.jobs.mcp.server import create_server


class TestCodexHookSetup:
    """Tests for repo-local Codex hook setup."""

    def test_creates_repo_local_codex_files(self, tmp_path: Path) -> None:
        result = setup_codex_hooks(tmp_path)

        assert result.config_updated is True
        assert result.hooks_updated is True

        config_path = tmp_path / ".codex" / "config.toml"
        hooks_path = tmp_path / ".codex" / "hooks.json"

        assert config_path.read_text(encoding="utf-8") == "[features]\ncodex_hooks = true\n"

        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        assert "SessionStart" in hooks["hooks"]
        assert "PostToolUse" in hooks["hooks"]

    def test_enables_codex_hooks_before_features_subtables(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("[features.experimental]\nfast_mode = true\n", encoding="utf-8")

        changed = ensure_codex_hooks_enabled(config_path)

        assert changed is True
        assert config_path.read_text(encoding="utf-8") == (
            "[features]\ncodex_hooks = true\n\n[features.experimental]\nfast_mode = true\n"
        )

    def test_merges_hooks_without_duplicates(self, tmp_path: Path) -> None:
        hooks_path = tmp_path / ".codex" / "hooks.json"
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        hooks_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "startup|resume",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "echo custom",
                                    }
                                ],
                            }
                        ]
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        first_changed = ensure_codex_hook_entries(hooks_path)
        second_changed = ensure_codex_hook_entries(hooks_path)

        assert first_changed is True
        assert second_changed is False

        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        session_hooks = hooks["hooks"]["SessionStart"][0]["hooks"]
        commands = [hook["command"] for hook in session_hooks]
        assert commands.count("uvx deepwork codex-hook session_start") == 1
        assert "echo custom" in commands

        post_tool_groups = hooks["hooks"]["PostToolUse"]
        assert any(group.get("matcher") == "Bash" for group in post_tool_groups)
        assert any(group.get("matcher") == "Write" for group in post_tool_groups)
        assert any(group.get("matcher") == "Edit" for group in post_tool_groups)

    @patch("deepwork.jobs.mcp.server.setup_codex_hooks")
    def test_create_server_sets_up_codex_hooks(
        self,
        mock_setup_codex_hooks: object,
        tmp_path: Path,
    ) -> None:
        create_server(tmp_path, platform="codex")

        mock_setup_codex_hooks.assert_called_once_with(tmp_path.resolve())  # type: ignore[attr-defined]


class TestCodexHookOutputs:
    """Tests for the Codex hook output builders."""

    @patch("deepwork.codex_hooks._get_active_sessions")
    def test_session_start_output_includes_session_id_and_restore_context(
        self,
        mock_get_active_sessions: object,
        tmp_path: Path,
    ) -> None:
        mock_get_active_sessions.return_value = {  # type: ignore[attr-defined]
            "active_sessions": [
                {
                    "session_id": "sess-1",
                    "job_name": "deepwork_jobs",
                    "workflow_name": "new_job",
                    "goal": "Create a workflow",
                    "current_step_id": "define",
                    "step_number": 1,
                    "total_steps": 3,
                    "completed_steps": [],
                    "common_job_info": "Shared context",
                    "current_step_instructions": "Do the thing",
                }
            ]
        }

        result = build_session_start_output(
            {
                "session_id": "codex-session-123",
                "cwd": str(tmp_path),
                "source": "resume",
            }
        )

        additional = result["hookSpecificOutput"]["additionalContext"]
        assert "DEEPWORK_SESSION_ID=codex-session-123" in additional
        assert "# DeepWork Workflow Context" in additional
        assert "deepwork_jobs/new_job" in additional

    def test_post_tool_use_output_only_for_git_commit(self) -> None:
        no_output = build_post_tool_use_output(
            {
                "tool_input": {
                    "command": "git status",
                }
            }
        )
        assert no_output == {}

        commit_output = build_post_tool_use_output(
            {
                "tool_input": {
                    "command": "git commit -m 'test'",
                }
            }
        )
        assert commit_output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert "review" in commit_output["hookSpecificOutput"]["additionalContext"].lower()

    def test_build_deepschema_output_uses_tool_input_file_path(self) -> None:
        with patch("deepwork.codex_hooks.deepschema_write_hook") as mock_hook:
            mock_hook.return_value = HookOutput(context="schema note")

            result = build_deepschema_output(
                {
                    "cwd": "/project",
                    "tool_input": {"file_path": "src/app.py"},
                },
                "write_file",
            )

        assert result["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert result["hookSpecificOutput"]["additionalContext"] == "schema note"
        hook_input = mock_hook.call_args.args[0]
        assert hook_input.tool_name == "write_file"
        assert hook_input.tool_input["file_path"] == "src/app.py"

    def test_build_deepschema_output_supports_top_level_file_path_fallback(self) -> None:
        with patch("deepwork.codex_hooks.deepschema_write_hook") as mock_hook:
            mock_hook.return_value = HookOutput()

            result = build_deepschema_output(
                {
                    "cwd": "/project",
                    "file_path": "src/app.py",
                },
                "edit_file",
            )

        assert result == {}
        hook_input = mock_hook.call_args.args[0]
        assert hook_input.tool_name == "edit_file"
        assert hook_input.tool_input["file_path"] == "src/app.py"
