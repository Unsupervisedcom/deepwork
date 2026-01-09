"""Tests for filesystem utilities."""

from pathlib import Path

import pytest

from deepwork.utils.fs import copy_dir, ensure_dir, find_files, safe_read, safe_write


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_creates_new_directory(self, temp_dir: Path) -> None:
        """Test that ensure_dir creates a new directory."""
        new_dir = temp_dir / "new_directory"
        assert not new_dir.exists()

        result = ensure_dir(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_creates_nested_directories(self, temp_dir: Path) -> None:
        """Test that ensure_dir creates nested directories."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        result = ensure_dir(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert result == nested_dir

    def test_handles_existing_directory(self, temp_dir: Path) -> None:
        """Test that ensure_dir works with existing directories."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        result = ensure_dir(existing_dir)

        assert existing_dir.exists()
        assert result == existing_dir

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that ensure_dir accepts string paths."""
        new_dir = temp_dir / "string_path"
        result = ensure_dir(str(new_dir))

        assert new_dir.exists()
        assert isinstance(result, Path)


class TestSafeWrite:
    """Tests for safe_write function."""

    def test_writes_content_to_file(self, temp_dir: Path) -> None:
        """Test that safe_write writes content to a file."""
        file_path = temp_dir / "test.txt"
        content = "Hello, World!"

        safe_write(file_path, content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_creates_parent_directories(self, temp_dir: Path) -> None:
        """Test that safe_write creates parent directories."""
        file_path = temp_dir / "nested" / "path" / "file.txt"
        content = "Nested content"

        safe_write(file_path, content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_overwrites_existing_file(self, temp_dir: Path) -> None:
        """Test that safe_write overwrites existing files."""
        file_path = temp_dir / "overwrite.txt"
        file_path.write_text("Old content")

        new_content = "New content"
        safe_write(file_path, new_content)

        assert file_path.read_text() == new_content

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that safe_write accepts string paths."""
        file_path = temp_dir / "string_path.txt"
        safe_write(str(file_path), "Content")

        assert file_path.exists()


class TestSafeRead:
    """Tests for safe_read function."""

    def test_reads_existing_file(self, temp_dir: Path) -> None:
        """Test that safe_read reads content from existing file."""
        file_path = temp_dir / "test.txt"
        content = "File content"
        file_path.write_text(content)

        result = safe_read(file_path)

        assert result == content

    def test_returns_none_for_missing_file(self, temp_dir: Path) -> None:
        """Test that safe_read returns None for missing files."""
        file_path = temp_dir / "nonexistent.txt"

        result = safe_read(file_path)

        assert result is None

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that safe_read accepts string paths."""
        file_path = temp_dir / "string_path.txt"
        content = "Content"
        file_path.write_text(content)

        result = safe_read(str(file_path))

        assert result == content

    def test_reads_unicode_content(self, temp_dir: Path) -> None:
        """Test that safe_read handles unicode content."""
        file_path = temp_dir / "unicode.txt"
        content = "Hello 世界 🌍"
        file_path.write_text(content, encoding="utf-8")

        result = safe_read(file_path)

        assert result == content


class TestCopyDir:
    """Tests for copy_dir function."""

    def test_copies_directory(self, temp_dir: Path) -> None:
        """Test that copy_dir copies a directory."""
        src = temp_dir / "source"
        src.mkdir()
        (src / "file1.txt").write_text("Content 1")
        (src / "file2.txt").write_text("Content 2")

        dst = temp_dir / "destination"
        copy_dir(src, dst)

        assert dst.exists()
        assert (dst / "file1.txt").read_text() == "Content 1"
        assert (dst / "file2.txt").read_text() == "Content 2"

    def test_copies_nested_directories(self, temp_dir: Path) -> None:
        """Test that copy_dir copies nested directories."""
        src = temp_dir / "source"
        src.mkdir()
        nested = src / "nested" / "deep"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("Nested content")

        dst = temp_dir / "destination"
        copy_dir(src, dst)

        assert (dst / "nested" / "deep" / "file.txt").read_text() == "Nested content"

    def test_ignores_patterns(self, temp_dir: Path) -> None:
        """Test that copy_dir ignores specified patterns."""
        src = temp_dir / "source"
        src.mkdir()
        (src / "file.txt").write_text("Include")
        (src / "file.md").write_text("Include")
        (src / "ignore.log").write_text("Ignore")
        (src / "__pycache__").mkdir()
        (src / "__pycache__" / "cache.pyc").write_text("Ignore")

        dst = temp_dir / "destination"
        copy_dir(src, dst, ignore_patterns=["*.log", "__pycache__"])

        assert (dst / "file.txt").exists()
        assert (dst / "file.md").exists()
        assert not (dst / "ignore.log").exists()
        assert not (dst / "__pycache__").exists()

    def test_raises_for_missing_source(self, temp_dir: Path) -> None:
        """Test that copy_dir raises FileNotFoundError for missing source."""
        src = temp_dir / "nonexistent"
        dst = temp_dir / "destination"

        with pytest.raises(FileNotFoundError, match="Source directory does not exist"):
            copy_dir(src, dst)

    def test_raises_for_non_directory_source(self, temp_dir: Path) -> None:
        """Test that copy_dir raises NotADirectoryError for file source."""
        src = temp_dir / "file.txt"
        src.write_text("Not a directory")
        dst = temp_dir / "destination"

        with pytest.raises(NotADirectoryError, match="Source is not a directory"):
            copy_dir(src, dst)


class TestFindFiles:
    """Tests for find_files function."""

    def test_finds_files_with_simple_pattern(self, temp_dir: Path) -> None:
        """Test that find_files finds files with simple pattern."""
        (temp_dir / "file1.txt").write_text("Content")
        (temp_dir / "file2.txt").write_text("Content")
        (temp_dir / "file.md").write_text("Content")

        results = find_files(temp_dir, "*.txt")

        assert len(results) == 2
        assert temp_dir / "file1.txt" in results
        assert temp_dir / "file2.txt" in results

    def test_finds_files_with_recursive_pattern(self, temp_dir: Path) -> None:
        """Test that find_files finds files recursively."""
        (temp_dir / "file.txt").write_text("Content")
        nested = temp_dir / "nested"
        nested.mkdir()
        (nested / "file.txt").write_text("Content")
        deep = nested / "deep"
        deep.mkdir()
        (deep / "file.txt").write_text("Content")

        results = find_files(temp_dir, "**/*.txt")

        assert len(results) == 3

    def test_returns_sorted_results(self, temp_dir: Path) -> None:
        """Test that find_files returns sorted results."""
        (temp_dir / "c.txt").write_text("Content")
        (temp_dir / "a.txt").write_text("Content")
        (temp_dir / "b.txt").write_text("Content")

        results = find_files(temp_dir, "*.txt")

        assert results[0].name == "a.txt"
        assert results[1].name == "b.txt"
        assert results[2].name == "c.txt"

    def test_returns_empty_list_for_no_matches(self, temp_dir: Path) -> None:
        """Test that find_files returns empty list when no matches."""
        (temp_dir / "file.txt").write_text("Content")

        results = find_files(temp_dir, "*.md")

        assert results == []

    def test_raises_for_missing_directory(self, temp_dir: Path) -> None:
        """Test that find_files raises FileNotFoundError for missing directory."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            find_files(nonexistent, "*.txt")

    def test_raises_for_non_directory(self, temp_dir: Path) -> None:
        """Test that find_files raises NotADirectoryError for file path."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("Content")

        with pytest.raises(NotADirectoryError, match="Path is not a directory"):
            find_files(file_path, "*.txt")
