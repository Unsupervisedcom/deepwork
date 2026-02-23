"""Tests for deepreview configuration discovery (deepwork.review.discovery) — validates REQ-002."""

from pathlib import Path

from deepwork.review.discovery import find_deepreview_files, load_all_rules


def _write_deepreview(path: Path, content: str) -> Path:
    """Write a .deepreview file in the given directory."""
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / ".deepreview"
    filepath.write_text(content, encoding="utf-8")
    return filepath


VALID_CONFIG = """
my_rule:
  match:
    include: ["**/*.py"]
  review:
    strategy: individual
    instructions: "Review it."
"""


class TestFindDeepReviewFiles:
    """Tests for find_deepreview_files."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.1, REQ-002.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_finds_file_in_root(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        files = find_deepreview_files(tmp_path)
        assert len(files) == 1
        assert files[0] == tmp_path / ".deepreview"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_finds_files_in_subdirectories(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        _write_deepreview(tmp_path / "src", VALID_CONFIG)
        _write_deepreview(tmp_path / "src" / "lib", VALID_CONFIG)
        files = find_deepreview_files(tmp_path)
        assert len(files) == 3

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_deepest_first_ordering(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        _write_deepreview(tmp_path / "src", VALID_CONFIG)
        _write_deepreview(tmp_path / "src" / "lib", VALID_CONFIG)
        files = find_deepreview_files(tmp_path)
        # Deepest first
        assert files[0] == tmp_path / "src" / "lib" / ".deepreview"
        assert files[1] == tmp_path / "src" / ".deepreview"
        assert files[2] == tmp_path / ".deepreview"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_empty_when_none_found(self, tmp_path: Path) -> None:
        files = find_deepreview_files(tmp_path)
        assert files == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_git_directory(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".deepreview").write_text(VALID_CONFIG)
        files = find_deepreview_files(tmp_path)
        assert files == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_node_modules(self, tmp_path: Path) -> None:
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        (nm_dir / ".deepreview").write_text(VALID_CONFIG)
        _write_deepreview(tmp_path, VALID_CONFIG)
        files = find_deepreview_files(tmp_path)
        assert len(files) == 1
        assert files[0] == tmp_path / ".deepreview"


class TestLoadAllRules:
    """Tests for load_all_rules."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.3.1, REQ-002.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_loads_rules_from_single_file(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        rules, errors = load_all_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0].name == "my_rule"
        assert errors == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.3.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_rules_from_multiple_files_are_independent(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        _write_deepreview(
            tmp_path / "src",
            """
src_rule:
  match:
    include: ["**/*.ts"]
  review:
    strategy: matches_together
    instructions: "Review TS files."
""",
        )
        rules, errors = load_all_rules(tmp_path)
        assert len(rules) == 2
        names = {r.name for r in rules}
        assert names == {"my_rule", "src_rule"}
        assert errors == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_source_dir_set_correctly(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path / "src", VALID_CONFIG)
        rules, errors = load_all_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0].source_dir == tmp_path / "src"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-002.3.4, REQ-002.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_invalid_file_reports_error_without_blocking(self, tmp_path: Path) -> None:
        _write_deepreview(tmp_path, VALID_CONFIG)
        _write_deepreview(tmp_path / "bad", "invalid: [yaml")
        rules, errors = load_all_rules(tmp_path)
        assert len(rules) == 1  # Valid rule still loaded
        assert len(errors) == 1
        assert "bad" in str(errors[0].file_path)
