"""Python environment management utilities."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class PythonEnvironment:
    """Manages Python virtual environments."""

    def __init__(self, config: dict):
        """Initialize Python environment manager.
        
        Args:
            config: Dictionary containing:
                - manager: "uv" | "system" | "skip"
                - version: Python version string (e.g., "3.11")
                - venv_path: Path to virtual environment (e.g., ".venv")
        """
        self.manager = config.get("manager", "uv")
        self.version = config.get("version", "3.11")
        self.venv_path = Path(config.get("venv_path", ".venv"))

    def setup(self, project_root: Path) -> bool:
        """Create virtual environment based on configured manager.
        
        Args:
            project_root: Path to the project root directory
            
        Returns:
            True if setup succeeded, False otherwise
            
        Raises:
            RuntimeError: If required tools are not available
        """
        if self.manager == "skip":
            return True

        venv_dir = project_root / self.venv_path

        if self.manager == "uv":
            return self._setup_with_uv(venv_dir)
        elif self.manager == "system":
            return self._setup_with_system(venv_dir)

        return False

    def _setup_with_uv(self, venv_dir: Path) -> bool:
        """Create venv using uv.
        
        Args:
            venv_dir: Path where virtual environment should be created
            
        Returns:
            True if creation succeeded, False otherwise
            
        Raises:
            RuntimeError: If uv is not found
        """
        if not shutil.which("uv"):
            raise RuntimeError("uv not found. Install via: brew install uv")

        cmd = ["uv", "venv", str(venv_dir), "--python", self.version]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _setup_with_system(self, venv_dir: Path) -> bool:
        """Create venv using system Python.
        
        Args:
            venv_dir: Path where virtual environment should be created
            
        Returns:
            True if creation succeeded, False otherwise
            
        Raises:
            RuntimeError: If Python is not found
        """
        python = shutil.which("python3") or shutil.which("python")
        if not python:
            raise RuntimeError("Python not found in PATH")

        cmd = [python, "-m", "venv", str(venv_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def install_package(self, package: str, project_root: Path) -> bool:
        """Install a package into the virtual environment.
        
        Args:
            package: Package name to install
            project_root: Path to the project root directory
            
        Returns:
            True if installation succeeded, False otherwise
        """
        venv_dir = project_root / self.venv_path

        if self.manager == "uv":
            cmd = ["uv", "pip", "install", package]
        else:
            pip = venv_dir / "bin" / "pip"
            cmd = [str(pip), "install", package]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        return result.returncode == 0

    @staticmethod
    def detect_existing(project_root: Path) -> Optional[Path]:
        """Detect existing virtual environment.
        
        Args:
            project_root: Path to the project root directory
            
        Returns:
            Path to detected virtual environment, or None if not found
        """
        candidates = [".venv", "venv", ".virtualenv"]
        for name in candidates:
            venv_dir = project_root / name
            if (venv_dir / "bin" / "python").exists():
                return venv_dir
        return None
