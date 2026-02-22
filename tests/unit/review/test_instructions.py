"""Tests for review instruction file generation (deepwork.review.instructions)."""

from pathlib import Path

from deepwork.review.config import ReviewTask
from deepwork.review.instructions import (
    build_instruction_file,
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
    )


class TestBuildInstructionFile:
    """Tests for build_instruction_file."""

    # REQ-005.1.2
    def test_includes_rule_name_in_header(self) -> None:
        task = _make_task(rule_name="python_review")
        content = build_instruction_file(task)
        assert "# Review: python_review" in content

    # REQ-005.1.3
    def test_includes_review_instructions(self) -> None:
        task = _make_task(instructions="Check for security issues.")
        content = build_instruction_file(task)
        assert "## Review Instructions" in content
        assert "Check for security issues." in content

    # REQ-005.1.4, REQ-005.2.1
    def test_includes_files_to_review_with_at_prefix(self) -> None:
        task = _make_task(files=["src/app.py", "src/lib.py"])
        content = build_instruction_file(task)
        assert "## Files to Review" in content
        assert "- @src/app.py" in content
        assert "- @src/lib.py" in content

    # REQ-005.1.6, REQ-005.2.2
    def test_includes_unchanged_matching_files(self) -> None:
        task = _make_task(additional_files=["src/unchanged.py"])
        content = build_instruction_file(task)
        assert "## Unchanged Matching Files" in content
        assert "- @src/unchanged.py" in content

    # REQ-005.1.7, REQ-005.2.3
    def test_includes_all_changed_filenames_without_at_prefix(self) -> None:
        task = _make_task(
            all_changed_filenames=["src/app.py", "tests/test.py", "README.md"]
        )
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
                assert not line.startswith("- @"), f"Context-only files should not have @ prefix: {line}"

    def test_omits_unchanged_section_when_empty(self) -> None:
        task = _make_task(additional_files=[])
        content = build_instruction_file(task)
        assert "## Unchanged Matching Files" not in content

    def test_omits_all_changed_section_when_none(self) -> None:
        task = _make_task(all_changed_filenames=None)
        content = build_instruction_file(task)
        assert "## All Changed Files" not in content

    def test_single_file_scope_description(self) -> None:
        task = _make_task(files=["src/app.py"])
        content = build_instruction_file(task)
        assert "src/app.py" in content.split("\n")[0]

    def test_multi_file_scope_description(self) -> None:
        task = _make_task(files=["a.py", "b.py", "c.py"])
        content = build_instruction_file(task)
        assert "3 files" in content.split("\n")[0]

    # REQ-005.6.1, REQ-005.6.2
    def test_includes_traceability_blurb(self) -> None:
        task = _make_task(source_location="src/.deepreview:5")
        content = build_instruction_file(task)
        assert "This review was requested by the policy at `src/.deepreview:5`." in content

    # REQ-005.6.3
    def test_traceability_preceded_by_horizontal_rule(self) -> None:
        task = _make_task(source_location="src/.deepreview:5")
        content = build_instruction_file(task)
        lines = content.strip().split("\n")
        # Find the traceability line
        trace_idx = next(
            i for i, l in enumerate(lines) if "This review was requested" in l
        )
        # The line two above should be the horizontal rule (blank line between)
        assert "---" in lines[trace_idx - 2]

    # REQ-005.6.4
    def test_omits_traceability_when_source_location_empty(self) -> None:
        task = _make_task(source_location="")
        content = build_instruction_file(task)
        assert "This review was requested" not in content

    def test_traceability_is_at_end(self) -> None:
        task = _make_task(source_location=".deepreview:1")
        content = build_instruction_file(task)
        last_nonblank = [l for l in content.strip().split("\n") if l.strip()][-1]
        assert "This review was requested" in last_nonblank


class TestWriteInstructionFiles:
    """Tests for write_instruction_files."""

    # REQ-005.3.1, REQ-005.3.2
    def test_creates_instruction_files(self, tmp_path: Path) -> None:
        tasks = [_make_task(rule_name="rule_a"), _make_task(rule_name="rule_b")]
        results = write_instruction_files(tasks, tmp_path)
        assert len(results) == 2

        for task, file_path in results:
            assert file_path.exists()
            assert file_path.suffix == ".md"
            assert ".deepwork/tmp/review_instructions" in str(file_path)

    # REQ-005.3.4
    def test_unique_filenames(self, tmp_path: Path) -> None:
        tasks = [_make_task() for _ in range(10)]
        results = write_instruction_files(tasks, tmp_path)
        paths = [r[1] for r in results]
        assert len(set(paths)) == 10  # All unique

    # REQ-005.5.1
    def test_clears_previous_files(self, tmp_path: Path) -> None:
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / "old_file.md").write_text("stale")

        tasks = [_make_task()]
        write_instruction_files(tasks, tmp_path)

        # Old file should be gone
        assert not (instructions_dir / "old_file.md").exists()
        # New file should exist
        files = list(instructions_dir.iterdir())
        assert len(files) == 1

    # REQ-005.3.6
    def test_returns_task_path_tuples(self, tmp_path: Path) -> None:
        task = _make_task(rule_name="my_rule")
        results = write_instruction_files([task], tmp_path)
        assert len(results) == 1
        assert results[0][0] is task
        assert results[0][1].exists()
