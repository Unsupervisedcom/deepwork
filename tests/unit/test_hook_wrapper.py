"""Tests for the hook wrapper module.

These tests verify that the hook wrapper correctly normalizes input/output
between different AI CLI platforms (Claude Code, Gemini CLI).
"""

import json

from deepwork.hooks.wrapper import (
    EVENT_TO_NORMALIZED,
    NORMALIZED_TO_EVENT,
    TOOL_TO_NORMALIZED,
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    denormalize_output,
    normalize_input,
)


class TestHookInput:
    """Tests for HookInput normalization."""

    def test_from_claude_stop_event(self) -> None:
        """Test normalizing Claude Stop event."""
        raw_data = {
            "session_id": "sess123",
            "transcript_path": "/path/to/transcript.jsonl",
            "cwd": "/project",
            "hook_event_name": "Stop",
            "tool_name": "",
            "tool_input": {},
        }

        hook_input = HookInput.from_dict(raw_data, Platform.CLAUDE)

        assert hook_input.platform == Platform.CLAUDE
        assert hook_input.event == NormalizedEvent.AFTER_AGENT
        assert hook_input.session_id == "sess123"
        assert hook_input.transcript_path == "/path/to/transcript.jsonl"
        assert hook_input.cwd == "/project"
        assert hook_input.raw_input == raw_data

    def test_from_gemini_after_agent_event(self) -> None:
        """Test normalizing Gemini AfterAgent event."""
        raw_data = {
            "session_id": "sess456",
            "transcript_path": "/path/to/transcript.json",
            "cwd": "/project",
            "hook_event_name": "AfterAgent",
            "timestamp": "2026-01-15T10:00:00Z",
        }

        hook_input = HookInput.from_dict(raw_data, Platform.GEMINI)

        assert hook_input.platform == Platform.GEMINI
        assert hook_input.event == NormalizedEvent.AFTER_AGENT
        assert hook_input.session_id == "sess456"

    def test_from_claude_pretooluse_event(self) -> None:
        """Test normalizing Claude PreToolUse event."""
        raw_data = {
            "session_id": "sess123",
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/path/to/file.txt",
                "content": "hello world",
            },
        }

        hook_input = HookInput.from_dict(raw_data, Platform.CLAUDE)

        assert hook_input.event == NormalizedEvent.BEFORE_TOOL
        assert hook_input.tool_name == "write_file"
        assert hook_input.tool_input["file_path"] == "/path/to/file.txt"

    def test_from_gemini_beforetool_event(self) -> None:
        """Test normalizing Gemini BeforeTool event."""
        raw_data = {
            "session_id": "sess456",
            "hook_event_name": "BeforeTool",
            "tool_name": "write_file",
            "tool_input": {
                "file_path": "/path/to/file.txt",
                "content": "hello world",
            },
        }

        hook_input = HookInput.from_dict(raw_data, Platform.GEMINI)

        assert hook_input.event == NormalizedEvent.BEFORE_TOOL
        assert hook_input.tool_name == "write_file"

    def test_tool_name_normalization_claude(self) -> None:
        """Test Claude tool names are normalized to snake_case."""
        test_cases = [
            ("Write", "write_file"),
            ("Read", "read_file"),
            ("Edit", "edit_file"),
            ("Bash", "shell"),
            ("Glob", "glob"),
            ("Grep", "grep"),
        ]

        for claude_name, expected in test_cases:
            raw_data = {
                "hook_event_name": "PreToolUse",
                "tool_name": claude_name,
            }
            hook_input = HookInput.from_dict(raw_data, Platform.CLAUDE)
            assert hook_input.tool_name == expected, f"Expected {expected} for {claude_name}"

    def test_event_normalization_claude(self) -> None:
        """Test all Claude events are normalized correctly."""
        test_cases = [
            ("Stop", NormalizedEvent.AFTER_AGENT),
            ("SubagentStop", NormalizedEvent.AFTER_AGENT),
            ("PreToolUse", NormalizedEvent.BEFORE_TOOL),
            ("PostToolUse", NormalizedEvent.AFTER_TOOL),
            ("UserPromptSubmit", NormalizedEvent.BEFORE_PROMPT),
            ("SessionStart", NormalizedEvent.SESSION_START),
            ("SessionEnd", NormalizedEvent.SESSION_END),
        ]

        for claude_event, expected in test_cases:
            raw_data = {"hook_event_name": claude_event}
            hook_input = HookInput.from_dict(raw_data, Platform.CLAUDE)
            assert hook_input.event == expected, f"Expected {expected} for {claude_event}"

    def test_event_normalization_gemini(self) -> None:
        """Test all Gemini events are normalized correctly."""
        test_cases = [
            ("AfterAgent", NormalizedEvent.AFTER_AGENT),
            ("BeforeTool", NormalizedEvent.BEFORE_TOOL),
            ("AfterTool", NormalizedEvent.AFTER_TOOL),
            ("BeforeAgent", NormalizedEvent.BEFORE_PROMPT),
            ("SessionStart", NormalizedEvent.SESSION_START),
            ("SessionEnd", NormalizedEvent.SESSION_END),
            ("BeforeModel", NormalizedEvent.BEFORE_MODEL),
            ("AfterModel", NormalizedEvent.AFTER_MODEL),
        ]

        for gemini_event, expected in test_cases:
            raw_data = {"hook_event_name": gemini_event}
            hook_input = HookInput.from_dict(raw_data, Platform.GEMINI)
            assert hook_input.event == expected, f"Expected {expected} for {gemini_event}"

    def test_empty_input(self) -> None:
        """Test handling of empty input."""
        hook_input = HookInput.from_dict({}, Platform.CLAUDE)

        assert hook_input.session_id == ""
        assert hook_input.transcript_path == ""
        assert hook_input.cwd == ""
        assert hook_input.tool_name == ""


class TestHookOutput:
    """Tests for HookOutput denormalization."""

    def test_empty_output_produces_empty_json(self) -> None:
        """Test that empty HookOutput produces empty dict."""
        output = HookOutput()
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.AFTER_AGENT)

        assert result == {}

    def test_block_decision_claude(self) -> None:
        """Test blocking output for Claude."""
        output = HookOutput(decision="block", reason="Must complete X first")
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.AFTER_AGENT)

        assert result["decision"] == "block"
        assert result["reason"] == "Must complete X first"

    def test_block_decision_gemini_converts_to_deny(self) -> None:
        """Test that 'block' is converted to 'deny' for Gemini."""
        output = HookOutput(decision="block", reason="Must complete X first")
        result = output.to_dict(Platform.GEMINI, NormalizedEvent.AFTER_AGENT)

        assert result["decision"] == "deny"
        assert result["reason"] == "Must complete X first"

    def test_deny_decision_stays_deny(self) -> None:
        """Test that 'deny' stays as 'deny' on both platforms."""
        output = HookOutput(decision="deny", reason="Not allowed")

        claude_result = output.to_dict(Platform.CLAUDE, NormalizedEvent.BEFORE_TOOL)
        assert claude_result["decision"] == "deny"

        gemini_result = output.to_dict(Platform.GEMINI, NormalizedEvent.BEFORE_TOOL)
        assert gemini_result["decision"] == "deny"

    def test_allow_decision(self) -> None:
        """Test allow decision."""
        output = HookOutput(decision="allow")
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.BEFORE_TOOL)

        assert result["decision"] == "allow"

    def test_continue_false(self) -> None:
        """Test continue=false output."""
        output = HookOutput(continue_loop=False, stop_reason="Critical error")
        result = output.to_dict(Platform.GEMINI, NormalizedEvent.AFTER_AGENT)

        assert result["continue"] is False
        assert result["stopReason"] == "Critical error"

    def test_suppress_output(self) -> None:
        """Test suppressOutput flag."""
        output = HookOutput(suppress_output=True)
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.BEFORE_TOOL)

        assert result["suppressOutput"] is True

    def test_context_for_claude_session_start(self) -> None:
        """Test context handling for Claude SessionStart."""
        output = HookOutput(context="Additional context here")
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.SESSION_START)

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert result["hookSpecificOutput"]["additionalContext"] == "Additional context here"

    def test_context_for_claude_other_events(self) -> None:
        """Test context handling for Claude non-SessionStart events."""
        output = HookOutput(context="Warning message")
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.AFTER_AGENT)

        assert result["systemMessage"] == "Warning message"

    def test_context_for_gemini(self) -> None:
        """Test context handling for Gemini."""
        output = HookOutput(context="Additional context")
        result = output.to_dict(Platform.GEMINI, NormalizedEvent.AFTER_AGENT)

        assert "hookSpecificOutput" in result
        assert result["hookSpecificOutput"]["additionalContext"] == "Additional context"

    def test_raw_output_merged(self) -> None:
        """Test that raw_output is merged into result."""
        output = HookOutput(
            decision="allow",
            raw_output={"customField": "customValue"},
        )
        result = output.to_dict(Platform.CLAUDE, NormalizedEvent.BEFORE_TOOL)

        assert result["decision"] == "allow"
        assert result["customField"] == "customValue"


class TestNormalizeInput:
    """Tests for the normalize_input function."""

    def test_valid_json(self) -> None:
        """Test normalizing valid JSON input."""
        raw_json = '{"hook_event_name": "Stop", "session_id": "123"}'
        hook_input = normalize_input(raw_json, Platform.CLAUDE)

        assert hook_input.event == NormalizedEvent.AFTER_AGENT
        assert hook_input.session_id == "123"

    def test_empty_json(self) -> None:
        """Test normalizing empty JSON input."""
        hook_input = normalize_input("{}", Platform.CLAUDE)

        assert hook_input.session_id == ""
        assert hook_input.event == NormalizedEvent.AFTER_AGENT  # Default

    def test_empty_string(self) -> None:
        """Test normalizing empty string input."""
        hook_input = normalize_input("", Platform.CLAUDE)

        assert hook_input.session_id == ""

    def test_whitespace_only(self) -> None:
        """Test normalizing whitespace-only input."""
        hook_input = normalize_input("   \n  ", Platform.CLAUDE)

        assert hook_input.session_id == ""

    def test_invalid_json(self) -> None:
        """Test normalizing invalid JSON input."""
        hook_input = normalize_input("not valid json", Platform.CLAUDE)

        assert hook_input.session_id == ""


class TestDenormalizeOutput:
    """Tests for the denormalize_output function."""

    def test_produces_valid_json(self) -> None:
        """Test that output is valid JSON."""
        output = HookOutput(decision="block", reason="test")
        json_str = denormalize_output(output, Platform.CLAUDE, NormalizedEvent.AFTER_AGENT)

        # Should not raise
        parsed = json.loads(json_str)
        assert parsed["decision"] == "block"

    def test_empty_output_produces_empty_object(self) -> None:
        """Test that empty output produces '{}'."""
        output = HookOutput()
        json_str = denormalize_output(output, Platform.CLAUDE, NormalizedEvent.AFTER_AGENT)

        assert json_str == "{}"


class TestEventMappings:
    """Tests for event name mappings."""

    def test_all_claude_events_have_normalized_mapping(self) -> None:
        """Test that all Claude events have normalized mappings."""
        claude_events = [
            "Stop",
            "SubagentStop",
            "PreToolUse",
            "PostToolUse",
            "UserPromptSubmit",
            "SessionStart",
            "SessionEnd",
        ]

        for event in claude_events:
            assert event in EVENT_TO_NORMALIZED[Platform.CLAUDE], f"Missing mapping for {event}"

    def test_all_gemini_events_have_normalized_mapping(self) -> None:
        """Test that all Gemini events have normalized mappings."""
        gemini_events = [
            "AfterAgent",
            "BeforeTool",
            "AfterTool",
            "BeforeAgent",
            "SessionStart",
            "SessionEnd",
            "BeforeModel",
            "AfterModel",
        ]

        for event in gemini_events:
            assert event in EVENT_TO_NORMALIZED[Platform.GEMINI], f"Missing mapping for {event}"

    def test_normalized_to_event_roundtrip_claude(self) -> None:
        """Test that Claude events can be normalized and denormalized."""
        for _platform_event, normalized in EVENT_TO_NORMALIZED[Platform.CLAUDE].items():
            if normalized in NORMALIZED_TO_EVENT[Platform.CLAUDE]:
                # SubagentStop maps to AFTER_AGENT but denormalizes to Stop
                denormalized = NORMALIZED_TO_EVENT[Platform.CLAUDE][normalized]
                # Just verify we get a valid event name back
                assert denormalized in EVENT_TO_NORMALIZED[Platform.CLAUDE]


class TestToolMappings:
    """Tests for tool name mappings."""

    def test_claude_tools_normalize_to_snake_case(self) -> None:
        """Test Claude tool names normalize to snake_case."""
        for _claude_tool, normalized in TOOL_TO_NORMALIZED[Platform.CLAUDE].items():
            assert "_" in normalized or normalized.islower(), f"{normalized} should be snake_case"

    def test_gemini_tools_are_already_snake_case(self) -> None:
        """Test Gemini tool names are already snake_case."""
        for gemini_tool, normalized in TOOL_TO_NORMALIZED[Platform.GEMINI].items():
            assert gemini_tool == normalized, "Gemini tools should be identity mapping"

    def test_common_tools_map_to_same_normalized_name(self) -> None:
        """Test that common tools map to the same normalized name across platforms."""
        common_tools = ["write_file", "read_file", "shell", "glob", "grep"]

        for tool in common_tools:
            # Find Claude tool that maps to this normalized name
            claude_tool = None
            for k, v in TOOL_TO_NORMALIZED[Platform.CLAUDE].items():
                if v == tool:
                    claude_tool = k
                    break

            gemini_tool = None
            for k, v in TOOL_TO_NORMALIZED[Platform.GEMINI].items():
                if v == tool:
                    gemini_tool = k
                    break

            if claude_tool and gemini_tool:
                # Both platforms should normalize to the same name
                assert TOOL_TO_NORMALIZED[Platform.CLAUDE][claude_tool] == tool
                assert TOOL_TO_NORMALIZED[Platform.GEMINI][gemini_tool] == tool


class TestIntegration:
    """Integration tests for the full normalization flow."""

    def test_claude_stop_hook_flow(self) -> None:
        """Test complete flow for Claude Stop hook."""
        # Input from Claude
        raw_input = json.dumps({
            "session_id": "sess123",
            "transcript_path": "/path/transcript.jsonl",
            "cwd": "/project",
            "hook_event_name": "Stop",
        })

        # Normalize
        hook_input = normalize_input(raw_input, Platform.CLAUDE)
        assert hook_input.event == NormalizedEvent.AFTER_AGENT

        # Process (would call hook function here)
        hook_output = HookOutput(decision="block", reason="Policy X requires attention")

        # Denormalize
        output_json = denormalize_output(hook_output, Platform.CLAUDE, hook_input.event)
        result = json.loads(output_json)

        assert result["decision"] == "block"
        assert "Policy X" in result["reason"]

    def test_gemini_afteragent_hook_flow(self) -> None:
        """Test complete flow for Gemini AfterAgent hook."""
        # Input from Gemini
        raw_input = json.dumps({
            "session_id": "sess456",
            "transcript_path": "/path/transcript.json",
            "cwd": "/project",
            "hook_event_name": "AfterAgent",
            "timestamp": "2026-01-15T10:00:00Z",
        })

        # Normalize
        hook_input = normalize_input(raw_input, Platform.GEMINI)
        assert hook_input.event == NormalizedEvent.AFTER_AGENT

        # Process (would call hook function here)
        hook_output = HookOutput(decision="block", reason="Policy Y requires attention")

        # Denormalize
        output_json = denormalize_output(hook_output, Platform.GEMINI, hook_input.event)
        result = json.loads(output_json)

        # Gemini should get "deny" instead of "block"
        assert result["decision"] == "deny"
        assert "Policy Y" in result["reason"]

    def test_cross_platform_same_hook_logic(self) -> None:
        """Test that the same hook logic produces correct output for both platforms."""

        def sample_hook(hook_input: HookInput) -> HookOutput:
            """Sample hook that blocks if event is after_agent."""
            if hook_input.event == NormalizedEvent.AFTER_AGENT:
                return HookOutput(decision="block", reason="Must review first")
            return HookOutput()

        # Test with Claude
        claude_input = normalize_input(
            '{"hook_event_name": "Stop"}',
            Platform.CLAUDE,
        )
        claude_output = sample_hook(claude_input)
        claude_json = denormalize_output(claude_output, Platform.CLAUDE, claude_input.event)
        claude_result = json.loads(claude_json)

        # Test with Gemini
        gemini_input = normalize_input(
            '{"hook_event_name": "AfterAgent"}',
            Platform.GEMINI,
        )
        gemini_output = sample_hook(gemini_input)
        gemini_json = denormalize_output(gemini_output, Platform.GEMINI, gemini_input.event)
        gemini_result = json.loads(gemini_json)

        # Both should block, but with platform-appropriate decision value
        assert claude_result["decision"] == "block"
        assert gemini_result["decision"] == "deny"
        assert claude_result["reason"] == gemini_result["reason"]
