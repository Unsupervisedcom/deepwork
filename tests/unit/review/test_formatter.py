"""Tests for output formatting (deepwork.review.formatter) — validates REVIEW-REQ-006."""

from pathlib import Path

from deepwork.review.config import ReviewTask
from deepwork.review.formatter import format_for_claude


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
        assert result.startswith("Invoke the following list of Tasks in parallel:")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_individual_task_name_includes_filename(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="py_review", files=["src/app.py"])
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert 'name: "py_review review of src/app.py"' in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_grouped_task_name_includes_file_count(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="py_review", files=["a.py", "b.py", "c.py"])
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert 'name: "py_review review of 3 files"' in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3b).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_subagent_type_when_no_agent(self, tmp_path: Path) -> None:
        task = _make_task(agent_name=None)
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "subagent_type: general-purpose" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3b).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_custom_subagent_type(self, tmp_path: Path) -> None:
        task = _make_task(agent_name="security-expert")
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert "subagent_type: security-expert" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3c).
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
        assert 'name: "rule_a review of a.py"' in result
        assert 'name: "rule_b review of b.py"' in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_scope_prefix_from_subdirectory_source(self, tmp_path: Path) -> None:
        """Rules from subdirectory .deepreview files include scope prefix in name."""
        task = _make_task(rule_name="job_definition_review", files=["job.yml"])
        task.source_location = "jobs/my_job/.deepreview:1"
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert 'name: "my_job/job_definition_review review of job.yml"' in result
        assert "description: Review my_job/job_definition_review" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_scope_prefix_for_root_level_source(self, tmp_path: Path) -> None:
        """Rules from the root .deepreview file have no scope prefix."""
        task = _make_task(rule_name="py_review", files=["app.py"])
        task.source_location = ".deepreview:5"
        file_path = tmp_path / "instructions.md"
        result = format_for_claude([(task, file_path)], tmp_path)
        assert 'name: "py_review review of app.py"' in result
        assert "description: Review py_review" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-006.3.3a, REVIEW-REQ-004.10).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_same_name_rules_disambiguated_by_scope(self, tmp_path: Path) -> None:
        """Same-named rules from different directories produce distinct names."""
        task_a = _make_task(rule_name="job_definition_review", files=["a/job.yml"])
        task_a.source_location = "jobs/job_a/.deepreview:1"
        task_b = _make_task(rule_name="job_definition_review", files=["b/job.yml"])
        task_b.source_location = "jobs/job_b/.deepreview:1"
        file_a = tmp_path / "a.md"
        file_b = tmp_path / "b.md"
        result = format_for_claude([(task_a, file_a), (task_b, file_b)], tmp_path)
        assert 'name: "job_a/job_definition_review review of a/job.yml"' in result
        assert 'name: "job_b/job_definition_review review of b/job.yml"' in result
