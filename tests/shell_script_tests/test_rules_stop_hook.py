"""Tests for the rules stop hook (deepwork.hooks.rules_check).

These tests verify that the rules stop hook correctly outputs JSON
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
def git_repo_with_src_rule(tmp_path: Path) -> Path:
    """Create a git repo with a v2 rule file that triggers on src/** changes."""
    repo = Repo.init(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create v2 rules directory and file
    rules_dir = tmp_path / ".deepwork" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Use compare_to: prompt since test repos don't have origin remote
    rule_file = rules_dir / "test-rule.md"
    rule_file.write_text(
        """---
name: Test Rule
trigger: "src/**/*"
compare_to: prompt
---
This is a test rule that fires when src/ files change.
Please address this rule.
"""
    )

    # Empty baseline means all current files are "new"
    deepwork_dir = tmp_path / ".deepwork"
    (deepwork_dir / ".last_work_tree").write_text("")

    return tmp_path


def run_stop_hook(
    cwd: Path,
    hook_input: dict | None = None,
    src_dir: Path | None = None,
) -> tuple[str, str, int]:
    """Run the rules_check module and return its output."""
    env = os.environ.copy()
    env["DEEPWORK_HOOK_PLATFORM"] = "claude"
    if src_dir:
        env["PYTHONPATH"] = str(src_dir)

    stdin_data = json.dumps(hook_input) if hook_input else ""

    result = subprocess.run(
        ["python", "-m", "deepwork.hooks.rules_check"],
        cwd=cwd,
        capture_output=True,
        text=True,
        input=stdin_data,
        env=env,
    )

    return result.stdout, result.stderr, result.returncode


class TestRulesStopHookBlocking:
    """Tests for rules stop hook blocking behavior."""

    def test_outputs_block_json_when_rule_fires(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that the hook outputs blocking JSON when a rule fires."""
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # Run the stop hook
        stdout, stderr, code = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)

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
        assert "Test Rule" in result["reason"], f"Rule name not in reason: {result}"

    def test_outputs_empty_json_when_no_rule_fires(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that the hook outputs empty JSON when no rule fires."""
        # Don't create any files that would trigger the rule
        # (rule triggers on src/** but we haven't created anything in src/)

        # Run the stop hook
        stdout, stderr, code = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)

        # Parse the output as JSON
        output = stdout.strip()
        assert output, f"Expected JSON output but got empty string. stderr: {stderr}"

        try:
            result = json.loads(output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {output!r}. Error: {e}")

        # Should be empty JSON (no blocking)
        assert result == {}, f"Expected empty JSON when no rules fire, got: {result}"

    def test_exits_early_when_no_rules_dir(self, src_dir: Path, git_repo: Path) -> None:
        """Test that the hook exits cleanly when no rules directory exists."""
        stdout, stderr, code = run_stop_hook(git_repo, src_dir=src_dir)

        # Should exit with code 0 and produce no output (or empty)
        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"
        # No output is fine when there's no rules directory
        output = stdout.strip()
        if output:
            # If there is output, it should be valid JSON
            try:
                result = json.loads(output)
                assert result == {}, f"Expected empty JSON, got: {result}"
            except json.JSONDecodeError:
                # Empty or no output is acceptable
                pass

    def test_respects_promise_tags(self, src_dir: Path, git_repo_with_src_rule: Path) -> None:
        """Test that promised rules are not re-triggered."""
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
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
                                    "text": "I've addressed the rule. <promise>Test Rule</promise>",
                                }
                            ]
                        },
                    }
                )
            )
            f.write("\n")

        try:
            # Run the stop hook with transcript path
            hook_input = {"transcript_path": transcript_path, "hook_event_name": "Stop"}
            stdout, stderr, code = run_stop_hook(
                git_repo_with_src_rule, hook_input, src_dir=src_dir
            )

            # Parse the output
            output = stdout.strip()
            assert output, f"Expected JSON output. stderr: {stderr}"

            result = json.loads(output)

            # Should be empty JSON because the rule was promised
            assert result == {}, f"Expected empty JSON when rule is promised, got: {result}"
        finally:
            os.unlink(transcript_path)

    def test_safety_pattern_prevents_firing(self, src_dir: Path, tmp_path: Path) -> None:
        """Test that safety patterns prevent rules from firing."""
        # Initialize git repo
        repo = Repo.init(tmp_path)

        readme = tmp_path / "README.md"
        readme.write_text("# Test Project\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create v2 rule with a safety pattern
        rules_dir = tmp_path / ".deepwork" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        rule_file = rules_dir / "documentation-rule.md"
        rule_file.write_text(
            """---
name: Documentation Rule
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
        test_src_dir = tmp_path / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# Source file\n")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        (docs_dir / "api.md").write_text("# API docs\n")

        # Stage both changes so they appear in git diff --cached
        repo.index.add(["src/main.py", "docs/api.md"])

        # Run the stop hook
        stdout, stderr, code = run_stop_hook(tmp_path, src_dir=src_dir)

        # Parse the output
        output = stdout.strip()
        assert output, f"Expected JSON output. stderr: {stderr}"

        result = json.loads(output)

        # Should be empty JSON because safety pattern matched
        assert result == {}, f"Expected empty JSON when safety pattern matches, got: {result}"


class TestRulesStopHookJsonFormat:
    """Tests for the JSON output format of the rules stop hook."""

    def test_json_has_correct_structure(self, src_dir: Path, git_repo_with_src_rule: Path) -> None:
        """Test that blocking JSON has the correct Claude Code structure."""
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        stdout, stderr, code = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)

        result = json.loads(stdout.strip())

        # Verify exact structure expected by Claude Code
        assert set(result.keys()) == {
            "decision",
            "reason",
        }, f"Unexpected keys in JSON: {result.keys()}"
        assert result["decision"] == "block"
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0

    def test_reason_contains_rule_instructions(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that the reason includes the rule instructions."""
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        stdout, stderr, code = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)

        result = json.loads(stdout.strip())

        # Check that the reason contains the rule content
        reason = result["reason"]
        assert "DeepWork Rules Triggered" in reason
        assert "Test Rule" in reason
        assert "test rule that fires" in reason
