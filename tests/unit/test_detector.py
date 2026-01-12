"""Tests for platform detector."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.detector import DetectorError, PlatformDetector


class TestPlatformDetector:
    """Tests for PlatformDetector class."""

    def test_detect_claude_present(self, temp_dir: Path) -> None:
        """Test detecting Claude when .claude directory exists."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        detector = PlatformDetector(temp_dir)
        adapter = detector.detect_platform("claude")

        assert adapter is not None
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.name == "claude"

    def test_detect_claude_absent(self, temp_dir: Path) -> None:
        """Test detecting Claude when .claude directory doesn't exist."""
        detector = PlatformDetector(temp_dir)
        adapter = detector.detect_platform("claude")

        assert adapter is None

    def test_detect_platform_raises_for_unknown(self, temp_dir: Path) -> None:
        """Test that detecting unknown platform raises error."""
        detector = PlatformDetector(temp_dir)

        with pytest.raises(DetectorError, match="Unknown adapter"):
            detector.detect_platform("unknown")

    def test_detect_all_platforms_empty(self, temp_dir: Path) -> None:
        """Test detecting all platforms when none are present."""
        detector = PlatformDetector(temp_dir)
        adapters = detector.detect_all_platforms()

        assert adapters == []

    def test_detect_all_platforms_claude_present(self, temp_dir: Path) -> None:
        """Test detecting all platforms when Claude is present."""
        (temp_dir / ".claude").mkdir()

        detector = PlatformDetector(temp_dir)
        adapters = detector.detect_all_platforms()

        assert len(adapters) == 1
        assert adapters[0].name == "claude"

    def test_get_adapter(self, temp_dir: Path) -> None:
        """Test getting adapter without checking availability."""
        detector = PlatformDetector(temp_dir)
        adapter = detector.get_adapter("claude")

        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.name == "claude"
        assert adapter.display_name == "Claude Code"

    def test_get_adapter_raises_for_unknown(self, temp_dir: Path) -> None:
        """Test that getting unknown adapter raises error."""
        detector = PlatformDetector(temp_dir)

        with pytest.raises(DetectorError, match="Unknown adapter"):
            detector.get_adapter("unknown")

    def test_list_supported_platforms(self) -> None:
        """Test listing all supported platforms."""
        platforms = PlatformDetector.list_supported_platforms()

        assert "claude" in platforms
        assert len(platforms) >= 1  # At least claude

    def test_detect_ignores_files(self, temp_dir: Path) -> None:
        """Test that detector ignores files with platform names."""
        # Create a file instead of directory
        (temp_dir / ".claude").write_text("not a directory")

        detector = PlatformDetector(temp_dir)
        adapter = detector.detect_platform("claude")

        assert adapter is None

    def test_detected_adapter_has_project_root(self, temp_dir: Path) -> None:
        """Test that detected adapter has project_root set."""
        (temp_dir / ".claude").mkdir()

        detector = PlatformDetector(temp_dir)
        adapter = detector.detect_platform("claude")

        assert adapter is not None
        assert adapter.project_root == temp_dir
