"""Tests for output formatting (deepwork.review.formatter) — validates REVIEW-REQ-006."""

from pathlib import Path
from unittest.mock import patch

from deepwork.review.config import ReviewTask
from deepwork.review.formatter import _resolve_file_ref_root, format_for_claude


def _make_task(
    rule_name: str = "test_rule",
    files: list[str] | None = None,
    agent_name: str | None = None,
) -> ReviewTask:
    """Create a ReviewTask with sensible defaults."""
    return ReviewTask(
        rule_name=rule_name,
        files_to_review=files or ["src/app.py"],
        instructions="Review it.",
        agent_name=agent_name,
    )


class TestFormatForClaude:
    """Tests for format_for_claude."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_empty_tasks_returns_no_tasks_message(self, tmp_path: Path) -> None:
        result = format_for_claude([], tmp_path)
        assert "No review tasks" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_output_starts_with_invoke_line(self, tmp_path: Path) -> None:
        task = _make_task()
        file_path = tmp_path / ".deepwork" / "tmp" / "review_instructions" / "123.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("content")
        result = format_for_claude([(task, file_path)], tmp_path)
        assert result.startswith("Invoke the following list of Agents in parallel.")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3c).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_subagent_type_when_no_agent(self, tmp_path: Path) -> None:
        task = _make_task(agent_name=None)
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "subagent_type: deepwork:reviewer" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3c).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_custom_subagent_type(self, tmp_path: Path) -> None:
        task = _make_task(agent_name="security-expert")
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "subagent_type: security-expert" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3b).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_description_field_present(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="py_review")
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "description: Review py_review" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3c, REVIEW-REQ-006.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_prompt_references_instruction_file(self, tmp_path: Path) -> None:
        task = _make_task()
        file_path = tmp_path / ".deepwork" / "tmp" / "review_instructions" / "7142141.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("content")
        result = format_for_claude([(task, file_path)], tmp_path)
        assert 'prompt: "@.deepwork/tmp/review_instructions/7142141.md"' in result

    def test_multiple_tasks(self, tmp_path: Path) -> None:
        task_a = _make_task(rule_name="rule_a", files=["a.py"])
        task_b = _make_task(rule_name="rule_b", files=["b.py"])
        file_a = tmp_path / "a.md"
        file_b = tmp_path / "b.md"
        result = format_for_claude([(task_a, file_a), (task_b, file_b)], tmp_path)
        assert "description: Review rule_a" in result
        assert "description: Review rule_b" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_scope_prefix_from_subdirectory_source(self, tmp_path: Path) -> None:
        """Rules from subdirectory .deepreview files include scope prefix in description."""
        task = _make_task(rule_name="job_definition_review", files=["job.yml"])
        task.source_location = "jobs/my_job/.deepreview:1"
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "description: Review my_job/job_definition_review" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_scope_prefix_for_root_level_source(self, tmp_path: Path) -> None:
        """Rules from the root .deepreview file have no scope prefix."""
        task = _make_task(rule_name="py_review", files=["app.py"])
        task.source_location = ".deepreview:5"
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "description: Review py_review" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_same_name_rules_disambiguated_by_scope(self, tmp_path: Path) -> None:
        """Same-named rules from different directories produce distinct descriptions."""
        task_a = _make_task(rule_name="job_definition_review", files=["a/job.yml"])
        task_a.source_location = "jobs/job_a/.deepreview:1"
        task_b = _make_task(rule_name="job_definition_review", files=["b/job.yml"])
        task_b.source_location = "jobs/job_b/.deepreview:1"
        file_a = tmp_path / "a.md"
        file_b = tmp_path / "b.md"
        result = format_for_claude([(task_a, file_a), (task_b, file_b)], tmp_path)
        assert "description: Review job_a/job_definition_review" in result
        assert "description: Review job_b/job_definition_review" in result


class TestGitCommonDir:
    """Tests for _git_common_dir helper."""

    def test_returns_none_when_git_fails(self, tmp_path: Path) -> None:
        """Non-git directories return None."""
        from deepwork.review.formatter import _git_common_dir

        # tmp_path is not a git repo, so git rev-parse will fail
        result = _git_common_dir(tmp_path)
        assert result is None

    def test_returns_none_on_exception(self, tmp_path: Path) -> None:
        """Handles subprocess exceptions gracefully."""
        from deepwork.review.formatter import _git_common_dir

        with patch("deepwork.review.formatter.subprocess.run", side_effect=OSError("no git")):
            result = _git_common_dir(tmp_path)
        assert result is None

    def test_returns_none_on_empty_output(self, tmp_path: Path) -> None:
        """Returns None when git outputs an empty string."""
        from deepwork.review.formatter import _git_common_dir

        mock_result = type("Result", (), {"returncode": 0, "stdout": "\n"})()
        with patch("deepwork.review.formatter.subprocess.run", return_value=mock_result):
            result = _git_common_dir(tmp_path)
        assert result is None

    def test_returns_path_on_success(self, tmp_path: Path) -> None:
        """Returns Path when git succeeds."""
        from deepwork.review.formatter import _git_common_dir

        mock_result = type("Result", (), {"returncode": 0, "stdout": "/tmp/repo/.git\n"})()
        with patch("deepwork.review.formatter.subprocess.run", return_value=mock_result):
            result = _git_common_dir(tmp_path)
        assert result == Path("/tmp/repo/.git")


class TestResolveFileRefRoot:
    """Tests for _resolve_file_ref_root — validates REVIEW-REQ-006.3.5."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_normal_repo_returns_project_root(self, tmp_path: Path) -> None:
        """In a normal (non-worktree) repo, returns project_root unchanged."""
        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            # git-common-dir == git-dir means not a worktree
            mock_git.return_value = tmp_path / ".git"
            result = _resolve_file_ref_root(tmp_path)
        assert result == tmp_path

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_worktree_returns_main_repo_root(self, tmp_path: Path) -> None:
        """In a git worktree, returns the main repo root."""
        main_repo = tmp_path / "main_repo"
        main_repo.mkdir()
        worktree = main_repo / ".claude" / "worktrees" / "my-feature"
        worktree.mkdir(parents=True)

        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            # git-common-dir points to main repo's .git
            mock_git.return_value = main_repo / ".git"
            result = _resolve_file_ref_root(worktree)
        assert result == main_repo

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_non_git_directory_returns_project_root(self, tmp_path: Path) -> None:
        """Non-git directories fall back to project_root."""
        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            mock_git.return_value = None
            result = _resolve_file_ref_root(tmp_path)
        assert result == tmp_path


class TestFormatForClaudeWorktree:
    """Tests for worktree-aware path formatting — validates REVIEW-REQ-006.3.5."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_worktree_prompt_path_relative_to_main_root(self, tmp_path: Path) -> None:
        """In a worktree, @file paths are relative to the main repo root."""
        main_repo = tmp_path / "repo"
        main_repo.mkdir()
        worktree = main_repo / ".claude" / "worktrees" / "feat"
        instructions = worktree / ".deepwork" / "tmp" / "review_instructions"
        instructions.mkdir(parents=True)
        file_path = instructions / "review_123.md"
        file_path.write_text("content")

        task = _make_task()
        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            mock_git.return_value = main_repo / ".git"
            result = format_for_claude([(task, file_path)], worktree)

        expected = "@.claude/worktrees/feat/.deepwork/tmp/review_instructions/review_123.md"
        assert f'prompt: "{expected}"' in result

    def test_fallback_to_absolute_path_when_not_relative(self, tmp_path: Path) -> None:
        """When file_path is not under the ref root, uses the path as-is."""
        unrelated_path = Path("/some/other/place/review.md")
        task = _make_task()
        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            mock_git.return_value = tmp_path / ".git"
            result = format_for_claude([(task, unrelated_path)], tmp_path)
        assert f'prompt: "@{unrelated_path}"' in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_normal_repo_prompt_path_relative_to_project_root(self, tmp_path: Path) -> None:
        """In a normal repo, @file paths are relative to project_root as before."""
        file_path = tmp_path / ".deepwork" / "tmp" / "review_instructions" / "review_123.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("content")

        task = _make_task()
        with patch("deepwork.review.formatter._git_common_dir") as mock_git:
            mock_git.return_value = tmp_path / ".git"
            result = format_for_claude([(task, file_path)], tmp_path)

        assert 'prompt: "@.deepwork/tmp/review_instructions/review_123.md"' in result
