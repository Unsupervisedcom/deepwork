"""Tests for review instruction file generation (deepwork.review.instructions).

Validates requirements: REVIEW-REQ-005, REVIEW-REQ-005.1, REVIEW-REQ-005.2,
REVIEW-REQ-005.3, REVIEW-REQ-005.4, REVIEW-REQ-005.5, REVIEW-REQ-005.6,
REVIEW-REQ-009, REVIEW-REQ-009.4, REVIEW-REQ-009.5.
"""

from pathlib import Path
from unittest.mock import patch

from deepwork.review.config import ReferenceFile, ReviewTask
from deepwork.review.instructions import (
    MAX_INLINE_FILES,
    MAX_INLINE_TOTAL_BYTES,
    _run_precompute_command,
    _run_precompute_commands,
    build_instruction_file,
    compute_review_id,
    short_instruction_filename,
    write_instruction_files,
)


def _make_task(
    rule_name: str = "test_rule",
    files: list[str] | None = None,
    instructions: str = "Review this.",
    agent_name: str | None = None,
    source_location: str = ".deepreview:1",
    additional_files: list[str] | None = None,
    all_changed_filenames: list[str] | None = None,
    precomputed_info_bash_command: str | None = None,
) -> ReviewTask:
    """Create a ReviewTask with sensible defaults."""
    return ReviewTask(
        rule_name=rule_name,
        files_to_review=files or ["src/app.py"],
        instructions=instructions,
        agent_name=agent_name,
        source_location=source_location,
        additional_files=additional_files or [],
        all_changed_filenames=all_changed_filenames,
        precomputed_info_bash_command=precomputed_info_bash_command,
    )


class TestBuildInstructionFile:
    """Tests for build_instruction_file."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_rule_name_in_header(self) -> None:
        task = _make_task(rule_name="python_review")
        content = build_instruction_file(task)
        assert "# Review: python_review" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_review_instructions(self) -> None:
        task = _make_task(instructions="Check for security issues.")
        content = build_instruction_file(task)
        assert "## Review Instructions" in content
        assert "Check for security issues." in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.4, REVIEW-REQ-005.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_files_to_review_with_at_prefix(self) -> None:
        task = _make_task(files=["src/app.py", "src/lib.py"])
        content = build_instruction_file(task)
        assert "## Files to Review" in content
        assert "- @src/app.py" in content
        assert "- @src/lib.py" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.6, REVIEW-REQ-005.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_unchanged_matching_files(self) -> None:
        task = _make_task(additional_files=["src/unchanged.py"])
        content = build_instruction_file(task)
        assert "## Unchanged Matching Files" in content
        assert "- @src/unchanged.py" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.7, REVIEW-REQ-005.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_all_changed_filenames_without_at_prefix(self) -> None:
        task = _make_task(all_changed_filenames=["src/app.py", "tests/test.py", "README.md"])
        content = build_instruction_file(task)
        assert "## All Changed Files" in content
        assert "- src/app.py" in content
        assert "- README.md" in content
        # Should NOT have @ prefix for context-only files
        lines = content.split("\n")
        all_changed_section = False
        for line in lines:
            if "## All Changed Files" in line:
                all_changed_section = True
            elif line.startswith("##"):
                all_changed_section = False
            if all_changed_section and line.startswith("- "):
                assert not line.startswith("- @"), (
                    f"Context-only files should not have @ prefix: {line}"
                )

    def test_omits_unchanged_section_when_empty(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        task = _make_task(additional_files=[])
        content = build_instruction_file(task)
        assert "## Unchanged Matching Files" not in content

    def test_omits_all_changed_section_when_none(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        task = _make_task(all_changed_filenames=None)
        content = build_instruction_file(task)
        assert "## All Changed Files" not in content

    def test_single_file_scope_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        task = _make_task(files=["src/app.py"])
        content = build_instruction_file(task)
        assert "src/app.py" in content.split("\n")[0]

    def test_multi_file_scope_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        task = _make_task(files=["a.py", "b.py", "c.py"])
        content = build_instruction_file(task)
        assert "3 files" in content.split("\n")[0]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.6.1, REVIEW-REQ-005.6.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_traceability_blurb(self) -> None:
        task = _make_task(source_location="src/.deepreview:5")
        content = build_instruction_file(task)
        assert "This review was requested by the policy at `src/.deepreview:5`." in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_traceability_preceded_by_horizontal_rule(self) -> None:
        task = _make_task(source_location="src/.deepreview:5")
        content = build_instruction_file(task)
        lines = content.strip().split("\n")
        # Find the traceability line
        trace_idx = next(i for i, line in enumerate(lines) if "This review was requested" in line)
        # The line two above should be the horizontal rule (blank line between)
        assert "---" in lines[trace_idx - 2]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.6.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_omits_traceability_when_source_location_empty(self) -> None:
        task = _make_task(source_location="")
        content = build_instruction_file(task)
        assert "This review was requested" not in content

    def test_traceability_is_at_end(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.6.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        task = _make_task(source_location=".deepreview:1")
        content = build_instruction_file(task)
        last_nonblank = [line for line in content.strip().split("\n") if line.strip()][-1]
        assert "This review was requested" in last_nonblank

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.4.1, REVIEW-REQ-009.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_after_review_section(self) -> None:
        task = _make_task()
        review_id = "test_rule--src-app.py--abc123def456"
        content = build_instruction_file(task, review_id)
        assert "## After Review" in content
        assert "mark_review_as_passed" in content
        assert review_id in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_after_review_section_before_traceability(self) -> None:
        task = _make_task(source_location="src/.deepreview:5")
        review_id = "test_rule--src-app.py--abc123def456"
        content = build_instruction_file(task, review_id)
        after_idx = content.index("## After Review")
        trace_idx = content.index("This review was requested")
        assert after_idx < trace_idx


class TestWriteInstructionFiles:
    """Tests for write_instruction_files."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.3.1, REVIEW-REQ-005.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_instruction_files(self, tmp_path: Path) -> None:
        tasks = [_make_task(rule_name="rule_a"), _make_task(rule_name="rule_b")]
        results = write_instruction_files(tasks, tmp_path)
        assert len(results) == 2

        for _task, file_path in results:
            assert file_path.exists()
            assert file_path.suffix == ".md"
            assert ".deepwork/tmp/review_instructions" in str(file_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.3.4, REVIEW-REQ-009.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_unique_filenames(self, tmp_path: Path) -> None:
        tasks = [_make_task(rule_name=f"rule_{i}") for i in range(10)]
        results = write_instruction_files(tasks, tmp_path)
        paths = [r[1] for r in results]
        assert len(set(paths)) == 10  # All unique

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.5.1, REVIEW-REQ-009.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_clears_previous_files(self, tmp_path: Path) -> None:
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / "old_file.md").write_text("stale")

        tasks = [_make_task()]
        write_instruction_files(tasks, tmp_path)

        # Old file should be gone
        assert not (instructions_dir / "old_file.md").exists()
        # New file should exist
        md_files = [f for f in instructions_dir.iterdir() if f.suffix == ".md"]
        assert len(md_files) == 1

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.3.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_task_path_tuples(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="my_rule")
        results = write_instruction_files([task], tmp_path)
        assert len(results) == 1
        assert results[0][0] is task
        assert results[0][1].exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_uses_review_id_based_filenames(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="lint_check", files=["src/app.py"])
        results = write_instruction_files([task], tmp_path)
        assert len(results) == 1
        filename = results[0][1].name
        assert filename.startswith("lint_check--")
        assert filename.endswith(".md")
        # Should contain the path component and hash
        assert "--src-app.py--" in filename

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.3.1, REVIEW-REQ-009.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_tasks_with_passed_marker(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="my_rule")
        review_id = compute_review_id(task, tmp_path)

        # Create .passed marker
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / f"{review_id}.passed").write_bytes(b"")

        results = write_instruction_files([task], tmp_path)
        assert results == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.5.1, REVIEW-REQ-009.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_preserves_passed_files_on_cleanup(self, tmp_path: Path) -> None:
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        passed_file = instructions_dir / "some_review.passed"
        passed_file.write_bytes(b"")

        write_instruction_files([_make_task()], tmp_path)

        assert passed_file.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.5.1, REVIEW-REQ-009.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_preserves_md_files_with_passed_marker(self, tmp_path: Path) -> None:
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / "old_review.md").write_text("passed content")
        (instructions_dir / "old_review.passed").write_bytes(b"")

        write_instruction_files([_make_task()], tmp_path)

        assert (instructions_dir / "old_review.md").exists()
        assert (instructions_dir / "old_review.passed").exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_all_tasks_passed_returns_empty(self, tmp_path: Path) -> None:
        tasks = [_make_task(rule_name="rule_a"), _make_task(rule_name="rule_b")]
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)

        for task in tasks:
            review_id = compute_review_id(task, tmp_path)
            (instructions_dir / f"{review_id}.passed").write_bytes(b"")

        results = write_instruction_files(tasks, tmp_path)
        assert results == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.3.1, REVIEW-REQ-009.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_some_tasks_passed_returns_remaining(self, tmp_path: Path) -> None:
        task_a = _make_task(rule_name="rule_a")
        task_b = _make_task(rule_name="rule_b")

        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)

        # Only mark task_a as passed
        review_id_a = compute_review_id(task_a, tmp_path)
        (instructions_dir / f"{review_id_a}.passed").write_bytes(b"")

        results = write_instruction_files([task_a, task_b], tmp_path)
        assert len(results) == 1
        assert results[0][0] is task_b


class TestComputeReviewId:
    """Tests for compute_review_id — validates REVIEW-REQ-009.1."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_single_file_produces_expected_format(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "app.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("print('hello')")

        task = _make_task(rule_name="python_review", files=["src/app.py"])
        review_id = compute_review_id(task, tmp_path)

        parts = review_id.split("--")
        assert len(parts) == 3
        assert parts[0] == "python_review"
        assert parts[1] == "src-app.py"
        assert len(parts[2]) == 12  # 12-char hex hash

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_deterministic_for_same_content(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("same content")

        task = _make_task(rule_name="rule", files=["src/app.py"])
        id1 = compute_review_id(task, tmp_path)
        id2 = compute_review_id(task, tmp_path)
        assert id1 == id2

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_different_content_produces_different_id(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)

        task = _make_task(rule_name="rule", files=["src/app.py"])

        (tmp_path / "src" / "app.py").write_text("version 1")
        id1 = compute_review_id(task, tmp_path)

        (tmp_path / "src" / "app.py").write_text("version 2")
        id2 = compute_review_id(task, tmp_path)

        assert id1 != id2

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_different_rule_produces_different_id(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("content")

        task_a = _make_task(rule_name="rule_a", files=["src/app.py"])
        task_b = _make_task(rule_name="rule_b", files=["src/app.py"])

        assert compute_review_id(task_a, tmp_path) != compute_review_id(task_b, tmp_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_slashes_replaced_with_dashes(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "app").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app" / "main.py").write_text("content")

        task = _make_task(rule_name="rule", files=["src/app/main.py"])
        review_id = compute_review_id(task, tmp_path)

        assert "src-app-main.py" in review_id

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_multiple_files_sorted_before_hashing(self, tmp_path: Path) -> None:
        (tmp_path / "b.py").write_text("b content")
        (tmp_path / "a.py").write_text("a content")

        task1 = _make_task(rule_name="rule", files=["a.py", "b.py"])
        task2 = _make_task(rule_name="rule", files=["b.py", "a.py"])

        assert compute_review_id(task1, tmp_path) == compute_review_id(task2, tmp_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_many_files_uses_count_summary(self, tmp_path: Path) -> None:
        # Create enough files that the joined paths exceed 100 chars
        files = [f"src/very/long/path/to/module_{i}/implementation.py" for i in range(5)]
        for f in files:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"content {f}")

        task = _make_task(rule_name="rule", files=files)
        review_id = compute_review_id(task, tmp_path)

        assert "5_files" in review_id

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_file_uses_placeholder(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="rule", files=["nonexistent.py"])
        # Should not raise — uses MISSING placeholder
        review_id = compute_review_id(task, tmp_path)
        assert len(review_id.split("--")) == 3

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_special_chars_in_rule_name_sanitized(self, tmp_path: Path) -> None:
        from deepwork.review.instructions import _sanitize_for_id

        assert _sanitize_for_id("my rule@v2!") == "my-rule-v2-"
        # Also verify it preserves allowed chars: alphanumeric, dash, underscore, dot
        assert _sanitize_for_id("rule_name-1.0") == "rule_name-1.0"


class TestInlineContent:
    """Tests for inline-content review tasks — validates REVIEW-REQ-005.1.8 and REVIEW-REQ-009.1.7.

    Inline-content tasks are used for type: string step outputs (see JOBS-REQ-004.8).
    They have no files_to_review and carry the value to review on inline_content.
    """

    def _make_inline_task(self, content: str, rule_name: str = "string_rule") -> ReviewTask:
        return ReviewTask(
            rule_name=rule_name,
            files_to_review=[],
            instructions="Review the inline content.",
            agent_name=None,
            source_location=".deepreview:1",
            inline_content=content,
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_includes_content_to_review_section(self) -> None:
        task = self._make_inline_task("hello world")
        content = build_instruction_file(task)
        assert "## Content to Review" in content
        assert "hello world" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_omits_files_to_review_section_when_no_files(self) -> None:
        task = self._make_inline_task("a value")
        content = build_instruction_file(task)
        assert "## Files to Review" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.1.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_scope_heading_is_inline_content(self) -> None:
        task = self._make_inline_task("anything")
        content = build_instruction_file(task)
        assert "# Review: string_rule — inline content" in content.split("\n")[0]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_review_id_uses_inline_marker(self, tmp_path: Path) -> None:
        task = self._make_inline_task("value a")
        review_id = compute_review_id(task, tmp_path)
        parts = review_id.split("--")
        assert len(parts) == 3
        assert parts[0] == "string_rule"
        assert parts[1] == "inline"
        assert len(parts[2]) == 12

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_distinct_inline_values_produce_distinct_ids(self, tmp_path: Path) -> None:
        task_a = self._make_inline_task("value a")
        task_b = self._make_inline_task("value b")
        assert compute_review_id(task_a, tmp_path) != compute_review_id(task_b, tmp_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-009.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_same_inline_value_produces_same_id(self, tmp_path: Path) -> None:
        task_a = self._make_inline_task("same value")
        task_b = self._make_inline_task("same value")
        assert compute_review_id(task_a, tmp_path) == compute_review_id(task_b, tmp_path)

    def test_pass_caching_works_for_inline_content(self, tmp_path: Path) -> None:
        """Writing a .passed marker for an inline task skips it next time."""
        task = self._make_inline_task("cache me")
        review_id = compute_review_id(task, tmp_path)
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / f"{review_id}.passed").write_bytes(b"")

        results = write_instruction_files([task], tmp_path)
        assert results == []

    def test_short_instruction_filename_is_stable(self, tmp_path: Path) -> None:
        review_id = "rule--src-app.py--abc123def456"
        assert short_instruction_filename(review_id) == short_instruction_filename(review_id)
        assert short_instruction_filename(review_id).startswith("r-")
        assert short_instruction_filename(review_id).endswith(".txt")


class TestPrecomputedContext:
    """Tests for precomputed info command execution — validates REVIEW-REQ-001.9, REVIEW-REQ-005.7."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.1, REVIEW-REQ-005.7.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_run_precompute_command_captures_stdout(self, tmp_path: Path) -> None:
        script = tmp_path / "info.sh"
        script.write_text("#!/usr/bin/env bash\necho 'hello world'")
        script.chmod(0o755)
        result = _run_precompute_command(str(script), tmp_path)
        assert "hello world" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_run_precompute_command_failure_returns_error(self, tmp_path: Path) -> None:
        script = tmp_path / "fail.sh"
        script.write_text("#!/usr/bin/env bash\necho 'oops' >&2\nexit 1")
        script.chmod(0o755)
        result = _run_precompute_command(str(script), tmp_path)
        assert "Precompute command failed" in result
        assert "exit code 1" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.4, REVIEW-REQ-001.9.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_run_precompute_command_timeout(self, tmp_path: Path) -> None:
        script = tmp_path / "slow.sh"
        script.write_text("#!/usr/bin/env bash\nsleep 120")
        script.chmod(0o755)
        with patch("deepwork.review.instructions.PRECOMPUTE_TIMEOUT_SECONDS", 1):
            result = _run_precompute_command(str(script), tmp_path)
        assert "timed out" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_run_precompute_command_uses_project_root_as_cwd(self, tmp_path: Path) -> None:
        script = tmp_path / "cwd.sh"
        script.write_text("#!/usr/bin/env bash\npwd")
        script.chmod(0o755)
        result = _run_precompute_command(str(script), tmp_path)
        assert str(tmp_path) in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.6, REVIEW-REQ-001.9.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_run_precompute_commands_deduplicates_and_parallelizes(self, tmp_path: Path) -> None:
        script = tmp_path / "echo.sh"
        script.write_text("#!/usr/bin/env bash\necho 'output'")
        script.chmod(0o755)
        commands = {str(script)}
        results = _run_precompute_commands(commands, tmp_path)
        assert str(script) in results
        assert "output" in results[str(script)]

    def test_run_precompute_commands_empty_set(self, tmp_path: Path) -> None:
        results = _run_precompute_commands(set(), tmp_path)
        assert results == {}

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.7.1, REVIEW-REQ-005.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_build_instruction_file_includes_precomputed_section(self) -> None:
        task = _make_task()
        content = build_instruction_file(task, "review-id", precomputed_info="# Data\nsome info")
        assert "## Precomputed Context" in content
        assert "# Data\nsome info" in content
        # Must be the last content section, after files and before After Review
        files_idx = content.index("## Files to Review")
        precomputed_idx = content.index("## Precomputed Context")
        after_review_idx = content.index("## After Review")
        assert files_idx < precomputed_idx < after_review_idx

    def test_build_instruction_file_omits_precomputed_when_none(self) -> None:
        task = _make_task()
        content = build_instruction_file(task, "review-id")
        assert "## Precomputed Context" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_build_instruction_file_includes_error_on_failure(self) -> None:
        task = _make_task()
        error_msg = "**Precompute command failed** (exit code 1):\n```\noops\n```"
        content = build_instruction_file(task, "review-id", precomputed_info=error_msg)
        assert "## Precomputed Context" in content
        assert "Precompute command failed" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-001.9.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_write_instruction_files_runs_precompute(self, tmp_path: Path) -> None:
        script = tmp_path / "info.sh"
        script.write_text("#!/usr/bin/env bash\necho 'precomputed data'")
        script.chmod(0o755)
        task = _make_task(precomputed_info_bash_command=str(script))
        results = write_instruction_files([task], tmp_path)
        assert len(results) == 1
        content = results[0][1].read_text()
        assert "## Precomputed Context" in content
        assert "precomputed data" in content


class TestReferenceFileInlining:
    """Tests for reference_files inlining in build_instruction_file."""

    def _task_with_refs(self, refs: list[ReferenceFile]) -> ReviewTask:
        return ReviewTask(
            rule_name="r",
            files_to_review=["src/app.py"],
            instructions="Review.",
            agent_name=None,
            source_location="",
            reference_files=refs,
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_empty_reference_files_no_section(self) -> None:
        task = _make_task()
        content = build_instruction_file(task)
        assert "## Reference Materials" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.8.2, REVIEW-REQ-005.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_inlines_content_with_description(self, tmp_path: Path) -> None:
        f = tmp_path / "example.yml"
        f.write_text("key: value\n")
        task = self._task_with_refs(
            [ReferenceFile(path=f, relative_label="example.yml", description="Sample YAML")]
        )
        content = build_instruction_file(task)
        assert "## Reference Materials" in content
        assert "### example.yml" in content
        assert "Sample YAML" in content
        assert "```yaml" in content
        assert "key: value" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.8.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_count_cap_triggers_omission(self, tmp_path: Path) -> None:
        refs: list[ReferenceFile] = []
        for i in range(MAX_INLINE_FILES + 3):
            f = tmp_path / f"f{i}.txt"
            f.write_text(f"content {i}")
            refs.append(ReferenceFile(path=f, relative_label=f"f{i}.txt"))
        task = self._task_with_refs(refs)
        content = build_instruction_file(task)
        assert "omitted due to size/count caps" in content
        assert "f20.txt" in content  # one of the omitted
        assert content.count("```") >= 2 * MAX_INLINE_FILES

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.8.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_byte_cap_triggers_omission(self, tmp_path: Path) -> None:
        big = tmp_path / "big.txt"
        big.write_text("a" * (MAX_INLINE_TOTAL_BYTES + 100))
        other = tmp_path / "other.txt"
        other.write_text("should be omitted")
        task = self._task_with_refs(
            [
                ReferenceFile(path=big, relative_label="big.txt"),
                ReferenceFile(path=other, relative_label="other.txt"),
            ]
        )
        content = build_instruction_file(task)
        assert "truncated" in content or "omitted due to size/count caps" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-005.8.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_file_graceful(self, tmp_path: Path) -> None:
        task = self._task_with_refs(
            [ReferenceFile(path=tmp_path / "nope.txt", relative_label="nope.txt")]
        )
        content = build_instruction_file(task)
        assert "could not inline nope.txt" in content
        # Section still rendered; other content not aborted.
        assert "## Reference Materials" in content
