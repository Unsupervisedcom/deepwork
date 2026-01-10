"""Job registry for tracking installed jobs."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from deepwork.utils.fs import ensure_dir
from deepwork.utils.yaml_utils import YAMLError, load_yaml, save_yaml


class RegistryError(Exception):
    """Exception raised for registry errors."""

    pass


@dataclass
class JobRegistryEntry:
    """Represents an entry in the job registry."""

    name: str
    version: str
    description: str
    job_dir: str  # Relative path to job directory
    installed_at: str  # ISO format timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "job_dir": self.job_dir,
            "installed_at": self.installed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRegistryEntry":
        """Create entry from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            job_dir=data["job_dir"],
            installed_at=data["installed_at"],
        )


class JobRegistry:
    """Manages the job registry."""

    def __init__(self, deepwork_dir: Path | str):
        """
        Initialize registry.

        Args:
            deepwork_dir: Path to .deepwork directory
        """
        self.deepwork_dir = Path(deepwork_dir)
        self.registry_file = self.deepwork_dir / "registry.yml"

    def _load_registry(self) -> dict[str, dict[str, Any]]:
        """
        Load registry from file.

        Returns:
            Dictionary mapping job names to entry data
        """
        if not self.registry_file.exists():
            return {}

        try:
            data = load_yaml(self.registry_file)
            if data is None:
                return {}
            return data.get("jobs", {})
        except YAMLError as e:
            raise RegistryError(f"Failed to load registry: {e}") from e

    def _save_registry(self, registry_data: dict[str, dict[str, Any]]) -> None:
        """
        Save registry to file.

        Args:
            registry_data: Dictionary mapping job names to entry data
        """
        ensure_dir(self.deepwork_dir)

        try:
            save_yaml(self.registry_file, {"jobs": registry_data})
        except YAMLError as e:
            raise RegistryError(f"Failed to save registry: {e}") from e

    def register_job(
        self, name: str, version: str, description: str, job_dir: str
    ) -> JobRegistryEntry:
        """
        Register a job.

        Args:
            name: Job name
            version: Job version
            description: Job description
            job_dir: Relative path to job directory

        Returns:
            Created registry entry

        Raises:
            RegistryError: If job is already registered
        """
        registry = self._load_registry()

        if name in registry:
            raise RegistryError(f"Job '{name}' is already registered")

        entry = JobRegistryEntry(
            name=name,
            version=version,
            description=description,
            job_dir=job_dir,
            installed_at=datetime.utcnow().isoformat(),
        )

        registry[name] = entry.to_dict()
        self._save_registry(registry)

        return entry

    def unregister_job(self, name: str) -> None:
        """
        Unregister a job.

        Args:
            name: Job name to unregister

        Raises:
            RegistryError: If job is not registered
        """
        registry = self._load_registry()

        if name not in registry:
            raise RegistryError(f"Job '{name}' is not registered")

        del registry[name]
        self._save_registry(registry)

    def get_job(self, name: str) -> JobRegistryEntry | None:
        """
        Get registry entry for a job.

        Args:
            name: Job name

        Returns:
            Registry entry if found, None otherwise
        """
        registry = self._load_registry()

        if name not in registry:
            return None

        return JobRegistryEntry.from_dict(registry[name])

    def list_jobs(self) -> list[JobRegistryEntry]:
        """
        List all registered jobs.

        Returns:
            List of registry entries (sorted by name)
        """
        registry = self._load_registry()
        entries = [JobRegistryEntry.from_dict(data) for data in registry.values()]
        return sorted(entries, key=lambda e: e.name)

    def is_registered(self, name: str) -> bool:
        """
        Check if a job is registered.

        Args:
            name: Job name

        Returns:
            True if job is registered, False otherwise
        """
        registry = self._load_registry()
        return name in registry

    def update_job(
        self, name: str, version: str | None = None, description: str | None = None
    ) -> JobRegistryEntry:
        """
        Update a registered job's metadata.

        Args:
            name: Job name
            version: New version (optional)
            description: New description (optional)

        Returns:
            Updated registry entry

        Raises:
            RegistryError: If job is not registered
        """
        registry = self._load_registry()

        if name not in registry:
            raise RegistryError(f"Job '{name}' is not registered")

        entry_data = registry[name]
        if version is not None:
            entry_data["version"] = version
        if description is not None:
            entry_data["description"] = description

        registry[name] = entry_data
        self._save_registry(registry)

        return JobRegistryEntry.from_dict(entry_data)
