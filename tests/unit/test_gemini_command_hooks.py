"""Tests for Gemini command hooks emulation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Import the module under test
# Since it's in templates, we need to import it differently
import importlib.util

# Load the module from the templates directory
SCRIPT_PATH = (
    Path(__file__).parent.parent.parent
    / "src"
    / "deepwork"
    / "templates"
    / "gemini"
    / "scripts"
    / "command_hooks"
    / "parse_command_hooks.py"
)

spec = importlib.util.spec_from_file_location("parse_command_hooks", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
parse_command_hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parse_command_hooks)


class TestDetectSlashCommand:
    """Tests for detect_slash_command function."""

    def test_detect_colon_separator(self) -> None:
        """Test detection with colon separator."""
        prompt = "Please run /deepwork_jobs:define for me"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "deepwork_jobs:define"
        assert job == "deepwork_jobs"
        assert step == "define"

    def test_detect_slash_separator(self) -> None:
        """Test detection with slash separator."""
        prompt = "Run /my_job/step_one please"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "my_job:step_one"
        assert job == "my_job"
        assert step == "step_one"

    def test_detect_at_start(self) -> None:
        """Test detection when command is at start of prompt."""
        prompt = "/competitive_research:identify run this"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "competitive_research:identify"
        assert job == "competitive_research"
        assert step == "identify"

    def test_detect_no_command(self) -> None:
        """Test when there's no slash command."""
        prompt = "Just do some regular work please"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd is None
        assert job is None
        assert step is None

    def test_detect_partial_command(self) -> None:
        """Test partial slash (no step) is not matched."""
        prompt = "Run /deepwork_jobs please"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd is None
        assert job is None
        assert step is None

    def test_detect_case_insensitive(self) -> None:
        """Test detection is case insensitive."""
        prompt = "/MyJob:MyStep"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "myjob:mystep"
        assert job == "myjob"
        assert step == "mystep"

    def test_detect_with_numbers(self) -> None:
        """Test detection with numbers in names."""
        prompt = "/job123:step456"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "job123:step456"
        assert job == "job123"
        assert step == "step456"

    def test_detect_with_underscores(self) -> None:
        """Test detection with underscores."""
        prompt = "/my_complex_job:my_step_name"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "my_complex_job:my_step_name"
        assert job == "my_complex_job"
        assert step == "my_step_name"

    def test_detect_multiple_commands_finds_first(self) -> None:
        """Test that first command is found when multiple present."""
        prompt = "/first_job:step1 and also /second_job:step2"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        assert cmd == "first_job:step1"
        assert job == "first_job"
        assert step == "step1"

    def test_detect_command_not_at_word_boundary(self) -> None:
        """Test that /cmd inside a word is not matched."""
        prompt = "check out https://example.com/foo:bar"
        cmd, job, step = parse_command_hooks.detect_slash_command(prompt)
        # This should still match because the pattern looks for space or start
        # but the URL case is tricky - let's verify behavior
        # Actually the pattern uses (?:^|\s) which requires start or whitespace
        # The URL has / after .com so it shouldn't match as a slash command
        assert cmd is None  # Should not match mid-URL


class TestStateManagement:
    """Tests for state file management functions."""

    @pytest.fixture
    def mock_project(self, tmp_path: Path) -> Path:
        """Create a mock project with .deepwork directory."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        return tmp_path

    def test_get_state_file_path(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test state file path is in .deepwork directory."""
        monkeypatch.chdir(mock_project)
        path = parse_command_hooks.get_state_file_path()
        assert path == mock_project / ".deepwork" / ".command_hook_state.json"

    def test_save_and_load_state(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test saving and loading state."""
        monkeypatch.chdir(mock_project)

        state = {
            "slash_command": "test_job:test_step",
            "job_name": "test_job",
            "step_id": "test_step",
            "hooks": {"after_agent": [{"type": "prompt", "content": "Check"}]},
        }

        parse_command_hooks.save_state(state)
        loaded = parse_command_hooks.load_state()

        assert loaded["slash_command"] == "test_job:test_step"
        assert loaded["job_name"] == "test_job"
        assert loaded["step_id"] == "test_step"
        assert len(loaded["hooks"]["after_agent"]) == 1

    def test_load_state_no_file(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading state when no file exists."""
        monkeypatch.chdir(mock_project)
        state = parse_command_hooks.load_state()
        assert state["slash_command"] is None
        assert state["job_name"] is None
        assert state["step_id"] is None
        assert state["hooks"] == {}

    def test_clear_state(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test clearing state removes the file."""
        monkeypatch.chdir(mock_project)

        # First save some state
        state = {"slash_command": "test:test", "hooks": {}}
        parse_command_hooks.save_state(state)

        state_path = parse_command_hooks.get_state_file_path()
        assert state_path.exists()

        # Clear it
        parse_command_hooks.clear_state()
        assert not state_path.exists()

    def test_clear_state_no_file(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test clearing state when no file exists doesn't error."""
        monkeypatch.chdir(mock_project)
        # Should not raise
        parse_command_hooks.clear_state()

    def test_load_state_corrupted_json(self, mock_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading corrupted state file returns default."""
        monkeypatch.chdir(mock_project)

        state_path = mock_project / ".deepwork" / ".command_hook_state.json"
        state_path.write_text("not valid json {{{")

        state = parse_command_hooks.load_state()
        assert state["slash_command"] is None


class TestFindJobYml:
    """Tests for find_job_yml function."""

    @pytest.fixture
    def project_with_job(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create a project with a job definition."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()

        jobs_dir = deepwork_dir / "jobs" / "my_job"
        jobs_dir.mkdir(parents=True)

        job_yml = jobs_dir / "job.yml"
        job_yml.write_text(yaml.dump({
            "name": "my_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{"prompt": "Check quality"}],
                }
            ],
        }))

        return tmp_path, job_yml

    def test_find_user_job(
        self, project_with_job: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test finding a user-defined job."""
        project, expected_path = project_with_job
        monkeypatch.chdir(project)

        result = parse_command_hooks.find_job_yml("my_job")
        assert result == expected_path

    def test_find_nonexistent_job(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test finding a job that doesn't exist."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        result = parse_command_hooks.find_job_yml("nonexistent_job")
        assert result is None


class TestParseJobHooks:
    """Tests for parse_job_hooks function."""

    @pytest.fixture
    def job_yml_with_stop_hooks(self, tmp_path: Path) -> Path:
        """Create a job.yml with stop_hooks (deprecated format)."""
        job_yml = tmp_path / "job.yml"
        job_yml.write_text(yaml.dump({
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test",
            "steps": [
                {
                    "id": "define",
                    "name": "Define",
                    "description": "Define step",
                    "instructions_file": "steps/define.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [
                        {"prompt": "Check quality criteria"},
                        {"script": "hooks/validate.sh"},
                    ],
                }
            ],
        }))
        return job_yml

    @pytest.fixture
    def job_yml_with_hooks_dict(self, tmp_path: Path) -> Path:
        """Create a job.yml with new hooks format."""
        job_yml = tmp_path / "job.yml"
        job_yml.write_text(yaml.dump({
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test",
            "steps": [
                {
                    "id": "build",
                    "name": "Build",
                    "description": "Build step",
                    "instructions_file": "steps/build.md",
                    "outputs": ["output.md"],
                    "hooks": {
                        "after_agent": [{"prompt": "Verify build"}],
                        "before_prompt": [{"script": "hooks/setup.sh"}],
                    },
                }
            ],
        }))
        return job_yml

    def test_parse_stop_hooks(self, job_yml_with_stop_hooks: Path) -> None:
        """Test parsing deprecated stop_hooks format."""
        hooks = parse_command_hooks.parse_job_hooks(job_yml_with_stop_hooks, "define")

        assert "after_agent" in hooks
        assert len(hooks["after_agent"]) == 2
        assert hooks["after_agent"][0]["prompt"] == "Check quality criteria"
        assert hooks["after_agent"][1]["script"] == "hooks/validate.sh"

    def test_parse_hooks_dict(self, job_yml_with_hooks_dict: Path) -> None:
        """Test parsing new hooks format."""
        hooks = parse_command_hooks.parse_job_hooks(job_yml_with_hooks_dict, "build")

        assert "after_agent" in hooks
        assert "before_prompt" in hooks
        assert len(hooks["after_agent"]) == 1
        assert len(hooks["before_prompt"]) == 1
        assert hooks["after_agent"][0]["prompt"] == "Verify build"
        assert hooks["before_prompt"][0]["script"] == "hooks/setup.sh"

    def test_parse_nonexistent_step(self, job_yml_with_stop_hooks: Path) -> None:
        """Test parsing hooks for a step that doesn't exist."""
        hooks = parse_command_hooks.parse_job_hooks(job_yml_with_stop_hooks, "nonexistent")
        assert hooks == {}

    def test_parse_step_no_hooks(self, tmp_path: Path) -> None:
        """Test parsing step with no hooks."""
        job_yml = tmp_path / "job.yml"
        job_yml.write_text(yaml.dump({
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test",
            "steps": [
                {
                    "id": "simple",
                    "name": "Simple",
                    "description": "No hooks",
                    "instructions_file": "steps/simple.md",
                    "outputs": ["out.md"],
                }
            ],
        }))

        hooks = parse_command_hooks.parse_job_hooks(job_yml, "simple")
        assert hooks == {}

    def test_parse_invalid_yaml(self, tmp_path: Path) -> None:
        """Test parsing invalid YAML returns empty dict."""
        job_yml = tmp_path / "job.yml"
        job_yml.write_text("not: valid: yaml: {{{}}")

        hooks = parse_command_hooks.parse_job_hooks(job_yml, "any")
        assert hooks == {}


class TestBuildHookContext:
    """Tests for build_hook_context function."""

    def test_build_prompt_hook_context(self, tmp_path: Path) -> None:
        """Test building context for inline prompt hook."""
        job_yml = tmp_path / "job.yml"
        hook_action = {"prompt": "Check all criteria"}

        context = parse_command_hooks.build_hook_context(hook_action, job_yml)

        assert context["type"] == "prompt"
        assert context["content"] == "Check all criteria"

    def test_build_prompt_file_hook_context(self, tmp_path: Path) -> None:
        """Test building context for prompt file hook."""
        job_dir = tmp_path / "my_job"
        job_dir.mkdir()
        job_yml = job_dir / "job.yml"

        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir()
        prompt_file = hooks_dir / "quality.md"
        prompt_file.write_text("Verify quality criteria:\n1. Check A\n2. Check B")

        hook_action = {"prompt_file": "hooks/quality.md"}

        context = parse_command_hooks.build_hook_context(hook_action, job_yml)

        assert context["type"] == "prompt"
        assert "Verify quality criteria" in context["content"]

    def test_build_prompt_file_missing(self, tmp_path: Path) -> None:
        """Test building context when prompt file is missing."""
        job_yml = tmp_path / "job.yml"
        hook_action = {"prompt_file": "nonexistent.md"}

        context = parse_command_hooks.build_hook_context(hook_action, job_yml)

        assert context["type"] == "prompt"
        assert "not found" in context["content"]

    def test_build_script_hook_context(self, tmp_path: Path) -> None:
        """Test building context for script hook."""
        job_yml = tmp_path / "job.yml"
        hook_action = {"script": "hooks/validate.sh"}

        context = parse_command_hooks.build_hook_context(hook_action, job_yml)

        assert context["type"] == "script"
        assert context["script"] == str(tmp_path / "hooks/validate.sh")
        assert context["content"] == "hooks/validate.sh"


class TestExecuteHook:
    """Tests for execute_hook function."""

    def test_execute_prompt_hook(self) -> None:
        """Test executing a prompt hook returns inject content."""
        hook_context = {
            "type": "prompt",
            "content": "Please verify the output",
        }

        result = parse_command_hooks.execute_hook(hook_context)

        assert result["success"] is True
        assert result["type"] == "prompt"
        assert result["inject_prompt"] == "Please verify the output"

    def test_execute_script_hook_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test executing a successful script hook."""
        monkeypatch.chdir(tmp_path)

        # Create a deepwork dir for find_project_root
        (tmp_path / ".deepwork").mkdir()

        script = tmp_path / "test_hook.sh"
        script.write_text("#!/bin/bash\necho 'Hook executed successfully'")
        script.chmod(0o755)

        hook_context = {
            "type": "script",
            "script": str(script),
            "content": "test_hook.sh",
        }

        result = parse_command_hooks.execute_hook(hook_context)

        assert result["success"] is True
        assert result["type"] == "script"
        assert "Hook executed successfully" in result["output"]

    def test_execute_script_hook_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test executing a script hook that exits with code 2 (blocking)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".deepwork").mkdir()

        script = tmp_path / "failing_hook.sh"
        script.write_text("#!/bin/bash\necho 'Error occurred' >&2\nexit 2")
        script.chmod(0o755)

        hook_context = {
            "type": "script",
            "script": str(script),
            "content": "failing_hook.sh",
        }

        result = parse_command_hooks.execute_hook(hook_context)

        assert result["success"] is False
        assert "Error occurred" in result["output"]

    def test_execute_script_hook_not_found(self) -> None:
        """Test executing a script hook when script doesn't exist."""
        hook_context = {
            "type": "script",
            "script": "/nonexistent/path/hook.sh",
            "content": "hook.sh",
        }

        result = parse_command_hooks.execute_hook(hook_context)

        assert result["success"] is False
        assert "not found" in result["output"]

    def test_execute_script_with_transcript_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test script receives TRANSCRIPT_PATH environment variable."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".deepwork").mkdir()

        script = tmp_path / "env_hook.sh"
        script.write_text("#!/bin/bash\necho \"TRANSCRIPT=$TRANSCRIPT_PATH\"")
        script.chmod(0o755)

        hook_context = {
            "type": "script",
            "script": str(script),
            "content": "env_hook.sh",
        }

        result = parse_command_hooks.execute_hook(hook_context, transcript_path="/path/to/transcript.jsonl")

        assert result["success"] is True
        assert "TRANSCRIPT=/path/to/transcript.jsonl" in result["output"]


class TestCLICommands:
    """Tests for CLI command functions."""

    @pytest.fixture
    def project_setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Set up a project with job definition."""
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()

        jobs_dir = deepwork_dir / "jobs" / "test_job"
        jobs_dir.mkdir(parents=True)

        job_yml = jobs_dir / "job.yml"
        job_yml.write_text(yaml.dump({
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Test step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["out.md"],
                    "stop_hooks": [{"prompt": "Verify output"}],
                }
            ],
        }))

        monkeypatch.chdir(tmp_path)
        return tmp_path

    def test_cmd_detect_with_command(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test detect command finds slash command."""
        import argparse
        args = argparse.Namespace(prompt="/test_job:step1 please run this")

        exit_code = parse_command_hooks.cmd_detect(args)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["slash_command"] == "test_job:step1"
        assert output["job_name"] == "test_job"
        assert output["step_id"] == "step1"
        assert output["has_hooks"] is True

    def test_cmd_detect_no_command(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test detect command when no slash command present."""
        import argparse
        args = argparse.Namespace(prompt="Just regular text")

        exit_code = parse_command_hooks.cmd_detect(args)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["slash_command"] is None
        assert output["has_hooks"] is False

    def test_cmd_get_hooks(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test get-hooks command."""
        import argparse

        # First detect to save state
        detect_args = argparse.Namespace(prompt="/test_job:step1")
        parse_command_hooks.cmd_detect(detect_args)
        capsys.readouterr()  # Clear output from detect

        # Now get hooks
        get_args = argparse.Namespace(event="after_agent")
        exit_code = parse_command_hooks.cmd_get_hooks(get_args)

        assert exit_code == 0

        captured = capsys.readouterr()
        hooks = json.loads(captured.out)

        assert len(hooks) == 1
        assert hooks[0]["type"] == "prompt"
        assert hooks[0]["content"] == "Verify output"

    def test_cmd_run_hooks(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run-hooks command."""
        import argparse

        # First detect to save state
        detect_args = argparse.Namespace(prompt="/test_job:step1")
        parse_command_hooks.cmd_detect(detect_args)
        capsys.readouterr()  # Clear output

        # Now run hooks
        run_args = argparse.Namespace(event="after_agent", transcript_path=None)
        exit_code = parse_command_hooks.cmd_run_hooks(run_args)

        assert exit_code == 0

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["executed"] == 1
        assert result["success"] is True
        assert "inject_prompt" in result
        assert "Verify output" in result["inject_prompt"]

    def test_cmd_run_hooks_no_hooks(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run-hooks when no hooks exist for event."""
        import argparse

        # Detect a command
        detect_args = argparse.Namespace(prompt="/test_job:step1")
        parse_command_hooks.cmd_detect(detect_args)
        capsys.readouterr()

        # Run hooks for an event that doesn't have any
        run_args = argparse.Namespace(event="before_prompt", transcript_path=None)
        exit_code = parse_command_hooks.cmd_run_hooks(run_args)

        assert exit_code == 0

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["executed"] == 0

    def test_cmd_clear(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test clear command."""
        import argparse

        # First save some state
        detect_args = argparse.Namespace(prompt="/test_job:step1")
        parse_command_hooks.cmd_detect(detect_args)
        capsys.readouterr()

        # Verify state exists
        state = parse_command_hooks.load_state()
        assert state["slash_command"] is not None

        # Clear
        clear_args = argparse.Namespace()
        exit_code = parse_command_hooks.cmd_clear(clear_args)

        assert exit_code == 0

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["cleared"] is True

        # Verify state is cleared
        state = parse_command_hooks.load_state()
        assert state["slash_command"] is None

    def test_cmd_get_state(
        self, project_setup: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test get-state command."""
        import argparse

        # Save some state
        detect_args = argparse.Namespace(prompt="/test_job:step1")
        parse_command_hooks.cmd_detect(detect_args)
        capsys.readouterr()

        # Get state
        state_args = argparse.Namespace()
        exit_code = parse_command_hooks.cmd_get_state(state_args)

        assert exit_code == 0

        captured = capsys.readouterr()
        state = json.loads(captured.out)

        assert state["slash_command"] == "test_job:step1"
        assert state["job_name"] == "test_job"
        assert state["step_id"] == "step1"


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_find_root_with_deepwork(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test finding root when .deepwork exists."""
        (tmp_path / ".deepwork").mkdir()
        subdir = tmp_path / "src" / "app"
        subdir.mkdir(parents=True)

        monkeypatch.chdir(subdir)

        root = parse_command_hooks.find_project_root()
        assert root == tmp_path

    def test_find_root_with_gemini(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test finding root when .gemini exists."""
        (tmp_path / ".gemini").mkdir()
        subdir = tmp_path / "lib"
        subdir.mkdir()

        monkeypatch.chdir(subdir)

        root = parse_command_hooks.find_project_root()
        assert root == tmp_path

    def test_find_root_no_marker(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test finding root when no marker directory exists."""
        monkeypatch.chdir(tmp_path)

        root = parse_command_hooks.find_project_root()
        # Should return cwd when no marker found
        assert root == tmp_path


class TestIntegration:
    """Integration tests for the full workflow."""

    @pytest.fixture
    def full_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a complete project setup."""
        # Create .deepwork structure
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir()

        # Create job
        job_dir = deepwork_dir / "jobs" / "research"
        job_dir.mkdir(parents=True)
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir()

        # Write step instruction
        (steps_dir / "gather.md").write_text("# Gather Research\nCollect data.")

        # Write hook script
        hook_script = hooks_dir / "validate.sh"
        hook_script.write_text("#!/bin/bash\necho 'Validation passed'")
        hook_script.chmod(0o755)

        # Write job.yml with multiple hooks
        (job_dir / "job.yml").write_text(yaml.dump({
            "name": "research",
            "version": "1.0.0",
            "summary": "Research workflow",
            "steps": [
                {
                    "id": "gather",
                    "name": "Gather Data",
                    "description": "Collect research data",
                    "instructions_file": "steps/gather.md",
                    "outputs": ["data.md"],
                    "hooks": {
                        "before_prompt": [
                            {"prompt": "Initialize research context"},
                        ],
                        "after_agent": [
                            {"prompt": "Verify data quality"},
                            {"script": "hooks/validate.sh"},
                        ],
                    },
                }
            ],
        }))

        monkeypatch.chdir(tmp_path)
        return tmp_path

    def test_full_workflow(
        self, full_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test complete detect -> run hooks workflow."""
        import argparse

        # 1. Detect command
        detect_args = argparse.Namespace(prompt="/research:gather please start")
        exit_code = parse_command_hooks.cmd_detect(detect_args)
        assert exit_code == 0

        captured = capsys.readouterr()
        detect_result = json.loads(captured.out)
        assert detect_result["slash_command"] == "research:gather"
        assert detect_result["has_hooks"] is True

        # 2. Run before_prompt hooks
        run_args = argparse.Namespace(event="before_prompt", transcript_path=None)
        exit_code = parse_command_hooks.cmd_run_hooks(run_args)
        assert exit_code == 0

        captured = capsys.readouterr()
        before_result = json.loads(captured.out)
        assert before_result["executed"] == 1
        assert "Initialize research context" in before_result.get("inject_prompt", "")

        # 3. Run after_agent hooks
        run_args = argparse.Namespace(event="after_agent", transcript_path=None)
        exit_code = parse_command_hooks.cmd_run_hooks(run_args)
        assert exit_code == 0

        captured = capsys.readouterr()
        after_result = json.loads(captured.out)
        assert after_result["executed"] == 2
        assert after_result["success"] is True

        # 4. Clear state
        clear_args = argparse.Namespace()
        exit_code = parse_command_hooks.cmd_clear(clear_args)
        assert exit_code == 0

        # 5. Verify state is cleared
        state = parse_command_hooks.load_state()
        assert state["slash_command"] is None

    def test_no_command_workflow(
        self, full_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test workflow when no slash command is detected."""
        import argparse

        # Detect with no command
        detect_args = argparse.Namespace(prompt="Just do some work")
        exit_code = parse_command_hooks.cmd_detect(detect_args)
        assert exit_code == 0

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["slash_command"] is None
        assert result["has_hooks"] is False

        # Run hooks should do nothing
        run_args = argparse.Namespace(event="after_agent", transcript_path=None)
        exit_code = parse_command_hooks.cmd_run_hooks(run_args)
        assert exit_code == 0

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["executed"] == 0
