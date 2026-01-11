"""Platform detection for AI coding assistants."""

from dataclasses import dataclass
from pathlib import Path


class DetectorError(Exception):
    """Exception raised for platform detection errors."""

    pass


@dataclass
class PlatformConfig:
    """Configuration for an AI platform."""

    name: str  # "claude", "gemini", "copilot"
    display_name: str  # "Claude Code", "Google Gemini", "GitHub Copilot"
    config_dir: str  # ".claude", ".gemini", ".github"
    commands_dir: str  # "commands", "commands", "commands"


# Supported platform configurations
PLATFORMS = {
    "claude": PlatformConfig(
        name="claude",
        display_name="Claude Code",
        config_dir=".claude",
        commands_dir="commands",
    ),
    "gemini": PlatformConfig(
        name="gemini",
        display_name="Google Gemini",
        config_dir=".gemini",
        commands_dir="commands",
    ),
    "copilot": PlatformConfig(
        name="copilot",
        display_name="GitHub Copilot",
        config_dir=".github",
        commands_dir="commands",
    ),
}


class PlatformDetector:
    """Detects available AI coding platforms."""

    def __init__(self, project_root: Path | str):
        """
        Initialize detector.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def detect_platform(self, platform_name: str) -> PlatformConfig | None:
        """
        Check if a specific platform is available.

        Args:
            platform_name: Platform name ("claude", "gemini", "copilot")

        Returns:
            PlatformConfig if platform is available, None otherwise

        Raises:
            DetectorError: If platform_name is not supported
        """
        if platform_name not in PLATFORMS:
            raise DetectorError(
                f"Unknown platform '{platform_name}'. "
                f"Supported platforms: {', '.join(PLATFORMS.keys())}"
            )

        platform = PLATFORMS[platform_name]
        config_dir = self.project_root / platform.config_dir

        if config_dir.exists() and config_dir.is_dir():
            return platform

        return None

    def detect_all_platforms(self) -> list[PlatformConfig]:
        """
        Detect all available platforms.

        Returns:
            List of available platform configurations
        """
        available = []
        for platform_name in PLATFORMS:
            platform = self.detect_platform(platform_name)
            if platform is not None:
                available.append(platform)

        return available

    def get_platform_config(self, platform_name: str) -> PlatformConfig:
        """
        Get configuration for a platform (without checking availability).

        Args:
            platform_name: Platform name

        Returns:
            Platform configuration

        Raises:
            DetectorError: If platform_name is not supported
        """
        if platform_name not in PLATFORMS:
            raise DetectorError(
                f"Unknown platform '{platform_name}'. "
                f"Supported platforms: {', '.join(PLATFORMS.keys())}"
            )

        return PLATFORMS[platform_name]

    @staticmethod
    def list_supported_platforms() -> list[str]:
        """
        List all supported platform names.

        Returns:
            List of platform names
        """
        return list(PLATFORMS.keys())
