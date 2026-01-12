"""Tests for the hooks syncer module."""

import json
from pathlib import Path

import pytest

from deepwork.core.hooks_syncer import (
    HookEntry,
    HooksSyncError,
    JobHooks,
    collect_job_hooks,
    merge_hooks_for_platform,
    sync_hooks_to_claude,
)
from deepwork.core.detector import PlatformConfig


class TestHookEntry:
    """Tests for HookEntry dataclass."""

    def test_get_script_path_relative(self, temp_dir: Path) -> None:
        """Test getting relative script path."""
        job_dir = temp_dir / ".deepwork" / "jobs" / "test_job"
        job_dir.mkdir(parents=True)

        entry = HookEntry(
            script="test_hook.sh",
            job_name="test_job",
            job_dir=job_dir,
        )

        path = entry.get_script_path(temp_dir)
        assert path == ".deepwork/jobs/test_job/hooks/test_hook.sh"


class TestJobHooks:
    """Tests for JobHooks dataclass."""

    def test_from_job_dir_with_hooks(self, temp_dir: Path) -> None:
        """Test loading hooks from job directory."""
        job_dir = temp_dir / "test_job"
        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create global_hooks.yml
        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text(
            """
UserPromptSubmit:
  - capture.sh
Stop:
  - policy_check.sh
  - cleanup.sh
"""
        )

        result = JobHooks.from_job_dir(job_dir)

        assert result is not None
        assert result.job_name == "test_job"
        assert result.hooks["UserPromptSubmit"] == ["capture.sh"]
        assert result.hooks["Stop"] == ["policy_check.sh", "cleanup.sh"]

    def test_from_job_dir_no_hooks_file(self, temp_dir: Path) -> None:
        """Test returns None when no hooks file exists."""
        job_dir = temp_dir / "test_job"
        job_dir.mkdir(parents=True)

        result = JobHooks.from_job_dir(job_dir)
        assert result is None

    def test_from_job_dir_empty_hooks_file(self, temp_dir: Path) -> None:
        """Test returns None when hooks file is empty."""
        job_dir = temp_dir / "test_job"
        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text("")

        result = JobHooks.from_job_dir(job_dir)
        assert result is None

    def test_from_job_dir_single_script_as_string(self, temp_dir: Path) -> None:
        """Test parsing single script as string instead of list."""
        job_dir = temp_dir / "test_job"
        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        hooks_file = hooks_dir / "global_hooks.yml"
        hooks_file.write_text("Stop: cleanup.sh\n")

        result = JobHooks.from_job_dir(job_dir)

        assert result is not None
        assert result.hooks["Stop"] == ["cleanup.sh"]


class TestCollectJobHooks:
    """Tests for collect_job_hooks function."""

    def test_collects_hooks_from_multiple_jobs(self, temp_dir: Path) -> None:
        """Test collecting hooks from multiple job directories."""
        jobs_dir = temp_dir / "jobs"

        # Create first job with hooks
        job1_dir = jobs_dir / "job1"
        (job1_dir / "hooks").mkdir(parents=True)
        (job1_dir / "hooks" / "global_hooks.yml").write_text("Stop:\n  - hook1.sh\n")

        # Create second job with hooks
        job2_dir = jobs_dir / "job2"
        (job2_dir / "hooks").mkdir(parents=True)
        (job2_dir / "hooks" / "global_hooks.yml").write_text("Stop:\n  - hook2.sh\n")

        # Create job without hooks
        job3_dir = jobs_dir / "job3"
        job3_dir.mkdir(parents=True)

        result = collect_job_hooks(jobs_dir)

        assert len(result) == 2
        job_names = {jh.job_name for jh in result}
        assert job_names == {"job1", "job2"}

    def test_returns_empty_for_nonexistent_dir(self, temp_dir: Path) -> None:
        """Test returns empty list when jobs dir doesn't exist."""
        jobs_dir = temp_dir / "nonexistent"
        result = collect_job_hooks(jobs_dir)
        assert result == []


class TestMergeHooksForPlatform:
    """Tests for merge_hooks_for_platform function."""

    def test_merges_hooks_from_multiple_jobs(self, temp_dir: Path) -> None:
        """Test merging hooks from multiple jobs."""
        # Create job directories
        job1_dir = temp_dir / ".deepwork" / "jobs" / "job1"
        job2_dir = temp_dir / ".deepwork" / "jobs" / "job2"
        job1_dir.mkdir(parents=True)
        job2_dir.mkdir(parents=True)

        job_hooks_list = [
            JobHooks(
                job_name="job1",
                job_dir=job1_dir,
                hooks={"Stop": ["hook1.sh"]},
            ),
            JobHooks(
                job_name="job2",
                job_dir=job2_dir,
                hooks={"Stop": ["hook2.sh"], "UserPromptSubmit": ["capture.sh"]},
            ),
        ]

        result = merge_hooks_for_platform(job_hooks_list, temp_dir)

        assert "Stop" in result
        assert "UserPromptSubmit" in result
        assert len(result["Stop"]) == 2
        assert len(result["UserPromptSubmit"]) == 1

    def test_avoids_duplicate_hooks(self, temp_dir: Path) -> None:
        """Test that duplicate hooks are not added."""
        job_dir = temp_dir / ".deepwork" / "jobs" / "job1"
        job_dir.mkdir(parents=True)

        # Same hook in same job (shouldn't happen but test anyway)
        job_hooks_list = [
            JobHooks(
                job_name="job1",
                job_dir=job_dir,
                hooks={"Stop": ["hook.sh", "hook.sh"]},
            ),
        ]

        result = merge_hooks_for_platform(job_hooks_list, temp_dir)

        # Should only have one entry
        assert len(result["Stop"]) == 1


class TestSyncHooksToClaude:
    """Tests for sync_hooks_to_claude function."""

    def test_creates_settings_file(self, temp_dir: Path) -> None:
        """Test creating settings.json when it doesn't exist."""
        platform = PlatformConfig(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            commands_dir="commands",
        )

        # Create .claude directory
        (temp_dir / ".claude").mkdir(parents=True)

        hooks = {
            "Stop": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "test_hook.sh"}],
                }
            ]
        }

        sync_hooks_to_claude(temp_dir, platform, hooks)

        settings_file = temp_dir / ".claude" / "settings.json"
        assert settings_file.exists()

        with open(settings_file) as f:
            settings = json.load(f)

        assert "hooks" in settings
        assert "Stop" in settings["hooks"]
        assert len(settings["hooks"]["Stop"]) == 1

    def test_merges_with_existing_settings(self, temp_dir: Path) -> None:
        """Test merging hooks into existing settings.json."""
        platform = PlatformConfig(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            commands_dir="commands",
        )

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

        hooks = {
            "Stop": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "new_hook.sh"}],
                }
            ]
        }

        sync_hooks_to_claude(temp_dir, platform, hooks)

        with open(settings_file) as f:
            settings = json.load(f)

        # Should preserve existing settings
        assert settings["version"] == "1.0"
        assert "PreToolUse" in settings["hooks"]

        # Should add new hooks
        assert "Stop" in settings["hooks"]
        assert len(settings["hooks"]["Stop"]) == 1

    def test_does_not_duplicate_existing_hooks(self, temp_dir: Path) -> None:
        """Test that existing hooks are not duplicated."""
        platform = PlatformConfig(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            commands_dir="commands",
        )

        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir(parents=True)

        # Settings with existing hook
        existing_settings = {
            "hooks": {
                "Stop": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "hook.sh"}]}
                ]
            },
        }
        settings_file = claude_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(existing_settings, f)

        # Try to add the same hook
        hooks = {
            "Stop": [
                {
                    "matcher": "",
                    "hooks": [{"type": "command", "command": "hook.sh"}],
                }
            ]
        }

        sync_hooks_to_claude(temp_dir, platform, hooks)

        with open(settings_file) as f:
            settings = json.load(f)

        # Should still only have one hook
        assert len(settings["hooks"]["Stop"]) == 1

    def test_handles_empty_hooks(self, temp_dir: Path) -> None:
        """Test that empty hooks dict doesn't modify settings."""
        platform = PlatformConfig(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            commands_dir="commands",
        )

        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir(parents=True)

        # No settings file exists initially
        sync_hooks_to_claude(temp_dir, platform, {})

        # Settings file should not be created
        settings_file = claude_dir / "settings.json"
        assert not settings_file.exists()
