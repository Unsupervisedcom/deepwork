"""Tests for policy_stop_hook.sh shell script.

These tests verify that the policy stop hook correctly outputs JSON
to block or allow the stop event in Claude Code.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def shell_scripts_dir() -> Path:
    """Return the path to the source shell scripts directory."""
    return (
        Path(__file__).parent.parent.parent
        / "src"
        / "deepwork"
        / "standard_jobs"
        / "deepwork_policy"
        / "hooks"
    )


@pytest.fixture
def git_repo_with_policy(tmp_path: Path) -> Path:
    """Create a git repo with a policy file and trigger a policy."""
    # Initialize git repo
    repo = Repo.init(tmp_path)

    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create a policy file that triggers on src/** changes
    # Use compare_to: prompt since test repos don't have origin remote
    policy_file = tmp_path / ".deepwork.policy.yml"
    policy_file.write_text(
        """- name: "Test Policy"
  trigger: "src/**/*"
  compare_to: prompt
  instructions: |
    This is a test policy that fires when src/ files change.
    Please address this policy.
"""
    )

    # Create .deepwork directory with empty baseline
    # (so new files are detected as "changed since prompt")
    deepwork_dir = tmp_path / ".deepwork"
    deepwork_dir.mkdir(exist_ok=True)
    # Empty baseline means all current files are "new"
    (deepwork_dir / ".last_work_tree").write_text("")

    return tmp_path


@pytest.fixture
def git_repo_no_policy(tmp_path: Path) -> Path:
    """Create a git repo without a policy file."""
    repo = Repo.init(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return tmp_path


def run_stop_hook(
    script_path: Path,
    cwd: Path,
    hook_input: dict | None = None,
) -> tuple[str, str, int]:
    """
    Run the policy_stop_hook.sh script and return its output.

    Args:
        script_path: Path to the policy_stop_hook.sh script
        cwd: Working directory to run the script in
        hook_input: Optional JSON input to pass via stdin

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    env = os.environ.copy()
    # Ensure Python can find the deepwork module
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

    stdin_data = json.dumps(hook_input) if hook_input else ""

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        input=stdin_data,
        env=env,
    )

    return result.stdout, result.stderr, result.returncode


class TestPolicyStopHookBlocking:
    """Tests for policy_stop_hook.sh blocking behavior."""

    def test_outputs_block_json_when_policy_fires(
        self, shell_scripts_dir: Path, git_repo_with_policy: Path
    ) -> None:
        """Test that the hook outputs blocking JSON when a policy fires."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_policy)
        repo.index.add(["src/main.py"])

        # Run the stop hook
        script_path = shell_scripts_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_policy)

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
        self, shell_scripts_dir: Path, git_repo_with_policy: Path
    ) -> None:
        """Test that the hook outputs empty JSON when no policy fires."""
        # Don't create any files that would trigger the policy
        # (policy triggers on src/** but we haven't created anything in src/)

        # Run the stop hook
        script_path = shell_scripts_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_policy)

        # Parse the output as JSON
        output = stdout.strip()
        assert output, f"Expected JSON output but got empty string. stderr: {stderr}"

        try:
            result = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {output!r}. Error: {e}")

        # Should be empty JSON (no blocking)
        assert result == {}, f"Expected empty JSON when no policies fire, got: {result}"

    def test_exits_early_when_no_policy_file(
        self, shell_scripts_dir: Path, git_repo_no_policy: Path
    ) -> None:
        """Test that the hook exits cleanly when no policy file exists."""
        script_path = shell_scripts_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_no_policy)

        # Should exit with code 0 and produce no output (or empty)
        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"
        # No output is fine when there's no policy file
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
        self, shell_scripts_dir: Path, git_repo_with_policy: Path
    ) -> None:
        """Test that promised policies are not re-triggered."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_policy)
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
            script_path = shell_scripts_dir / "policy_stop_hook.sh"
            hook_input = {"transcript_path": transcript_path}
            stdout, stderr, code = run_stop_hook(script_path, git_repo_with_policy, hook_input)

            # Parse the output
            output = stdout.strip()
            assert output, f"Expected JSON output. stderr: {stderr}"

            result = json.loads(output)

            # Should be empty JSON because the policy was promised
            assert result == {}, f"Expected empty JSON when policy is promised, got: {result}"
        finally:
            os.unlink(transcript_path)

    def test_safety_pattern_prevents_firing(self, shell_scripts_dir: Path, tmp_path: Path) -> None:
        """Test that safety patterns prevent policies from firing."""
        # Initialize git repo
        repo = Repo.init(tmp_path)

        readme = tmp_path / "README.md"
        readme.write_text("# Test Project\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create a policy with a safety pattern
        # Use compare_to: prompt since test repos don't have origin remote
        policy_file = tmp_path / ".deepwork.policy.yml"
        policy_file.write_text(
            """- name: "Documentation Policy"
  trigger: "src/**/*"
  safety: "docs/**/*"
  compare_to: prompt
  instructions: |
    Update documentation when changing source files.
"""
        )

        # Create .deepwork directory with empty baseline
        deepwork_dir = tmp_path / ".deepwork"
        deepwork_dir.mkdir(exist_ok=True)
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
        script_path = shell_scripts_dir / "policy_stop_hook.sh"
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
        self, shell_scripts_dir: Path, git_repo_with_policy: Path
    ) -> None:
        """Test that blocking JSON has the correct Claude Code structure."""
        # Create a file that triggers the policy
        src_dir = git_repo_with_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_policy)
        repo.index.add(["src/main.py"])

        script_path = shell_scripts_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_policy)

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
        self, shell_scripts_dir: Path, git_repo_with_policy: Path
    ) -> None:
        """Test that the reason includes the policy instructions."""
        src_dir = git_repo_with_policy / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_policy)
        repo.index.add(["src/main.py"])

        script_path = shell_scripts_dir / "policy_stop_hook.sh"
        stdout, stderr, code = run_stop_hook(script_path, git_repo_with_policy)

        result = json.loads(stdout.strip())

        # Check that the reason contains the policy content
        reason = result["reason"]
        assert "DeepWork Policies Triggered" in reason
        assert "Test Policy" in reason
        assert "test policy that fires" in reason
