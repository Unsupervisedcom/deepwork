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


class TestRulesStopHookInfiniteLoopPrevention:
    """Tests for preventing infinite loops in rules stop hook."""

    def test_queued_prompt_rule_does_not_refire(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that a prompt rule with QUEUED status doesn't fire again.

        This prevents infinite loops when the transcript is unavailable or
        promise tags haven't been written yet.
        """
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # First run: rule should fire and create queue entry
        stdout1, stderr1, code1 = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)
        result1 = json.loads(stdout1.strip())
        assert result1.get("decision") == "block", f"First run should block: {result1}"
        assert "Test Rule" in result1.get("reason", "")

        # Second run: rule should NOT fire again (already QUEUED)
        # Note: No transcript with promise tag, but the queue entry prevents re-firing
        stdout2, stderr2, code2 = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)
        result2 = json.loads(stdout2.strip())
        assert result2 == {}, f"Second run should not block (rule already queued): {result2}"

    def test_rule_fires_again_after_queue_cleared(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that a rule fires again after the queue is cleared."""
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # First run: rule should fire
        stdout1, stderr1, code1 = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)
        result1 = json.loads(stdout1.strip())
        assert result1.get("decision") == "block"

        # Clear the queue
        queue_dir = git_repo_with_src_rule / ".deepwork" / "tmp" / "rules" / "queue"
        if queue_dir.exists():
            for f in queue_dir.glob("*.json"):
                f.unlink()

        # Third run: rule should fire again (queue cleared)
        stdout3, stderr3, code3 = run_stop_hook(git_repo_with_src_rule, src_dir=src_dir)
        result3 = json.loads(stdout3.strip())
        assert result3.get("decision") == "block", f"Rule should fire again: {result3}"

    def test_promise_tag_still_prevents_firing(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that promise tags still prevent rules from firing.

        Even with the queue-based fix, promise tags should work when
        the transcript is available.
        """
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # Create a transcript with promise tag (simulating agent response)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            transcript_path = f.name
            f.write(
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "<promise>Test Rule</promise>",
                                }
                            ]
                        },
                    }
                )
            )
            f.write("\n")

        try:
            # Run with transcript: rule should NOT fire (promise tag found)
            hook_input = {"transcript_path": transcript_path, "hook_event_name": "Stop"}
            stdout, stderr, code = run_stop_hook(
                git_repo_with_src_rule, hook_input, src_dir=src_dir
            )
            result = json.loads(stdout.strip())
            assert result == {}, f"Rule should not fire with promise tag: {result}"
        finally:
            os.unlink(transcript_path)


class TestSubagentStopEvent:
    """Tests for SubagentStop event triggering agentFinished rules."""

    def test_subagent_stop_event_triggers_rules(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that SubagentStop event triggers agentFinished rules.

        Claude Code has both Stop and SubagentStop events that should both
        trigger after_agent/agentFinished rules.
        """
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        # Stage the change
        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # Run with SubagentStop event
        hook_input = {"hook_event_name": "SubagentStop"}
        stdout, stderr, code = run_stop_hook(git_repo_with_src_rule, hook_input, src_dir=src_dir)

        # Parse the output
        output = stdout.strip()
        assert output, f"Expected JSON output. stderr: {stderr}"
        result = json.loads(output)

        # Should trigger the rule just like Stop event does
        assert result.get("decision") == "block", f"SubagentStop should trigger rules: {result}"
        assert "Test Rule" in result.get("reason", "")

    def test_both_stop_and_subagent_stop_trigger_same_rules(
        self, src_dir: Path, git_repo_with_src_rule: Path
    ) -> None:
        """Test that Stop and SubagentStop events trigger the same rules.

        Both events should fire agentFinished rules with identical behavior.
        """
        # Create a file that triggers the rule
        test_src_dir = git_repo_with_src_rule / "src"
        test_src_dir.mkdir(exist_ok=True)
        (test_src_dir / "main.py").write_text("# New file\n")

        repo = Repo(git_repo_with_src_rule)
        repo.index.add(["src/main.py"])

        # Test Stop event
        hook_input_stop = {"hook_event_name": "Stop"}
        stdout_stop, _, _ = run_stop_hook(git_repo_with_src_rule, hook_input_stop, src_dir=src_dir)
        result_stop = json.loads(stdout_stop.strip())

        # Clear the queue to allow the rule to fire again
        queue_dir = git_repo_with_src_rule / ".deepwork" / "tmp" / "rules" / "queue"
        if queue_dir.exists():
            for f in queue_dir.glob("*.json"):
                f.unlink()

        # Test SubagentStop event
        hook_input_subagent = {"hook_event_name": "SubagentStop"}
        stdout_subagent, _, _ = run_stop_hook(
            git_repo_with_src_rule, hook_input_subagent, src_dir=src_dir
        )
        result_subagent = json.loads(stdout_subagent.strip())

        # Both should produce the same blocking behavior
        assert result_stop.get("decision") == result_subagent.get("decision") == "block"
        assert "Test Rule" in result_stop.get("reason", "")
        assert "Test Rule" in result_subagent.get("reason", "")
