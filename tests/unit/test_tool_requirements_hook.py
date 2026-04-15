"""Tests for the tool requirements PreToolUse hook (DW-REQ-012.9, PLUG-REQ-001.15)."""

from unittest.mock import MagicMock, patch

from deepwork.hooks.wrapper import HookInput, NormalizedEvent, Platform


class TestToolRequirementsHook:
    def _make_input(
        self,
        tool_name: str = "shell",
        tool_input: dict | None = None,
        raw_tool_name: str = "Bash",
        session_id: str = "test-session",
        cwd: str = "/test/project",
    ) -> HookInput:
        return HookInput(
            platform=Platform.CLAUDE,
            event=NormalizedEvent.BEFORE_TOOL,
            session_id=session_id,
            cwd=cwd,
            tool_name=tool_name,
            tool_input=tool_input or {"command": "ls"},
            raw_input={
                "hook_event_name": "PreToolUse",
                "tool_name": raw_tool_name,
                "session_id": session_id,
            },
        )

    def test_skips_non_before_tool_events(self) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        hook_input = HookInput(
            platform=Platform.CLAUDE,
            event=NormalizedEvent.AFTER_TOOL,
            tool_name="shell",
        )
        result = tool_requirements_hook(hook_input)
        assert result.decision == ""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-012.9.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loop_prevention_skips_all_appeal_prefixes(self) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        for prefix in [
            "mcp__deepwork__appeal_tool_requirement",
            "mcp__deepwork-dev__appeal_tool_requirement",
            "mcp__plugin_deepwork_deepwork__appeal_tool_requirement",
        ]:
            hook_input = self._make_input(raw_tool_name=prefix)
            result = tool_requirements_hook(hook_input)
            assert result.decision == "", f"Failed for {prefix}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-012.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.hooks.tool_requirements.discover_sidecar")
    def test_fail_closed_when_no_sidecar(self, mock_discover: MagicMock) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        mock_discover.return_value = None
        hook_input = self._make_input()
        result = tool_requirements_hook(hook_input)

        assert "permissionDecision" in str(result.raw_output)
        assert result.raw_output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "not running" in result.raw_output["hookSpecificOutput"]["permissionDecisionReason"]

    @patch("deepwork.hooks.tool_requirements._http_post")
    @patch("deepwork.hooks.tool_requirements.discover_sidecar")
    def test_allow_on_sidecar_allow(self, mock_discover: MagicMock, mock_post: MagicMock) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        mock_discover.return_value = {"pid": 123, "port": 9999}
        mock_post.return_value = {"decision": "allow", "reason": "OK"}

        hook_input = self._make_input()
        result = tool_requirements_hook(hook_input)
        assert result.decision == ""
        assert result.raw_output == {}

    @patch("deepwork.hooks.tool_requirements._http_post")
    @patch("deepwork.hooks.tool_requirements.discover_sidecar")
    def test_deny_on_sidecar_deny(self, mock_discover: MagicMock, mock_post: MagicMock) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        mock_discover.return_value = {"pid": 123, "port": 9999}
        mock_post.return_value = {
            "decision": "deny",
            "reason": "Policy violation: r1",
        }

        hook_input = self._make_input()
        result = tool_requirements_hook(hook_input)

        assert result.raw_output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert (
            "Policy violation"
            in result.raw_output["hookSpecificOutput"]["permissionDecisionReason"]
        )

    @patch("deepwork.hooks.tool_requirements._http_post")
    @patch("deepwork.hooks.tool_requirements.discover_sidecar")
    def test_fail_closed_on_connection_error(
        self, mock_discover: MagicMock, mock_post: MagicMock
    ) -> None:
        from deepwork.hooks.tool_requirements import tool_requirements_hook

        mock_discover.return_value = {"pid": 123, "port": 9999}
        mock_post.side_effect = ConnectionRefusedError("Connection refused")

        hook_input = self._make_input()
        result = tool_requirements_hook(hook_input)

        assert result.raw_output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert (
            "Failed to reach" in result.raw_output["hookSpecificOutput"]["permissionDecisionReason"]
        )
