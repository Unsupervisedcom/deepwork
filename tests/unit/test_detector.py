"""Tests for platform detector."""

from pathlib import Path

import pytest

from deepwork.core.detector import (
    PLATFORMS,
    DetectorError,
    PlatformDetector,
)


class TestPlatformConfig:
    """Tests for PlatformConfig dataclass."""

    def test_claude_config(self) -> None:
        """Test Claude platform configuration."""
        config = PLATFORMS["claude"]

        assert config.name == "claude"
        assert config.display_name == "Claude Code"
        assert config.config_dir == ".claude"
        assert config.skill_prefix == "skill-"
        assert config.skill_extension == ".md"

    def test_gemini_config(self) -> None:
        """Test Gemini platform configuration."""
        config = PLATFORMS["gemini"]

        assert config.name == "gemini"
        assert config.display_name == "Google Gemini"
        assert config.config_dir == ".gemini"
        assert config.skill_prefix == "skill-"
        assert config.skill_extension == ".md"

    def test_copilot_config(self) -> None:
        """Test Copilot platform configuration."""
        config = PLATFORMS["copilot"]

        assert config.name == "copilot"
        assert config.display_name == "GitHub Copilot"
        assert config.config_dir == ".github"
        assert config.skill_prefix == "copilot-"
        assert config.skill_extension == ".md"


class TestPlatformDetector:
    """Tests for PlatformDetector class."""

    def test_detect_claude_present(self, temp_dir: Path) -> None:
        """Test detecting Claude when .claude directory exists."""
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        detector = PlatformDetector(temp_dir)
        config = detector.detect_platform("claude")

        assert config is not None
        assert config.name == "claude"

    def test_detect_claude_absent(self, temp_dir: Path) -> None:
        """Test detecting Claude when .claude directory doesn't exist."""
        detector = PlatformDetector(temp_dir)
        config = detector.detect_platform("claude")

        assert config is None

    def test_detect_gemini_present(self, temp_dir: Path) -> None:
        """Test detecting Gemini when .gemini directory exists."""
        gemini_dir = temp_dir / ".gemini"
        gemini_dir.mkdir()

        detector = PlatformDetector(temp_dir)
        config = detector.detect_platform("gemini")

        assert config is not None
        assert config.name == "gemini"

    def test_detect_copilot_present(self, temp_dir: Path) -> None:
        """Test detecting Copilot when .github directory exists."""
        github_dir = temp_dir / ".github"
        github_dir.mkdir()

        detector = PlatformDetector(temp_dir)
        config = detector.detect_platform("copilot")

        assert config is not None
        assert config.name == "copilot"

    def test_detect_platform_raises_for_unknown(self, temp_dir: Path) -> None:
        """Test that detecting unknown platform raises error."""
        detector = PlatformDetector(temp_dir)

        with pytest.raises(DetectorError, match="Unknown platform"):
            detector.detect_platform("unknown")

    def test_detect_all_platforms_empty(self, temp_dir: Path) -> None:
        """Test detecting all platforms when none are present."""
        detector = PlatformDetector(temp_dir)
        platforms = detector.detect_all_platforms()

        assert platforms == []

    def test_detect_all_platforms_multiple(self, temp_dir: Path) -> None:
        """Test detecting all platforms when multiple are present."""
        (temp_dir / ".claude").mkdir()
        (temp_dir / ".gemini").mkdir()

        detector = PlatformDetector(temp_dir)
        platforms = detector.detect_all_platforms()

        assert len(platforms) == 2
        names = {p.name for p in platforms}
        assert names == {"claude", "gemini"}

    def test_get_platform_config(self, temp_dir: Path) -> None:
        """Test getting platform config without checking availability."""
        detector = PlatformDetector(temp_dir)
        config = detector.get_platform_config("claude")

        assert config.name == "claude"
        assert config.display_name == "Claude Code"

    def test_get_platform_config_raises_for_unknown(self, temp_dir: Path) -> None:
        """Test that getting unknown platform config raises error."""
        detector = PlatformDetector(temp_dir)

        with pytest.raises(DetectorError, match="Unknown platform"):
            detector.get_platform_config("unknown")

    def test_list_supported_platforms(self) -> None:
        """Test listing all supported platforms."""
        platforms = PlatformDetector.list_supported_platforms()

        assert "claude" in platforms
        assert "gemini" in platforms
        assert "copilot" in platforms
        assert len(platforms) == 3

    def test_detect_ignores_files(self, temp_dir: Path) -> None:
        """Test that detector ignores files with platform names."""
        # Create a file instead of directory
        (temp_dir / ".claude").write_text("not a directory")

        detector = PlatformDetector(temp_dir)
        config = detector.detect_platform("claude")

        assert config is None
