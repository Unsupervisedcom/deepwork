"""Tests for the hooks syncer module."""

import json
from pathlib import Path

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.hooks_syncer import (
    ExpertHooks,
    HookEntry,
    HookSpec,
    collect_expert_hooks,
    merge_hooks_for_platform,
    sync_hooks_to_platform,
)


class TestHookEntry:
    """Tests for HookEntry dataclass."""

    def test_get_command_for_script(self, temp_dir: Path) -> None:
        """Test getting command for a script hook."""
        expert_dir = temp_dir / ".deepwork" / "experts" / "test_expert"
        expert_dir.mkdir(parents=True)

        entry = HookEntry(
            expert_name="test_expert",
            expert_dir=expert_dir,
            script="test_hook.sh",
        )

        cmd = entry.get_command(temp_dir)
        assert cmd == ".deepwork/experts/test_expert/hooks/test_hook.sh"

    def test_get_command_for_module(self, temp_dir: Path) -> None:
        """Test getting command for a module hook."""
        expert_dir = temp_dir / ".deepwork" / "experts" / "test_expert"
        expert_dir.mkdir(parents=True)

        entry = HookEntry(
            expert_name="test_expert",
            expert_dir=expert_dir,
            module="deepwork.hooks.rules_check",
        )

        cmd = entry.get_command(temp_dir)
        assert cmd == "deepwork hook rules_check"


class TestExpertHooks:
    """Tests for ExpertHooks dataclass."""

    def test_from_expert_dir_with_hooks(self, temp_dir: Path) -> None:
        """Test loading hooks from expert directory."""
        expert_dir = temp_dir / "test_expert"
        hooks_dir = expert_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        # Create expert.yml so it's recognized as a valid expert
        (expert_dir / "expert.yml").write_text(
            "discovery_description: test\nfull_expertise: test\n"
        )

        # Create global_hooks.yml
        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text(
            """
UserPromptSubmit:
  - capture.sh
Stop:
  - rules_check.sh
  - cleanup.sh
"""
        )

        result = ExpertHooks.from_expert_dir(expert_dir)

        assert result is not None
        assert result.expert_name == "test_expert"
        assert len(result.hooks["UserPromptSubmit"]) == 1
        assert result.hooks["UserPromptSubmit"][0].script == "capture.sh"
        assert len(result.hooks["Stop"]) == 2
        assert result.hooks["Stop"][0].script == "rules_check.sh"
        assert result.hooks["Stop"][1].script == "cleanup.sh"

    def test_from_expert_dir_with_module_hooks(self, temp_dir: Path) -> None:
        """Test loading module-based hooks from expert directory."""
        expert_dir = temp_dir / "test_expert"
        hooks_dir = expert_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        # Create expert.yml so it's recognized as a valid expert
        (expert_dir / "expert.yml").write_text(
            "discovery_description: test\nfull_expertise: test\n"
        )

        # Create global_hooks.yml with module format
        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text(
            """
UserPromptSubmit:
  - capture.sh
Stop:
  - module: deepwork.hooks.rules_check
"""
        )

        result = ExpertHooks.from_expert_dir(expert_dir)

        assert result is not None
        assert result.hooks["UserPromptSubmit"][0].script == "capture.sh"
        assert result.hooks["Stop"][0].module == "deepwork.hooks.rules_check"
        assert result.hooks["Stop"][0].script is None

    def test_from_expert_dir_no_hooks_file(self, temp_dir: Path) -> None:
        """Test returns None when no hooks file exists."""
        expert_dir = temp_dir / "test_expert"
        expert_dir.mkdir(parents=True)

        result = ExpertHooks.from_expert_dir(expert_dir)
        assert result is None

    def test_from_expert_dir_empty_hooks_file(self, temp_dir: Path) -> None:
        """Test returns None when hooks file is empty."""
        expert_dir = temp_dir / "test_expert"
        hooks_dir = expert_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text("")

        result = ExpertHooks.from_expert_dir(expert_dir)
        assert result is None

    def test_from_expert_dir_single_script_as_string(self, temp_dir: Path) -> None:
        """Test parsing single script as string instead of list."""
        expert_dir = temp_dir / "test_expert"
        hooks_dir = expert_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text("Stop: cleanup.sh\n")

        result = ExpertHooks.from_expert_dir(expert_dir)

        assert result is not None
        assert len(result.hooks["Stop"]) == 1
        assert result.hooks["Stop"][0].script == "cleanup.sh"


class TestCollectExpertHooks:
    """Tests for collect_expert_hooks function."""

    def test_collects_hooks_from_multiple_experts(self, temp_dir: Path) -> None:
        """Test collecting hooks from multiple expert directories."""
        experts_dir = temp_dir / "experts"

        # Create first expert with hooks
        expert1_dir = experts_dir / "expert1"
        (expert1_dir / "hooks").mkdir(parents=True)
        (expert1_dir / "expert.yml").write_text(
            "discovery_description: test\nfull_expertise: test\n"
        )
        (expert1_dir / "hooks" / "global_hooks.yml").write_text("Stop:\n  - hook1.sh\n")

        # Create second expert with hooks
        expert2_dir = experts_dir / "expert2"
        (expert2_dir / "hooks").mkdir(parents=True)
        (expert2_dir / "expert.yml").write_text(
            "discovery_description: test\nfull_expertise: test\n"
        )
        (expert2_dir / "hooks" / "global_hooks.yml").write_text("Stop:\n  - hook2.sh\n")

        # Create expert without hooks
        expert3_dir = experts_dir / "expert3"
        expert3_dir.mkdir(parents=True)
        (expert3_dir / "expert.yml").write_text(
            "discovery_description: test\nfull_expertise: test\n"
        )

        result = collect_expert_hooks(experts_dir)

        assert len(result) == 2
        expert_names = {eh.expert_name for eh in result}
        assert expert_names == {"expert1", "expert2"}

    def test_returns_empty_for_nonexistent_dir(self, temp_dir: Path) -> None:
        """Test returns empty list when experts dir doesn't exist."""
        experts_dir = temp_dir / "nonexistent"
        result = collect_expert_hooks(experts_dir)
        assert result == []


class TestMergeHooksForPlatform:
    """Tests for merge_hooks_for_platform function."""

    def test_merges_hooks_from_multiple_experts(self, temp_dir: Path) -> None:
        """Test merging hooks from multiple experts."""
        # Create expert directories
        expert1_dir = temp_dir / ".deepwork" / "experts" / "expert1"
        expert2_dir = temp_dir / ".deepwork" / "experts" / "expert2"
        expert1_dir.mkdir(parents=True)
        expert2_dir.mkdir(parents=True)

        expert_hooks_list = [
            ExpertHooks(
                expert_name="expert1",
                expert_dir=expert1_dir,
                hooks={"Stop": [HookSpec(script="hook1.sh")]},
            ),
            ExpertHooks(
                expert_name="expert2",
                expert_dir=expert2_dir,
                hooks={
                    "Stop": [HookSpec(script="hook2.sh")],
                    "UserPromptSubmit": [HookSpec(script="capture.sh")],
                },
            ),
        ]

        result = merge_hooks_for_platform(expert_hooks_list, temp_dir)

        assert "Stop" in result
        assert "UserPromptSubmit" in result
        assert len(result["Stop"]) == 2
        assert len(result["UserPromptSubmit"]) == 1

    def test_avoids_duplicate_hooks(self, temp_dir: Path) -> None:
        """Test that duplicate hooks are not added."""
        expert_dir = temp_dir / ".deepwork" / "experts" / "expert1"
        expert_dir.mkdir(parents=True)

        # Same hook in same expert (shouldn't happen but test anyway)
        expert_hooks_list = [
            ExpertHooks(
                expert_name="expert1",
                expert_dir=expert_dir,
                hooks={"Stop": [HookSpec(script="hook.sh"), HookSpec(script="hook.sh")]},
            ),
        ]

        result = merge_hooks_for_platform(expert_hooks_list, temp_dir)

        # Should only have one entry
        assert len(result["Stop"]) == 1

    def test_duplicates_stop_hooks_to_subagent_stop(self, temp_dir: Path) -> None:
        """Test that Stop hooks are also registered for SubagentStop event.

        Claude Code has separate Stop and SubagentStop events. When a Stop hook
        is defined, it should also be registered for SubagentStop so the hook
        triggers for both the main agent and subagents.
        """
        expert_dir = temp_dir / ".deepwork" / "experts" / "expert1"
        expert_dir.mkdir(parents=True)

        expert_hooks_list = [
            ExpertHooks(
                expert_name="expert1",
                expert_dir=expert_dir,
                hooks={"Stop": [HookSpec(script="hook.sh")]},
            ),
        ]

        result = merge_hooks_for_platform(expert_hooks_list, temp_dir)

        # Should have both Stop and SubagentStop events
        assert "Stop" in result
        assert "SubagentStop" in result
        assert len(result["Stop"]) == 1
        assert len(result["SubagentStop"]) == 1

        # Both should have the same hook command
        stop_cmd = result["Stop"][0]["hooks"][0]["command"]
        subagent_stop_cmd = result["SubagentStop"][0]["hooks"][0]["command"]
        assert stop_cmd == subagent_stop_cmd == ".deepwork/experts/expert1/hooks/hook.sh"

    def test_does_not_duplicate_subagent_stop_if_no_stop(self, temp_dir: Path) -> None:
        """Test that SubagentStop is not created if there are no Stop hooks."""
        expert_dir = temp_dir / ".deepwork" / "experts" / "expert1"
        expert_dir.mkdir(parents=True)

        expert_hooks_list = [
            ExpertHooks(
                expert_name="expert1",
                expert_dir=expert_dir,
                hooks={"UserPromptSubmit": [HookSpec(script="capture.sh")]},
            ),
        ]

        result = merge_hooks_for_platform(expert_hooks_list, temp_dir)

        # Should only have UserPromptSubmit, not SubagentStop
        assert "UserPromptSubmit" in result
        assert "SubagentStop" not in result
        assert "Stop" not in result


class TestSyncHooksToPlatform:
    """Tests for sync_hooks_to_platform function using adapters."""

    def test_syncs_hooks_via_adapter(self, temp_dir: Path) -> None:
        """Test syncing hooks to platform via adapter."""
        # Create .claude directory
        (temp_dir / ".claude").mkdir(parents=True)

        adapter = ClaudeAdapter(temp_dir)

        # Create expert directories
        expert_dir = temp_dir / ".deepwork" / "experts" / "test_expert"
        expert_dir.mkdir(parents=True)

        expert_hooks_list = [
            ExpertHooks(
                expert_name="test_expert",
                expert_dir=expert_dir,
                hooks={"Stop": [HookSpec(script="test_hook.sh")]},
            ),
        ]

        count = sync_hooks_to_platform(temp_dir, adapter, expert_hooks_list)

        # Count is 2 because Stop hooks are also registered for SubagentStop
        assert count == 2

        # Verify settings.json was created
        settings_file = temp_dir / ".claude" / "settings.json"
        assert settings_file.exists()

        with open(settings_file) as f:
            settings = json.load(f)

        assert "hooks" in settings
        assert "Stop" in settings["hooks"]
        assert "SubagentStop" in settings["hooks"]

    def test_returns_zero_for_empty_hooks(self, temp_dir: Path) -> None:
        """Test returns 0 when no hooks to sync."""
        adapter = ClaudeAdapter(temp_dir)

        count = sync_hooks_to_platform(temp_dir, adapter, [])

        assert count == 0

    def test_merges_with_existing_settings(self, temp_dir: Path) -> None:
        """Test merging hooks into existing settings.json."""
        # Create .claude directory with existing settings
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir(parents=True)

        existing_settings = {
            "version": "1.0",
            "hooks": {
                "PreToolUse": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "existing.sh"}]}
                ]
            },
        }
        settings_file = claude_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(existing_settings, f)

        adapter = ClaudeAdapter(temp_dir)

        expert_dir = temp_dir / ".deepwork" / "experts" / "test_expert"
        expert_dir.mkdir(parents=True)

        expert_hooks_list = [
            ExpertHooks(
                expert_name="test_expert",
                expert_dir=expert_dir,
                hooks={"Stop": [HookSpec(script="new_hook.sh")]},
            ),
        ]

        sync_hooks_to_platform(temp_dir, adapter, expert_hooks_list)

        with open(settings_file) as f:
            settings = json.load(f)

        # Should preserve existing settings
        assert settings["version"] == "1.0"
        assert "PreToolUse" in settings["hooks"]

        # Should add new hooks
        assert "Stop" in settings["hooks"]
        assert len(settings["hooks"]["Stop"]) == 1
