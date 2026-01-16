"""Tests for policy_stop_hook.sh shell script.

These tests verify that the policy stop hook correctly outputs JSON
to block or allow the stop event in Claude Code.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
from git import Repo

from .conftest import run_shell_script


@pytest.fixture
def git_repo_with_src_policy(tmp_path: Path) -> Path:
    """Create a git repo with a v2 policy file that triggers on src/** changes."""
    repo = Repo.init(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create v2 policy directory and file
    policies_dir = tmp_path / ".deepwork" / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)

    # Use compare_to: prompt since test repos don't have origin remote
    policy_file = policies_dir / "test-policy.md"
    policy_file.write_text(
        """---
name: Test Policy
trigger: "src/**/*"
compare_to: prompt
---
This is a test policy that fires when src/ files change.
Please address this policy.
"""
    )

    # Empty baseline means all current files are "new"
    deepwork_dir = tmp_path / ".deepwork"
    (deepwork_dir / ".last_work_tree").write_text("")

    return tmp_path


def run_stop_hook(
    script_path: Path,
    cwd: Path,
    hook_input: dict | None = None,
) -> tuple[str, str, int]:
    """Run the policy_stop_hook.sh script and return its output."""
    return run_shell_script(script_path, cwd, hook_input=hook_input)


class TestPolicyStopHookBlocking:
    """Tests for policy_stop_hook.sh blocking behavior."""

    def test_outputs_block_json_when_policy_fires(
        self, policy_hooks_dir: Path, git_repo_with_src_policy: Path
    ) -> None:
        """Test that the hook outputs blocking JSON when a policy fires."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_src_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_policy)
        repo.index.add(["src/main.py"])

        # Run the stop hook
        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_src_policy)

        # Parse the output as JSON
        output = stdout.strip()
        assert output, f"Expected JSON output but got empty string. stderr: {stderr}"

        try:
            result = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {output!r}. Error: {e}")

        # Verify the JSON has the blocking structure
        assert "decision" in result, f"Expected 'decision' key in JSON: {result}"
        assert result["decision"] == "block", f"Expected decision='block', got: {result}"
        assert "reason" in result, f"Expected 'reason' key in JSON: {result}"
        assert "Test Policy" in result["reason"], f"Policy name not in reason: {result}"

    def test_outputs_empty_json_when_no_policy_fires(
        self, policy_hooks_dir: Path, git_repo_with_src_policy: Path
    ) -> None:
        """Test that the hook outputs empty JSON when no policy fires."""
        # Don't create any files that would trigger the policy
        # (policy triggers on src/** but we haven't created anything in src/)

        # Run the stop hook
        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_src_policy)

        # Parse the output as JSON
        output = stdout.strip()
        assert output, f"Expected JSON output but got empty string. stderr: {stderr}"

        try:
            result = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {output!r}. Error: {e}")

        # Should be empty JSON (no blocking)
        assert result == {}, f"Expected empty JSON when no policies fire, got: {result}"

    def test_exits_early_when_no_policy_dir(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook exits cleanly when no policy directory exists."""
        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo)

        # Should exit with code 0 and produce no output (or empty)
        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"
        # No output is fine when there's no policy directory
        output = stdout.strip()
        if output:
            # If there is output, it should be valid JSON
            try:
                result = json.loads(output)
                assert result == {}, f"Expected empty JSON, got: {result}"
            except json.JSONDecodeError:
                # Empty or no output is acceptable
                pass

    def test_respects_promise_tags(
        self, policy_hooks_dir: Path, git_repo_with_src_policy: Path
    ) -> None:
        """Test that promised policies are not re-triggered."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_src_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_policy)
        repo.index.add(["src/main.py"])

        # Create a mock transcript with the promise tag
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            transcript_path = f.name
            # Write a mock assistant message with the promise tag
            f.write(
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "I've addressed the policy. <promise>✓ Test Policy</promise>",
                                }
                            ]
                        },
                    }
                )
            )
            f.write("\n")

        try:
            # Run the stop hook with transcript path
            script_path = policy_hooks_dir / "policy_stop_hook.sh"
            hook_input = {"transcript_path": transcript_path, "hook_event_name": "Stop"}
            stdout, stderr, code = run_stop_hook(script_path, git_repo_with_src_policy, hook_input)

            # Parse the output
            output = stdout.strip()
            assert output, f"Expected JSON output. stderr: {stderr}"

            result = json.loads(output)

            # Should be empty JSON because the policy was promised
            assert result == {}, f"Expected empty JSON when policy is promised, got: {result}"
        finally:
            os.unlink(transcript_path)

    def test_safety_pattern_prevents_firing(self, policy_hooks_dir: Path, tmp_path: Path) -> None:
        """Test that safety patterns prevent policies from firing."""
        # Initialize git repo
        repo = Repo.init(tmp_path)

        readme = tmp_path / "README.md"
        readme.write_text("# Test Project\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create v2 policy with a safety pattern
        policies_dir = tmp_path / ".deepwork" / "policies"
        policies_dir.mkdir(parents=True, exist_ok=True)

        policy_file = policies_dir / "documentation-policy.md"
        policy_file.write_text(
            """---
name: Documentation Policy
trigger: "src/**/*"
safety: "docs/**/*"
compare_to: prompt
---
Update documentation when changing source files.
"""
        )

        # Create .deepwork directory with empty baseline
        deepwork_dir = tmp_path / ".deepwork"
        (deepwork_dir / ".last_work_tree").write_text("")

        # Create both trigger and safety files
        src_dir = tmp_path / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# Source file\n")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "api.md").write_text("# API docs\n")

        # Stage both changes so they appear in git diff --cached
        repo.index.add(["src/main.py", "docs/api.md"])

        # Run the stop hook
        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, tmp_path)

        # Parse the output
        output = stdout.strip()
        assert output, f"Expected JSON output. stderr: {stderr}"

        result = json.loads(output)

        # Should be empty JSON because safety pattern matched
        assert result == {}, f"Expected empty JSON when safety pattern matches, got: {result}"


class TestPolicyStopHookJsonFormat:
    """Tests for the JSON output format of policy_stop_hook.sh."""

    def test_json_has_correct_structure(
        self, policy_hooks_dir: Path, git_repo_with_src_policy: Path
    ) -> None:
        """Test that blocking JSON has the correct Claude Code structure."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_src_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_src_policy)
        repo.index.add(["src/main.py"])

        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_src_policy)

        result = json.loads(stdout.strip())

        # Verify exact structure expected by Claude Code
        assert set(result.keys()) == {
            "decision",
            "reason",
        }, f"Unexpected keys in JSON: {result.keys()}"
        assert result["decision"] == "block"
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0

    def test_reason_contains_policy_instructions(
        self, policy_hooks_dir: Path, git_repo_with_src_policy: Path
    ) -> None:
        """Test that the reason includes the policy instructions."""
        src_dir = git_repo_with_src_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_src_policy)
        repo.index.add(["src/main.py"])

        script_path = policy_hooks_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_src_policy)

        result = json.loads(stdout.strip())

        # Check that the reason contains the policy content
        reason = result["reason"]
        assert "DeepWork Policies Triggered" in reason
        assert "Test Policy" in reason
        assert "test policy that fires" in reason
