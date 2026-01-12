"""Platform detection for AI coding assistants."""

from pathlib import Path

from deepwork.core.adapters import AdapterError, AgentAdapter


class DetectorError(Exception):
    """Exception raised for platform detection errors."""

    pass


class PlatformDetector:
    """Detects available AI coding platforms using registered adapters."""

    def __init__(self, project_root: Path | str):
        """
        Initialize detector.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)

    def detect_platform(self, platform_name: str) -> AgentAdapter | None:
        """
        Check if a specific platform is available.

        Args:
            platform_name: Platform name ("claude", "gemini", "copilot")

        Returns:
            AgentAdapter instance if platform is available, None otherwise

        Raises:
            DetectorError: If platform_name is not supported
        """
        try:
            adapter_cls = AgentAdapter.get(platform_name)
        except AdapterError as e:
            raise DetectorError(str(e)) from e

        adapter = adapter_cls(self.project_root)
        if adapter.detect():
            return adapter

        return None

    def detect_all_platforms(self) -> list[AgentAdapter]:
        """
        Detect all available platforms.

        Returns:
            List of available adapter instances
        """
        available = []
        for platform_name in AgentAdapter.list_names():
            adapter = self.detect_platform(platform_name)
            if adapter is not None:
                available.append(adapter)

        return available

    def get_adapter(self, platform_name: str) -> AgentAdapter:
        """
        Get an adapter instance for a platform (without checking availability).

        Args:
            platform_name: Platform name

        Returns:
            AgentAdapter instance

        Raises:
            DetectorError: If platform_name is not supported
        """
        try:
            adapter_cls = AgentAdapter.get(platform_name)
        except AdapterError as e:
            raise DetectorError(str(e)) from e

        return adapter_cls(self.project_root)

    @staticmethod
    def list_supported_platforms() -> list[str]:
        """
        List all supported platform names.

        Returns:
            List of platform names
        """
        return AgentAdapter.list_names()
